"""
State polling worker.
Monitors poker windows for state changes and emits events when hero's turn is detected.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from ..app.config import PollerConfig, TableConfig, Region
from ..capture.screen_capture import ScreenCapture, capture_region, capture_pixel
from ..capture.window_manager import WindowManager, RegisteredWindow
from ..capture.window_registry import WindowRegistry, TableWindow
from ..vision.card_recognition import CardRecognizer, build_hole_cards, build_board_cards
from ..vision.ui_state import UIStateDetector
from ..poker.models import (
    Observation, Stage, Position, HoleCards, BoardCards, HeroTurnEvent
)
from ..poker.positions import get_hero_position, get_active_positions


logger = logging.getLogger(__name__)


@dataclass
class WindowState:
    """Tracked state for a single window."""
    window_id: str
    last_observation: Optional[Observation] = None
    last_turn_state: bool = False
    consecutive_turn_signals: int = 0
    last_update_time: float = 0.0
    new_hand_detected_time: float = 0.0  # Time when new hand was detected
    last_hand_id: Optional[str] = None
    turn_detected_time: float = 0.0  # Time when turn=true was first detected
    cards_recognized: bool = False  # True after cards successfully recognized
    card_votes: list = None  # List of recognized cards for voting (accumulates over polls)
    final_cards: object = None  # Final cards after voting (cached until new hand)
    final_decision: object = None  # Final decision (cached until new hand)
    
    # Settings for voting
    VOTE_SAMPLES_NEEDED: int = 9  # Number of samples before voting


class TurnEventCallback:
    """Typed callback for hero turn events."""
    def __call__(self, event: HeroTurnEvent) -> None:
        pass


class StatePoller:
    """
    Polls poker windows for state changes and detects hero's turn.
    
    Features:
    - Configurable poll frequency
    - Debouncing to avoid false triggers
    - Per-window state tracking
    - Event emission on hero turn detection
    - Support for both WindowManager and WindowRegistry
    """
    
    def __init__(
        self,
        window_manager: Optional[WindowManager] = None,
        window_registry: Optional[WindowRegistry] = None,
        config: Optional[PollerConfig] = None,
        table_config: Optional[TableConfig] = None,
        on_hero_turn: Optional[Callable[[HeroTurnEvent], None]] = None,
        on_observation: Optional[Callable[[Observation], None]] = None,
        on_debug: Optional[Callable[[str, dict], None]] = None
    ):
        """
        Initialize state poller.
        
        Args:
            window_manager: Window manager to get windows from (legacy)
            window_registry: Window registry for multi-table support
            config: Poller configuration
            table_config: Default table configuration for recognition
            on_hero_turn: Callback when hero's turn is detected
            on_observation: Callback for every observation (optional)
            on_debug: Callback for debug info (window_id, debug_dict)
        """
        self.window_manager = window_manager
        self.window_registry = window_registry
        self.config = config or PollerConfig()
        self.table_config = table_config or TableConfig()
        
        self._on_hero_turn = on_hero_turn
        self._on_observation = on_observation
        self._on_debug = on_debug
        
        self._window_states: Dict[str, WindowState] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Per-window UI detectors (to preserve state like last_hand_id)
        self._ui_detectors: Dict[str, UIStateDetector] = {}
        
        # Recognition components
        self._capture = ScreenCapture()
        self._recognizer = CardRecognizer()
        
        # Preflop decision engine (RFI-only mode by default)
        from ..poker.preflop_engine import RangesBasedEngine
        self._preflop_engine = RangesBasedEngine(rfi_only_mode=True)
        
        # Debounce settings
        self._debounce_signals = 1  # Number of consecutive signals needed (instant)
        
        # Manual card overrides: {window_id: "KsQh"}
        self._card_overrides: Dict[str, str] = {}
    
    def _get_or_create_state(self, window_id: str) -> WindowState:
        """Get or create window state."""
        if window_id not in self._window_states:
            self._window_states[window_id] = WindowState(window_id=window_id)
        return self._window_states[window_id]
    
    def set_card_override(self, window_id: str, cards_str: str):
        """
        Set manual card override for a window.
        
        Args:
            window_id: Window ID
            cards_str: Cards string like "KsQh" or "AsKd"
        """
        # Parse cards string into HoleCards
        from ..poker.models import Card
        
        cards_str = cards_str.strip().upper()
        if len(cards_str) < 4:
            logger.warning(f"Invalid cards override: {cards_str}")
            return
        
        # Extract two cards (each is 2 chars: rank + suit)
        try:
            # Handle formats like "KsQh" or "Ks Qh"
            cards_str = cards_str.replace(" ", "")
            card1_str = cards_str[:2].upper()
            card2_str = cards_str[2:4].upper()
            
            # Lowercase suit
            card1_str = card1_str[0] + card1_str[1].lower()
            card2_str = card2_str[0] + card2_str[1].lower()
            
            card1 = Card(rank=card1_str[0], suit=card1_str[1])
            card2 = Card(rank=card2_str[0], suit=card2_str[1])
            
            hole_cards = HoleCards(card1=card1, card2=card2)
            
            # Store override
            with self._lock:
                self._card_overrides[window_id] = hole_cards
            
            logger.info(f"[{window_id}] Card override set: {hole_cards}")
            
            # Also update state's final cards
            state = self._get_or_create_state(window_id)
            state.final_cards = hole_cards
            state.final_decision = None  # Will recalculate
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse cards override '{cards_str}': {e}")
    
    def _poll_window(self, window: RegisteredWindow) -> Optional[Observation]:
        """
        Poll a single window and build observation.
        
        Args:
            window: Registered window to poll (RegisteredWindow or TableWindow)
        
        Returns:
            Observation or None if detection failed
        """
        window_offset = window.info.get_screen_offset()
        window_id = window.window_id
        
        # Get table config - use per-window config if available (TableWindow)
        if hasattr(window, 'config') and window.config:
            table_config = window.config
        else:
            table_config = self.table_config
        
        # Get or create UI state detector for this window (preserves state)
        if window_id not in self._ui_detectors:
            self._ui_detectors[window_id] = UIStateDetector(table_config, self._capture)
        detector = self._ui_detectors[window_id]
        
        # Detect UI state
        ui_state = detector.get_full_state(window_offset)
        
        dealer_result = ui_state["dealer"]
        active_result = ui_state["active_players"]
        turn_result = ui_state["hero_turn"]
        
        # Detect hand ID for new hand detection
        hand_result = detector.detect_hand_id(window_offset)
        
        # Detect hero stack
        stack_result = detector.detect_hero_stack(window_offset)
        hero_stack_bb = stack_result.stack_bb
        
        # Track new hand timing for card recognition delay
        import time
        state = self._get_or_create_state(window_id)
        if hand_result.is_new_hand:
            state.new_hand_detected_time = time.time()
            state.last_hand_id = hand_result.hand_id
        
        # Debug info will be sent after card recognition (below)
        
        # Get dealer seat (required for position calculation)
        if dealer_result.seat_index is None:
            return None  # No dealer = not at table or between hands
        
        dealer_seat = dealer_result.seat_index
        
        # Calculate hero position
        hero_position = get_hero_position(
            table_config.hero_seat_index,
            dealer_seat,
            total_seats=8
        )
        
        # Calculate active player positions
        # Include hero seat in active seats list
        all_active_seats = active_result.active_seats + [table_config.hero_seat_index]
        active_positions = tuple(get_active_positions(
            all_active_seats, dealer_seat, total_seats=8
        ))
        
        # Recognize hero cards using per-window config
        # Logic: recognize until turn=true + 3 seconds, then stop
        current_time = time.time()
        
        # Track when turn was first detected
        if turn_result.is_hero_turn and state.turn_detected_time == 0:
            state.turn_detected_time = current_time
            logger.debug(f"Turn detected at {current_time}")
        
        # Reset on new hand
        if hand_result.is_new_hand:
            state.turn_detected_time = 0.0
            state.cards_recognized = False
            state.new_hand_detected_time = current_time
            state.card_votes = []  # Reset voting
            state.final_cards = None
            state.final_decision = None
            # Clear manual override on new hand
            with self._lock:
                if window_id in self._card_overrides:
                    del self._card_overrides[window_id]
            state.final_decision = None
        
        # Initialize card_votes if None
        if state.card_votes is None:
            state.card_votes = []
        
        # Check for manual card override first
        with self._lock:
            override_cards = self._card_overrides.get(window_id)
        
        # Decide whether to recognize cards
        # Logic: recognize cards until turn=true + 3 seconds, then use final result
        time_since_new_hand = current_time - state.new_hand_detected_time if state.new_hand_detected_time > 0 else 999
        time_since_turn = current_time - state.turn_detected_time if state.turn_detected_time > 0 else 0
        recognition_window_closed = state.turn_detected_time > 0 and time_since_turn > 3.0
        
        if override_cards:
            # Use manual override
            hero_cards = override_cards
            state.final_cards = override_cards
        elif time_since_new_hand < 1.0:
            hero_cards = None  # Wait for cards to be dealt
        elif state.final_cards is not None:
            # Already have final cards from voting - use cached
            hero_cards = state.final_cards
        else:
            # Recognize cards and accumulate votes (single recognition per poll)
            recognized = self._recognize_hero_cards_single(window_offset, table_config)
            if recognized:
                state.card_votes.append(recognized)
                logger.debug(f"Card vote {len(state.card_votes)}/{state.VOTE_SAMPLES_NEEDED}: {recognized}")
            
            # Check if we have enough votes for finalization
            if len(state.card_votes) >= state.VOTE_SAMPLES_NEEDED:
                from collections import Counter
                # Vote on cards (use string representation for hashing)
                votes = [str(c) for c in state.card_votes]
                counter = Counter(votes)
                most_common, count = counter.most_common(1)[0]
                
                # Require majority (at least 5 out of 9)
                if count >= (state.VOTE_SAMPLES_NEEDED // 2 + 1):
                    # Find the actual HoleCards object
                    for c in state.card_votes:
                        if str(c) == most_common:
                            state.final_cards = c
                            break
                    logger.info(f"CARDS FINALIZED by voting ({count}/{len(votes)}): {state.final_cards}")
                else:
                    # No clear winner - keep oldest half, accumulate more
                    logger.debug(f"Voting uncertain: {counter.most_common(3)}, continuing...")
                    state.card_votes = state.card_votes[-(state.VOTE_SAMPLES_NEEDED // 2):]
            
            hero_cards = recognized
        
        # Detect board cards
        board_cards = self._recognize_board_cards(window_offset, table_config)
        stage = board_cards.get_stage()
        
        # Build observation
        observation = Observation(
            timestamp=datetime.now(),
            window_id=window_id,
            stage=stage,
            hero_position=hero_position,
            dealer_seat=dealer_seat,
            active_players_count=len(all_active_seats),
            active_positions=active_positions,
            hero_cards=hero_cards,
            board_cards=board_cards,
            is_hero_turn=turn_result.is_hero_turn,
            hero_stack_bb=hero_stack_bb,
            confidence={
                "dealer": dealer_result.confidence,
                "turn": turn_result.confidence,
            }
        )
        
        # Get preflop decision using observation
        # Only show final decision after cards are finalized by voting
        decision = None
        if state.final_cards and self._preflop_engine and stage == Stage.PREFLOP:
            # Use final cards from voting for decision
            observation_with_final = Observation(
                timestamp=observation.timestamp,
                window_id=observation.window_id,
                stage=observation.stage,
                hero_position=observation.hero_position,
                dealer_seat=observation.dealer_seat,
                active_players_count=observation.active_players_count,
                active_positions=observation.active_positions,
                hero_cards=state.final_cards,
                board_cards=observation.board_cards,
                is_hero_turn=observation.is_hero_turn,
                hero_stack_bb=observation.hero_stack_bb,
                confidence=observation.confidence,
            )
            if state.final_decision is None:
                state.final_decision = self._preflop_engine.get_decision(observation_with_final)
                if state.final_decision:
                    logger.info(f"FINAL DECISION: {state.final_decision.action.value} ({state.final_decision.reasoning})")
            decision = state.final_decision
        
        # Send debug info (always, after decision is known)
        if self._on_debug:
            # Show final cards after voting, or current sample during accumulation
            display_cards = state.final_cards if state.final_cards else hero_cards
            cards_str = str(display_cards) if display_cards else None
            # Use final_decision if available (persists after turn ends)
            display_decision = decision if decision else state.final_decision
            decision_str = display_decision.action.value if display_decision else None
            self._on_debug(window_id, {
                "dealer_seat": dealer_result.seat_index,
                "active_count": active_result.count,
                "active_seats": active_result.active_seats,
                "is_turn": turn_result.is_hero_turn,
                "hero_cards": cards_str,
                "decision": decision_str,
                "hand_id": hand_result.hand_id,
                "is_new_hand": hand_result.is_new_hand,
                "hero_stack_bb": hero_stack_bb,
            })
        
        return observation
    
    def _recognize_hero_cards_single(
        self,
        window_offset: tuple,
        table_config: Optional[TableConfig] = None
    ) -> Optional[HoleCards]:
        """
        Recognize hero's hole cards (single sample for voting accumulation).
        
        Called once per poll cycle. Results are accumulated in WindowState.card_votes
        and finalized through voting after 9 samples.
        
        Args:
            window_offset: Window screen offset
            table_config: Table configuration with card regions
        
        Returns:
            HoleCards or None if recognition failed
        """
        config = table_config or self.table_config
        
        # Capture rank images
        card1_rank_img = capture_region(
            config.hero_card1_number, window_offset
        )
        card2_rank_img = capture_region(
            config.hero_card2_number, window_offset
        )
        
        # Check rank images captured
        if not all([card1_rank_img, card2_rank_img]):
            logger.debug("Capture failed for hero cards")
            return None
        
        # Recognize ranks using OCR
        rank1, _ = self._recognizer.recognize_rank_ocr(card1_rank_img)
        rank2, _ = self._recognizer.recognize_rank_ocr(card2_rank_img)
        
        if not rank1 or not rank2:
            logger.debug(f"OCR failed: rank1={rank1} rank2={rank2}")
            return None
        
        # Recognize suits using color detection (faster and more reliable)
        suit1_pixel = config.hero_card1_suit_pixel
        suit2_pixel = config.hero_card2_suit_pixel
        
        color1 = capture_pixel(suit1_pixel.left, suit1_pixel.top, window_offset)
        color2 = capture_pixel(suit2_pixel.left, suit2_pixel.top, window_offset)
        
        if not color1 or not color2:
            logger.debug("Suit pixel capture failed")
            return None
        
        suit1, _ = self._recognizer.recognize_suit_by_color(color1)
        suit2, _ = self._recognizer.recognize_suit_by_color(color2)
        
        # Build cards
        try:
            from ..poker.models import Card
            card1 = Card(rank=rank1, suit=suit1)
            card2 = Card(rank=rank2, suit=suit2)
            
            if card1 == card2:
                logger.debug(f"Duplicate cards detected: {card1}")
                return None
            
            return HoleCards(card1=card1, card2=card2)
        except Exception as e:
            logger.debug(f"Card creation failed: {e}")
            return None
    
    def _recognize_board_cards(
        self,
        window_offset: tuple,
        table_config: Optional[TableConfig] = None
    ) -> BoardCards:
        """
        Recognize board cards (flop/turn/river).
        
        Args:
            window_offset: Window screen offset
            table_config: Table configuration with board regions
        
        Returns:
            BoardCards (empty if preflop or recognition failed)
        """
        config = table_config or self.table_config
        cards = []
        
        for region_dict in config.board_card_regions:
            if not isinstance(region_dict, dict):
                continue
            
            number_region = region_dict.get('number')
            suit_region = region_dict.get('suit')
            
            if not number_region or not suit_region:
                continue
            
            # Capture images
            rank_img = capture_region(number_region, window_offset)
            suit_img = capture_region(suit_region, window_offset)
            
            if not rank_img or not suit_img:
                # No more cards on board
                break
            
            # Recognize card
            result = self._recognizer.recognize_card(rank_img, suit_img)
            
            if not result.is_valid:
                # Card not recognizable - likely no card there
                break
            
            # Check for duplicates
            if any(str(c) == str(result.card) for c in cards):
                logger.warning(f"Duplicate board card detected: {result.card}")
                continue
            
            cards.append(result.card)
        
        # Validate board card count (must be 0, 3, 4, or 5)
        valid_counts = (0, 3, 4, 5)
        if len(cards) not in valid_counts:
            logger.debug(f"Invalid board card count: {len(cards)}, using empty board")
            return BoardCards.empty()
        
        return BoardCards(cards=tuple(cards))
    
    def _handle_observation(self, observation: Observation, state: WindowState):
        """
        Handle a new observation and check for turn changes.
        
        Args:
            observation: New observation
            state: Window state to update
        """
        # Emit observation callback
        if self._on_observation:
            try:
                self._on_observation(observation)
            except Exception as e:
                logger.error(f"Observation callback error: {e}")
        
        # Check for hero turn with debouncing
        if observation.is_hero_turn:
            state.consecutive_turn_signals += 1
            
            if (state.consecutive_turn_signals >= self._debounce_signals
                    and not state.last_turn_state):
                # Hero turn confirmed - emit event
                event = HeroTurnEvent(
                    timestamp=observation.timestamp,
                    window_id=observation.window_id,
                    observation=observation
                )
                
                if self._on_hero_turn:
                    try:
                        self._on_hero_turn(event)
                    except Exception as e:
                        logger.error(f"Hero turn callback error: {e}")
                
                state.last_turn_state = True
                logger.info(
                    f"[{observation.window_id}] Hero turn detected - "
                    f"Position: {observation.hero_position.value}, "
                    f"Cards: {observation.hero_cards}"
                )
        else:
            state.consecutive_turn_signals = 0
            state.last_turn_state = False
        
        state.last_observation = observation
        state.last_update_time = time.time()
    
    def _poll_loop(self):
        """Main polling loop."""
        interval = 1.0 / self.config.poll_frequency_hz
        
        logger.info(
            f"Starting poll loop at {self.config.poll_frequency_hz} Hz "
            f"(interval: {interval*1000:.0f}ms)"
        )
        
        while self._running:
            start_time = time.time()
            
            try:
                # Get windows to poll - prefer registry over manager
                windows_to_poll = []
                
                if self.window_registry:
                    self.window_registry.refresh_all()
                    windows_to_poll = self.window_registry.get_active_windows()
                elif self.window_manager:
                    self.window_manager.refresh_all()
                    windows_to_poll = self.window_manager.get_active_windows()
                
                # Poll each active window
                for window in windows_to_poll:
                    state = self._get_or_create_state(window.window_id)
                    
                    try:
                        observation = self._poll_window(window)
                        if observation:
                            self._handle_observation(observation, state)
                    except Exception as e:
                        logger.error(f"Error polling {window.window_id}: {e}")
                        # Track error in TableWindow if available
                        if hasattr(window, 'mark_error'):
                            window.mark_error(str(e))
            
            except Exception as e:
                logger.error(f"Poll loop error: {e}")
            
            # Sleep for remaining interval
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def start(self):
        """Start the polling thread."""
        if self._running:
            logger.warning("Poller already running")
            return
        
        # OCR-based recognition - no templates needed
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("State poller started")
    
    def stop(self):
        """Stop the polling thread."""
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        self._capture.close()
        logger.info("State poller stopped")
    
    def is_running(self) -> bool:
        """Check if poller is running."""
        return self._running
    
    def get_last_observation(self, window_id: str) -> Optional[Observation]:
        """Get last observation for a window."""
        state = self._window_states.get(window_id)
        return state.last_observation if state else None
