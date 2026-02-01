"""
Tests for preflop decision engine.
"""
import pytest
from datetime import datetime

from src.poker.preflop_engine import PlaceholderPreflopEngine, create_engine
from src.poker.models import (
    Observation, Card, HoleCards, BoardCards, Stage, Position, Action
)


def make_observation(hole_cards: HoleCards, stage: Stage = Stage.PREFLOP) -> Observation:
    """Helper to create test observations."""
    return Observation(
        timestamp=datetime.now(),
        window_id="test_window",
        stage=stage,
        hero_position=Position.BTN,
        dealer_seat=0,
        active_players_count=4,
        active_positions=tuple(),
        hero_cards=hole_cards,
        board_cards=BoardCards.empty(),
    )


def make_hole_cards(rank1: str, suit1: str, rank2: str, suit2: str) -> HoleCards:
    """Helper to create hole cards."""
    return HoleCards(
        card1=Card(rank=rank1, suit=suit1),
        card2=Card(rank=rank2, suit=suit2)
    )


class TestPlaceholderEngine:
    """Tests for placeholder preflop engine."""
    
    def test_pocket_aces_raises(self):
        """Test that pocket aces recommend raise."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("A", "h", "A", "s")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
        assert decision.sizing_bb == 3.0
    
    def test_pocket_kings_raises(self):
        """Test that pocket kings recommend raise."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("K", "h", "K", "s")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
    
    def test_pocket_tens_raises(self):
        """Test that pocket tens (TT) recommend raise."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("T", "h", "T", "s")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
        assert "TT" in decision.reasoning or "premium" in decision.reasoning.lower()
    
    def test_pocket_nines_folds(self):
        """Test that pocket nines (99) recommend fold (below threshold)."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("9", "h", "9", "s")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.FOLD
    
    def test_ak_suited_raises(self):
        """Test that AKs recommends raise."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("A", "h", "K", "h")  # Suited
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
    
    def test_aq_suited_raises(self):
        """Test that AQs recommends raise."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("A", "d", "Q", "d")  # Suited
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
    
    def test_ak_offsuit_raises(self):
        """Test that AKo recommends raise."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("A", "h", "K", "s")  # Offsuit
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
    
    def test_72_offsuit_folds(self):
        """Test that 72o recommends fold."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("7", "h", "2", "s")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.FOLD
    
    def test_jt_suited_folds(self):
        """Test that JTs recommends fold (not in premium range)."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("J", "h", "T", "h")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.FOLD
    
    def test_no_decision_without_hole_cards(self):
        """Test that missing hole cards returns None."""
        engine = PlaceholderPreflopEngine()
        obs = Observation(
            timestamp=datetime.now(),
            window_id="test",
            stage=Stage.PREFLOP,
            hero_position=Position.BTN,
            dealer_seat=0,
            active_players_count=4,
            active_positions=tuple(),
            hero_cards=None,  # No hole cards
            board_cards=BoardCards.empty(),
        )
        
        decision = engine.get_decision(obs)
        
        assert decision is None
    
    def test_no_decision_on_flop(self):
        """Test that flop stage returns None."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("A", "h", "A", "s")
        
        board = BoardCards(cards=(
            Card(rank="K", suit="h"),
            Card(rank="Q", suit="s"),
            Card(rank="J", suit="d"),
        ))
        
        obs = Observation(
            timestamp=datetime.now(),
            window_id="test",
            stage=Stage.FLOP,
            hero_position=Position.BTN,
            dealer_seat=0,
            active_players_count=4,
            active_positions=tuple(),
            hero_cards=hole,
            board_cards=board,
        )
        
        decision = engine.get_decision(obs)
        
        assert decision is None
    
    def test_decision_has_source(self):
        """Test that decisions include source information."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("A", "h", "A", "s")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert "placeholder" in decision.source
    
    def test_decision_has_reasoning(self):
        """Test that decisions include reasoning."""
        engine = PlaceholderPreflopEngine()
        hole = make_hole_cards("A", "h", "A", "s")
        obs = make_observation(hole)
        
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert len(decision.reasoning) > 0


class TestEngineFactory:
    """Tests for engine factory function."""
    
    def test_create_placeholder_engine(self):
        """Test creating placeholder engine."""
        engine = create_engine("placeholder")
        assert isinstance(engine, PlaceholderPreflopEngine)
    
    def test_create_default_engine(self):
        """Test default engine type - now uses RangesBasedEngine."""
        from src.poker.preflop_engine import RangesBasedEngine
        engine = create_engine()
        assert isinstance(engine, RangesBasedEngine)
    
    def test_create_chart_engine(self):
        """Test creating chart engine (falls back to placeholder)."""
        engine = create_engine("chart")
        # ChartBasedPreflopEngine internally uses placeholder
        assert engine is not None
