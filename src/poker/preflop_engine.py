"""
Preflop decision engine.
Provides recommended actions based on hole cards, position, and table dynamics.
Currently implements placeholder logic - will be extended with chart-based decisions.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging

from .models import (
    Observation, PreflopDecision, Action, Position, HoleCards, Stage
)


logger = logging.getLogger(__name__)


class PreflopEngine(ABC):
    """Abstract base class for preflop decision engines."""
    
    @abstractmethod
    def get_decision(self, observation: Observation) -> Optional[PreflopDecision]:
        """
        Get preflop decision based on current observation.
        
        Args:
            observation: Current table state
        
        Returns:
            PreflopDecision if decision can be made, None otherwise
        """
        pass


class PlaceholderPreflopEngine(PreflopEngine):
    """
    Simple placeholder preflop engine with basic rules.
    
    Current logic:
    - Pocket pairs TT+ -> RAISE 3BB
    - AK, AQ suited -> RAISE 3BB
    - Everything else -> FOLD
    
    This is intentionally simple and will be replaced with chart-based logic.
    """
    
    # Premium pocket pairs (TT and higher)
    PREMIUM_PAIRS = frozenset(["TT", "JJ", "QQ", "KK", "AA"])
    
    # Premium suited hands
    PREMIUM_SUITED = frozenset(["AKs", "AQs"])
    
    # Premium offsuit hands
    PREMIUM_OFFSUIT = frozenset(["AKo"])
    
    def get_decision(self, observation: Observation) -> Optional[PreflopDecision]:
        """
        Get simple rule-based preflop decision.
        """
        # Validate we're in preflop
        if observation.stage != Stage.PREFLOP:
            logger.debug("Not preflop, skipping decision")
            return None
        
        # Validate we have hole cards
        if observation.hero_cards is None:
            logger.warning("No hero cards detected, cannot make decision")
            return None
        
        hand_notation = observation.hero_cards.hand_notation()
        logger.debug(f"Evaluating hand: {hand_notation}")
        
        # Check for premium hands
        if hand_notation in self.PREMIUM_PAIRS:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=3.0,
                confidence=1.0,
                source="placeholder_premium_pair",
                reasoning=f"Premium pocket pair: {hand_notation}"
            )
        
        if hand_notation in self.PREMIUM_SUITED:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=3.0,
                confidence=1.0,
                source="placeholder_premium_suited",
                reasoning=f"Premium suited hand: {hand_notation}"
            )
        
        if hand_notation in self.PREMIUM_OFFSUIT:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=3.0,
                confidence=1.0,
                source="placeholder_premium_offsuit",
                reasoning=f"Premium offsuit hand: {hand_notation}"
            )
        
        # Default: fold
        return PreflopDecision(
            action=Action.FOLD,
            sizing_bb=None,
            confidence=0.8,
            source="placeholder_default",
            reasoning=f"Non-premium hand: {hand_notation}"
        )


class OpeningRangesEngine(PreflopEngine):
    """
    Opening ranges engine based on legacy ranges.
    
    Logic:
    - If all active players are at or after our position -> this is an open
    - Look up opening range for our position
    - If hand is in range -> RAISE 3BB
    - Otherwise -> FOLD
    """
    
    # Preflop action order (first to act -> last to act)
    ACTION_ORDER = [
        Position.UTG,
        Position.UTG1,
        Position.HJ,
        Position.CO,
        Position.BTN,
        Position.SB,
        Position.BB,
    ]
    
    # Opening ranges per position (from legacy)
    OPENING_RANGES = {
        Position.UTG: frozenset([
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'KQs', 'KJs', 'QJs', 'JTs',
            'AKo', 'AQo', 'AJo', 'ATo', 'KQo', 'QJo', 'JTo',
        ]),
        Position.UTG1: frozenset([
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', 'T9s',
            'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'KQo', 'QJo', 'JTo', 'T9o',
        ]),
        Position.HJ: frozenset([
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', 'T9s', '98s',
            'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
            'KQo', 'QJo', 'JTo',
        ]),
        Position.CO: frozenset([
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
            'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'QJs', 'QTs', 'Q9s', 'Q8s',
            'JTs', 'J9s', 'J8s', 'T9s', 'T8s', '98s', '97s', '87s', '76s', '65s', '54s',
            'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
            'KQo', 'KJo', 'KTo', 'K9o', 'QJo', 'QTo', 'Q9o', 'JTo', 'J9o', 'T9o', '98o', '87o', '76o', '65o', '54o',
        ]),
        Position.BTN: frozenset([
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
            'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'QJs', 'QTs', 'Q9s', 'Q8s',
            'JTs', 'J9s', 'J8s', 'T9s', 'T8s', '98s', '87s', '76s', '65s', '54s',
            'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
            'KQo', 'KJo', 'KTo', 'K9o', 'QJo', 'QTo', 'Q9o', 'JTo', 'J9o', 'T9o', '98o', '87o', '76o', '65o', '54o',
        ]),
        Position.SB: frozenset([
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', 'T9s',
            'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'KQo', 'QJo', 'JTo', 'T9o',
        ]),
        Position.BB: frozenset([
            # BB doesn't open - this is for defense/check
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
            'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'QJs', 'QTs', 'Q9s', 'Q8s',
            'JTs', 'J9s', 'J8s', 'T9s', 'T8s', '98s', '97s', '87s', '76s', '65s', '54s',
            'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
            'KQo', 'KJo', 'KTo', 'K9o', 'QJo', 'QTo', 'Q9o', 'JTo', 'J9o', 'T9o', '98o', '87o', '76o', '65o', '54o',
        ]),
    }
    
    def _get_action_index(self, position: Position) -> int:
        """Get position index in action order (0 = first to act)."""
        try:
            return self.ACTION_ORDER.index(position)
        except ValueError:
            return -1
    
    def _is_open_situation(self, observation: Observation) -> bool:
        """
        Check if this is an open (RFI) situation.
        
        Open = all active players are at or after our position in action order.
        This means no one before us has called/raised.
        """
        if observation.hero_position is None:
            return False
        
        hero_idx = self._get_action_index(observation.hero_position)
        if hero_idx < 0:
            return False
        
        # Check all active positions
        if observation.active_positions:
            for pos in observation.active_positions:
                pos_idx = self._get_action_index(pos)
                # If any active player is before hero in action order
                # and not hero themselves, it's not an open
                if pos_idx >= 0 and pos_idx < hero_idx:
                    logger.debug(f"Not open: {pos.value} acted before {observation.hero_position.value}")
                    return False
        
        return True
    
    def get_decision(self, observation: Observation) -> Optional[PreflopDecision]:
        """Get decision based on opening ranges."""
        # Validate preflop
        if observation.stage != Stage.PREFLOP:
            return None
        
        # Validate hole cards
        if observation.hero_cards is None:
            logger.warning("No hero cards detected")
            return None
        
        # Validate position
        if observation.hero_position is None:
            logger.warning("No hero position detected")
            return None
        
        hand_notation = observation.hero_cards.hand_notation()
        position = observation.hero_position
        
        # Check if this is an open situation
        is_open = self._is_open_situation(observation)
        
        if is_open:
            # Look up opening range for position
            opening_range = self.OPENING_RANGES.get(position, frozenset())
            
            if hand_notation in opening_range:
                return PreflopDecision(
                    action=Action.RAISE,
                    sizing_bb=3.0,
                    confidence=1.0,
                    source="opening_range",
                    reasoning=f"OPEN {position.value}: {hand_notation}"
                )
            else:
                return PreflopDecision(
                    action=Action.FOLD,
                    sizing_bb=None,
                    confidence=0.9,
                    source="opening_range",
                    reasoning=f"Not in {position.value} range: {hand_notation}"
                )
        else:
            # Not an open situation - someone raised/limped before us
            # For now, only play premium hands vs action
            premium = frozenset(['AA', 'KK', 'QQ', 'JJ', 'TT', 'AKs', 'AKo'])
            
            if hand_notation in premium:
                return PreflopDecision(
                    action=Action.RAISE,
                    sizing_bb=3.0,
                    confidence=0.8,
                    source="vs_action_premium",
                    reasoning=f"Premium vs action: {hand_notation}"
                )
            else:
                return PreflopDecision(
                    action=Action.FOLD,
                    sizing_bb=None,
                    confidence=0.7,
                    source="vs_action_default",
                    reasoning=f"Fold vs action: {hand_notation}"
                )


class ChartBasedPreflopEngine(PreflopEngine):
    """
    Chart-based preflop engine.
    
    TODO: Implement chart loading and lookup.
    Will support:
    - RFI (Raise First In) charts per position
    - 3-bet charts
    - Calling ranges
    - Adjustments for player count
    """
    
    def __init__(self, charts_path: Optional[str] = None):
        """
        Initialize with path to charts directory.
        
        Args:
            charts_path: Path to directory containing chart JSON/CSV files
        """
        self.charts_path = charts_path
        self.charts = {}  # Will be loaded from files
        self._fallback = OpeningRangesEngine()
    
    def get_decision(self, observation: Observation) -> Optional[PreflopDecision]:
        """
        Get chart-based decision.
        Falls back to opening ranges if charts not loaded.
        """
        # TODO: Implement chart lookup
        # For now, delegate to opening ranges
        logger.debug("Charts not implemented, using opening ranges")
        return self._fallback.get_decision(observation)
    
    def load_charts(self) -> bool:
        """
        Load charts from configured path.
        
        Returns:
            True if charts loaded successfully
        """
        # TODO: Implement chart loading
        logger.warning("Chart loading not implemented")
        return False


def create_engine(engine_type: str = "opening", **kwargs) -> PreflopEngine:
    """
    Factory function to create preflop engine.
    
    Args:
        engine_type: "placeholder", "opening", or "chart"
        **kwargs: Additional arguments for engine initialization
    
    Returns:
        PreflopEngine instance
    """
    if engine_type == "chart":
        return ChartBasedPreflopEngine(**kwargs)
    if engine_type == "opening":
        return OpeningRangesEngine()
    return PlaceholderPreflopEngine()
