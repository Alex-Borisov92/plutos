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
        self._fallback = PlaceholderPreflopEngine()
    
    def get_decision(self, observation: Observation) -> Optional[PreflopDecision]:
        """
        Get chart-based decision.
        Falls back to placeholder if charts not loaded.
        """
        # TODO: Implement chart lookup
        # For now, delegate to placeholder
        logger.debug("Charts not implemented, using placeholder")
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


def create_engine(engine_type: str = "placeholder", **kwargs) -> PreflopEngine:
    """
    Factory function to create preflop engine.
    
    Args:
        engine_type: "placeholder" or "chart"
        **kwargs: Additional arguments for engine initialization
    
    Returns:
        PreflopEngine instance
    """
    if engine_type == "chart":
        return ChartBasedPreflopEngine(**kwargs)
    return PlaceholderPreflopEngine()
