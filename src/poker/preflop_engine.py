"""
Preflop decision engine.

Provides recommended actions based on hole cards, position, stack depth,
and action history. Uses chart-based ranges from preflop_ranges module.

Supported scenarios:
- RFI (Raise First In) - opening ranges
- Defense vs Open - facing an open raise (3bet/call/fold)
- Defense vs 3bet - we opened, villain 3bet (4bet/call/fold)
- ICM Push/Fold - short stack situations (1-10bb)

Stack depth zones:
- 1-10bb: ICM push/fold mode
- 10-20bb: Placeholder (not yet implemented)
- 20+bb: Standard open/defense ranges
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set, Tuple
import logging

from .models import (
    Observation, PreflopDecision, Action, Position, HoleCards, Stage
)
from .preflop_ranges import (
    OPEN_RANGES,
    DEFENSE_VS_OPEN,
    DEFENSE_VS_3BET,
    DEFENSE_VS_3BET_SB_VS_BB,
    ICM_PUSH_FOLD,
    get_stack_bucket,
    is_short_stack,
)


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Position mapping
# -----------------------------------------------------------------------------

# Map Position enum values to range lookup keys
POSITION_TO_RANGE_KEY: Dict[str, str] = {
    "BTN": "BTN",
    "SB": "SB",
    "BB": "BB",
    "UTG": "UTG",
    "UTG+1": "UTG+1",
    "UTG+2": "UTG+2",
    "LJ": "LJ",
    "HJ": "HJ",
    "CO": "CO",
    # Legacy aliases
    "MP": "UTG+2",      # MP maps to UTG+2 in 9max
    "MP+1": "LJ",       # MP+1 maps to LJ
    "UNKNOWN": None,
}


def position_to_key(position: Position) -> Optional[str]:
    """Convert Position enum to range lookup key."""
    return POSITION_TO_RANGE_KEY.get(position.value)


# Preflop action order (first to act -> last to act)
ACTION_ORDER: List[str] = [
    "UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB", "BB"
]


def get_action_index(pos_key: str) -> int:
    """Get position index in action order (-1 if not found)."""
    try:
        return ACTION_ORDER.index(pos_key)
    except ValueError:
        return -1


# -----------------------------------------------------------------------------
# Action situation detection
# -----------------------------------------------------------------------------

class ActionSituation(Enum):
    """Preflop action situation for Hero."""
    RFI = "rfi"                     # Raise First In - no action before us
    FACING_OPEN = "facing_open"     # Someone opened, we can 3bet/call/fold
    FACING_3BET = "facing_3bet"     # We opened, got 3bet
    FACING_4BET = "facing_4bet"     # We 3bet, got 4bet
    LIMP_POT = "limp_pot"           # Facing limpers
    PUSH_FOLD = "push_fold"         # ICM short stack situation
    UNKNOWN = "unknown"


@dataclass
class ActionContext:
    """Context for making preflop decisions."""
    situation: ActionSituation
    hero_pos: str                   # Hero position key
    villain_pos: Optional[str]      # Opener/3bettor position key
    stack_bb: float
    is_ante: bool = True            # Assume ante for now


# -----------------------------------------------------------------------------
# Abstract base class
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Main ranges-based engine
# -----------------------------------------------------------------------------

class RangesBasedEngine(PreflopEngine):
    """
    Preflop engine using chart-based ranges.
    
    Handles:
    - RFI (open raises)
    - Defense vs open (3bet/call)
    - Defense vs 3bet (4bet/call)
    - ICM push/fold for short stacks
    """
    
    # Default sizing in BB
    DEFAULT_OPEN_SIZE = 2.5
    DEFAULT_3BET_SIZE = 3.0  # Multiplier of open
    DEFAULT_4BET_SIZE = 2.5  # Multiplier of 3bet
    
    def __init__(self, min_stack_for_ranges: float = 10.0):
        """
        Initialize engine.
        
        Args:
            min_stack_for_ranges: Minimum stack (bb) to use open/defense ranges.
                                  Below this, use push/fold.
        """
        self.min_stack_for_ranges = min_stack_for_ranges
    
    def get_decision(self, observation: Observation) -> Optional[PreflopDecision]:
        """Get preflop decision based on ranges."""
        # Validate preflop stage
        if observation.stage != Stage.PREFLOP:
            logger.debug("Not preflop, skipping")
            return None
        
        # Validate hero cards
        if observation.hero_cards is None:
            logger.warning("No hero cards detected")
            return None
        
        # Validate hero position
        if observation.hero_position is None:
            logger.warning("No hero position detected")
            return None
        
        hero_key = position_to_key(observation.hero_position)
        if hero_key is None:
            logger.warning(f"Unknown position: {observation.hero_position}")
            return None
        
        hand = observation.hero_cards.hand_notation()
        stack_bb = observation.hero_stack_bb or 100.0  # Default to deep stack
        
        # Determine action context
        context = self._analyze_context(observation, hero_key, stack_bb)
        
        logger.debug(
            f"Hand: {hand}, Position: {hero_key}, "
            f"Stack: {stack_bb}bb, Situation: {context.situation.value}"
        )
        
        # Route to appropriate handler
        if context.situation == ActionSituation.PUSH_FOLD:
            return self._handle_push_fold(hand, context)
        elif context.situation == ActionSituation.RFI:
            return self._handle_rfi(hand, context)
        elif context.situation == ActionSituation.FACING_OPEN:
            return self._handle_facing_open(hand, context)
        elif context.situation == ActionSituation.FACING_3BET:
            return self._handle_facing_3bet(hand, context)
        else:
            logger.debug(f"Unhandled situation: {context.situation}")
            return self._default_fold(hand, context)
    
    def _analyze_context(
        self,
        observation: Observation,
        hero_key: str,
        stack_bb: float
    ) -> ActionContext:
        """Analyze the action context from observation."""
        # Check for short stack push/fold
        if is_short_stack(stack_bb):
            return ActionContext(
                situation=ActionSituation.PUSH_FOLD,
                hero_pos=hero_key,
                villain_pos=None,
                stack_bb=stack_bb,
            )
        
        # Determine if this is RFI or facing action
        # For now, use simple heuristic based on active positions
        is_rfi = self._is_rfi_situation(observation, hero_key)
        
        if is_rfi:
            return ActionContext(
                situation=ActionSituation.RFI,
                hero_pos=hero_key,
                villain_pos=None,
                stack_bb=stack_bb,
            )
        
        # Facing action - determine opener position
        opener_pos = self._find_opener_position(observation, hero_key)
        
        if opener_pos:
            # Check if we are the opener (facing 3bet)
            # This would require tracking our previous action
            # For now, assume we're facing an open
            return ActionContext(
                situation=ActionSituation.FACING_OPEN,
                hero_pos=hero_key,
                villain_pos=opener_pos,
                stack_bb=stack_bb,
            )
        
        return ActionContext(
            situation=ActionSituation.UNKNOWN,
            hero_pos=hero_key,
            villain_pos=None,
            stack_bb=stack_bb,
        )
    
    def _is_rfi_situation(self, observation: Observation, hero_key: str) -> bool:
        """
        Check if this is a Raise First In situation.
        
        RFI = all players before hero have folded.
        """
        hero_idx = get_action_index(hero_key)
        if hero_idx < 0:
            return False
        
        # Check active positions - if any active player is before hero, not RFI
        if observation.active_positions:
            for pos in observation.active_positions:
                pos_key = position_to_key(pos)
                if pos_key is None:
                    continue
                pos_idx = get_action_index(pos_key)
                if pos_idx >= 0 and pos_idx < hero_idx:
                    return False
        
        return True
    
    def _find_opener_position(
        self,
        observation: Observation,
        hero_key: str
    ) -> Optional[str]:
        """Find the position of the opener (first raiser)."""
        hero_idx = get_action_index(hero_key)
        
        # Look for earliest active position before hero
        earliest_pos = None
        earliest_idx = float('inf')
        
        if observation.active_positions:
            for pos in observation.active_positions:
                pos_key = position_to_key(pos)
                if pos_key is None:
                    continue
                pos_idx = get_action_index(pos_key)
                if 0 <= pos_idx < hero_idx and pos_idx < earliest_idx:
                    earliest_idx = pos_idx
                    earliest_pos = pos_key
        
        return earliest_pos
    
    # -------------------------------------------------------------------------
    # Decision handlers
    # -------------------------------------------------------------------------
    
    def _handle_rfi(self, hand: str, context: ActionContext) -> PreflopDecision:
        """Handle Raise First In decision."""
        open_range = OPEN_RANGES.get(context.hero_pos, frozenset())
        
        if hand in open_range:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=self.DEFAULT_OPEN_SIZE,
                confidence=1.0,
                source="ranges_rfi",
                reasoning=f"OPEN {context.hero_pos}: {hand}",
            )
        else:
            return PreflopDecision(
                action=Action.FOLD,
                sizing_bb=None,
                confidence=0.95,
                source="ranges_rfi",
                reasoning=f"Fold - not in {context.hero_pos} open range: {hand}",
            )
    
    def _handle_facing_open(self, hand: str, context: ActionContext) -> PreflopDecision:
        """Handle facing an open raise."""
        if context.villain_pos is None:
            return self._default_fold(hand, context)
        
        # Get defense ranges
        defense = DEFENSE_VS_OPEN.get(context.hero_pos, {}).get(context.villain_pos)
        if defense is None:
            logger.debug(
                f"No defense range for {context.hero_pos} vs {context.villain_pos}"
            )
            return self._default_fold(hand, context)
        
        # Check ranges in priority order
        threebet_value = defense.get("3bet", frozenset())
        threebet_bluff = defense.get("3bet_bluff", frozenset())
        call_range = defense.get("call", frozenset())
        
        if hand in threebet_value:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=self.DEFAULT_OPEN_SIZE * self.DEFAULT_3BET_SIZE,
                confidence=1.0,
                source="ranges_vs_open",
                reasoning=f"3BET value vs {context.villain_pos}: {hand}",
            )
        
        if hand in threebet_bluff:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=self.DEFAULT_OPEN_SIZE * self.DEFAULT_3BET_SIZE,
                confidence=0.85,
                source="ranges_vs_open",
                reasoning=f"3BET bluff vs {context.villain_pos}: {hand}",
            )
        
        if hand in call_range:
            return PreflopDecision(
                action=Action.CALL,
                sizing_bb=None,
                confidence=0.95,
                source="ranges_vs_open",
                reasoning=f"CALL vs {context.villain_pos}: {hand}",
            )
        
        return PreflopDecision(
            action=Action.FOLD,
            sizing_bb=None,
            confidence=0.9,
            source="ranges_vs_open",
            reasoning=f"Fold vs {context.villain_pos} open: {hand}",
        )
    
    def _handle_facing_3bet(self, hand: str, context: ActionContext) -> PreflopDecision:
        """Handle facing a 3bet after we opened."""
        if context.villain_pos is None:
            return self._default_fold(hand, context)
        
        # Special case: SB vs BB reg battle
        if context.hero_pos == "SB" and context.villain_pos == "BB":
            defense = DEFENSE_VS_3BET_SB_VS_BB
        else:
            defense = DEFENSE_VS_3BET.get(context.hero_pos, {}).get(context.villain_pos)
        
        if defense is None:
            logger.debug(
                f"No 3bet defense range for {context.hero_pos} vs {context.villain_pos}"
            )
            return self._default_fold(hand, context)
        
        fourbet_value = defense.get("4bet", frozenset())
        fourbet_bluff = defense.get("4bet_bluff", frozenset())
        call_range = defense.get("call", frozenset())
        fold_range = defense.get("fold", frozenset())
        
        if hand in fourbet_value:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=self.DEFAULT_OPEN_SIZE * self.DEFAULT_3BET_SIZE * self.DEFAULT_4BET_SIZE,
                confidence=1.0,
                source="ranges_vs_3bet",
                reasoning=f"4BET value vs {context.villain_pos}: {hand}",
            )
        
        if hand in fourbet_bluff:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=self.DEFAULT_OPEN_SIZE * self.DEFAULT_3BET_SIZE * self.DEFAULT_4BET_SIZE,
                confidence=0.8,
                source="ranges_vs_3bet",
                reasoning=f"4BET bluff vs {context.villain_pos}: {hand}",
            )
        
        if hand in call_range:
            return PreflopDecision(
                action=Action.CALL,
                sizing_bb=None,
                confidence=0.9,
                source="ranges_vs_3bet",
                reasoning=f"CALL 3bet from {context.villain_pos}: {hand}",
            )
        
        return PreflopDecision(
            action=Action.FOLD,
            sizing_bb=None,
            confidence=0.9,
            source="ranges_vs_3bet",
            reasoning=f"Fold to 3bet from {context.villain_pos}: {hand}",
        )
    
    def _handle_push_fold(self, hand: str, context: ActionContext) -> PreflopDecision:
        """Handle ICM push/fold decision."""
        stack_bucket = get_stack_bucket(context.stack_bb)
        
        # Get push ranges for this stack depth and position
        bucket_ranges = ICM_PUSH_FOLD.get(stack_bucket, {})
        position_ranges = bucket_ranges.get(context.hero_pos, {})
        
        if not position_ranges:
            logger.debug(
                f"No push/fold range for {context.hero_pos} at {stack_bucket}"
            )
            # Fall back to tight premium range
            return self._push_fold_fallback(hand, context)
        
        # Check push ranges based on exact stack
        # Note: "push" contains full range, "push_Xbb" are subsets for specific depths
        push_range: FrozenSet[str] = frozenset()
        
        if stack_bucket == "1-5bb":
            # For 1-5bb zone, use the full "push" range
            # (push_5bb and push_lt5bb are narrower subsets, push is the union)
            push_range = position_ranges.get("push", frozenset())
        elif stack_bucket == "6-10bb":
            if context.stack_bb >= 10:
                push_range = (
                    position_ranges.get("push_10bb") or
                    position_ranges.get("push", frozenset())
                )
            else:
                push_range = (
                    position_ranges.get("push_6_9bb") or
                    position_ranges.get("push", frozenset())
                )
        else:
            push_range = position_ranges.get("push", frozenset())
        
        if hand in push_range:
            return PreflopDecision(
                action=Action.ALL_IN,
                sizing_bb=context.stack_bb,
                confidence=1.0,
                source="icm_push_fold",
                reasoning=f"PUSH {context.hero_pos} at {context.stack_bb:.1f}bb: {hand}",
            )
        
        return PreflopDecision(
            action=Action.FOLD,
            sizing_bb=None,
            confidence=0.95,
            source="icm_push_fold",
            reasoning=f"Fold {context.hero_pos} at {context.stack_bb:.1f}bb: {hand}",
        )
    
    def _push_fold_fallback(self, hand: str, context: ActionContext) -> PreflopDecision:
        """Fallback push/fold for positions without ranges."""
        # Very tight premium range
        premium = frozenset({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs"})
        
        if hand in premium:
            return PreflopDecision(
                action=Action.ALL_IN,
                sizing_bb=context.stack_bb,
                confidence=0.9,
                source="icm_push_fold_fallback",
                reasoning=f"PUSH premium at {context.stack_bb:.1f}bb: {hand}",
            )
        
        return PreflopDecision(
            action=Action.FOLD,
            sizing_bb=None,
            confidence=0.8,
            source="icm_push_fold_fallback",
            reasoning=f"Fold non-premium at {context.stack_bb:.1f}bb: {hand}",
        )
    
    def _default_fold(self, hand: str, context: ActionContext) -> PreflopDecision:
        """Default fold decision."""
        return PreflopDecision(
            action=Action.FOLD,
            sizing_bb=None,
            confidence=0.5,
            source="default",
            reasoning=f"Default fold: {hand}",
        )


# -----------------------------------------------------------------------------
# Legacy engines (kept for backwards compatibility)
# -----------------------------------------------------------------------------

class PlaceholderPreflopEngine(PreflopEngine):
    """
    Simple placeholder preflop engine with basic rules.
    DEPRECATED: Use RangesBasedEngine instead.
    """
    
    PREMIUM_PAIRS = frozenset(["TT", "JJ", "QQ", "KK", "AA"])
    PREMIUM_SUITED = frozenset(["AKs", "AQs"])
    PREMIUM_OFFSUIT = frozenset(["AKo"])
    
    def get_decision(self, observation: Observation) -> Optional[PreflopDecision]:
        if observation.stage != Stage.PREFLOP:
            return None
        if observation.hero_cards is None:
            return None
        
        hand = observation.hero_cards.hand_notation()
        
        if hand in self.PREMIUM_PAIRS:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=3.0,
                confidence=1.0,
                source="placeholder_premium_pair",
                reasoning=f"Premium pair: {hand}",
            )
        
        if hand in self.PREMIUM_SUITED or hand in self.PREMIUM_OFFSUIT:
            return PreflopDecision(
                action=Action.RAISE,
                sizing_bb=3.0,
                confidence=1.0,
                source="placeholder_premium",
                reasoning=f"Premium hand: {hand}",
            )
        
        return PreflopDecision(
            action=Action.FOLD,
            sizing_bb=None,
            confidence=0.8,
            source="placeholder_default",
            reasoning=f"Non-premium: {hand}",
        )


# -----------------------------------------------------------------------------
# Factory function
# -----------------------------------------------------------------------------

def create_engine(engine_type: str = "ranges", **kwargs) -> PreflopEngine:
    """
    Factory function to create preflop engine.
    
    Args:
        engine_type: "ranges" (default), "placeholder"
        **kwargs: Additional arguments for engine
    
    Returns:
        PreflopEngine instance
    """
    if engine_type == "placeholder":
        return PlaceholderPreflopEngine()
    
    # Default to ranges-based engine
    return RangesBasedEngine(**kwargs)
