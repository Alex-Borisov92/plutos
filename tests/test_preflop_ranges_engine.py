"""
Tests for RangesBasedEngine preflop decision engine.

Tests cover:
- RFI (open raise) decisions
- Defense vs open (3bet/call/fold)
- Defense vs 3bet (4bet/call/fold)
- ICM push/fold for short stacks
- Position mapping
"""
import pytest
from datetime import datetime

from src.poker.models import (
    Observation, Position, Stage, Card, HoleCards, BoardCards, Action
)
from src.poker.preflop_engine import (
    RangesBasedEngine,
    create_engine,
    position_to_key,
    get_action_index,
    ActionSituation,
)
from src.poker.preflop_ranges import (
    OPEN_RANGES,
    DEFENSE_VS_OPEN,
    DEFENSE_VS_3BET,
    get_stack_bucket,
    is_short_stack,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def engine():
    """Create a RangesBasedEngine instance."""
    return RangesBasedEngine()


def make_observation(
    hero_cards: tuple,
    hero_position: Position,
    active_positions: tuple = (),
    hero_stack_bb: float = 100.0,
) -> Observation:
    """Helper to create test observations."""
    card1 = Card(rank=hero_cards[0][0], suit=hero_cards[0][1])
    card2 = Card(rank=hero_cards[1][0], suit=hero_cards[1][1])
    
    return Observation(
        timestamp=datetime.now(),
        window_id="test",
        stage=Stage.PREFLOP,
        hero_position=hero_position,
        dealer_seat=0,
        active_players_count=len(active_positions) + 1,
        active_positions=active_positions,
        hero_cards=HoleCards(card1=card1, card2=card2),
        board_cards=BoardCards.empty(),
        hero_stack_bb=hero_stack_bb,
        is_hero_turn=True,
    )


# -----------------------------------------------------------------------------
# Position mapping tests
# -----------------------------------------------------------------------------

class TestPositionMapping:
    """Tests for position mapping utilities."""
    
    def test_position_to_key_standard(self):
        """Test standard position mapping."""
        assert position_to_key(Position.BTN) == "BTN"
        assert position_to_key(Position.SB) == "SB"
        assert position_to_key(Position.BB) == "BB"
        assert position_to_key(Position.UTG) == "UTG"
        assert position_to_key(Position.CO) == "CO"
        assert position_to_key(Position.HJ) == "HJ"
    
    def test_position_to_key_new_positions(self):
        """Test new position mappings."""
        assert position_to_key(Position.UTG1) == "UTG+1"
        assert position_to_key(Position.UTG2) == "UTG+2"
        assert position_to_key(Position.LJ) == "LJ"
    
    def test_position_to_key_legacy(self):
        """Test legacy position mappings."""
        assert position_to_key(Position.MP) == "UTG+2"
        assert position_to_key(Position.MP1) == "LJ"
    
    def test_position_to_key_unknown(self):
        """Test unknown position."""
        assert position_to_key(Position.UNKNOWN) is None
    
    def test_action_order(self):
        """Test action order indices."""
        assert get_action_index("UTG") == 0
        assert get_action_index("UTG+1") == 1
        assert get_action_index("BB") == 8
        assert get_action_index("invalid") == -1


# -----------------------------------------------------------------------------
# RFI (Open Raise) tests
# -----------------------------------------------------------------------------

class TestRFIDecisions:
    """Tests for Raise First In decisions."""
    
    def test_utg_open_premium(self, engine):
        """UTG should open with premium hands."""
        obs = make_observation(
            hero_cards=(("A", "s"), ("K", "s")),  # AKs
            hero_position=Position.UTG,
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
        assert "OPEN" in decision.reasoning
    
    def test_utg_fold_weak(self, engine):
        """UTG should fold weak hands."""
        obs = make_observation(
            hero_cards=(("7", "s"), ("2", "h")),  # 72o
            hero_position=Position.UTG,
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.FOLD
    
    def test_btn_open_wide(self, engine):
        """BTN should open wider range."""
        # K7o is in BTN open range but not UTG
        obs = make_observation(
            hero_cards=(("K", "s"), ("7", "h")),  # K7o
            hero_position=Position.BTN,
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
    
    def test_sb_open_very_wide(self, engine):
        """SB should open very wide when folded to."""
        # Q5o is in SB open range
        obs = make_observation(
            hero_cards=(("Q", "s"), ("5", "h")),  # Q5o
            hero_position=Position.SB,
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
    
    def test_all_pairs_open_from_hj(self, engine):
        """All pairs should be opened from HJ."""
        for pair_rank in "23456789TJQKA":
            obs = make_observation(
                hero_cards=((pair_rank, "s"), (pair_rank, "h")),
                hero_position=Position.HJ,
            )
            decision = engine.get_decision(obs)
            
            assert decision is not None
            assert decision.action == Action.RAISE, f"Failed for {pair_rank}{pair_rank}"


# -----------------------------------------------------------------------------
# Defense vs Open tests
# -----------------------------------------------------------------------------

class TestDefenseVsOpen:
    """Tests for facing an open raise."""
    
    def test_co_3bet_vs_utg_with_aq(self, engine):
        """CO should 3bet AQs vs UTG open."""
        obs = make_observation(
            hero_cards=(("A", "s"), ("Q", "s")),  # AQs
            hero_position=Position.CO,
            active_positions=(Position.UTG,),  # UTG opened
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
        assert "3BET" in decision.reasoning
    
    def test_btn_call_vs_co_with_88(self, engine):
        """BTN should call with 88 vs CO open."""
        obs = make_observation(
            hero_cards=(("8", "s"), ("8", "h")),  # 88
            hero_position=Position.BTN,
            active_positions=(Position.CO,),  # CO opened
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.CALL
    
    def test_sb_3bet_bluff_vs_btn(self, engine):
        """SB should 3bet bluff wide vs BTN."""
        # A5s is in 3bet bluff range vs BTN
        obs = make_observation(
            hero_cards=(("A", "s"), ("5", "s")),  # A5s
            hero_position=Position.SB,
            active_positions=(Position.BTN,),
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.RAISE
    
    def test_bb_defend_wide_vs_sb(self, engine):
        """BB should defend wide vs SB open."""
        # K5o is in BB call range vs SB
        obs = make_observation(
            hero_cards=(("K", "s"), ("5", "h")),  # K5o
            hero_position=Position.BB,
            active_positions=(Position.SB,),
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action in (Action.CALL, Action.RAISE)


# -----------------------------------------------------------------------------
# ICM Push/Fold tests
# -----------------------------------------------------------------------------

class TestPushFold:
    """Tests for ICM push/fold decisions."""
    
    def test_short_stack_push_premium(self, engine):
        """Short stack should push premium hands."""
        obs = make_observation(
            hero_cards=(("A", "s"), ("A", "h")),  # AA
            hero_position=Position.UTG,
            hero_stack_bb=5.0,
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.ALL_IN
        assert "PUSH" in decision.reasoning
    
    def test_short_stack_fold_trash(self, engine):
        """Short stack should fold trash hands."""
        obs = make_observation(
            hero_cards=(("3", "s"), ("2", "h")),  # 32o
            hero_position=Position.UTG,
            hero_stack_bb=5.0,
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.FOLD
    
    def test_sb_push_any_two_at_3bb(self, engine):
        """SB should push very wide at 3bb."""
        # Even weak hands should push from SB at 3bb
        obs = make_observation(
            hero_cards=(("J", "s"), ("5", "h")),  # J5o
            hero_position=Position.SB,
            hero_stack_bb=3.0,
        )
        decision = engine.get_decision(obs)
        
        assert decision is not None
        assert decision.action == Action.ALL_IN
    
    def test_stack_bucket_detection(self):
        """Test stack bucket detection."""
        assert get_stack_bucket(3.0) == "1-5bb"
        assert get_stack_bucket(5.0) == "1-5bb"
        assert get_stack_bucket(7.0) == "6-10bb"
        assert get_stack_bucket(10.0) == "6-10bb"
        assert get_stack_bucket(12.0) == "10-15bb"
        assert get_stack_bucket(18.0) == "16-20bb"
        assert get_stack_bucket(50.0) == "deep"
    
    def test_is_short_stack(self):
        """Test short stack detection."""
        assert is_short_stack(5.0) is True
        assert is_short_stack(10.0) is True
        assert is_short_stack(11.0) is False
        assert is_short_stack(100.0) is False


# -----------------------------------------------------------------------------
# Edge cases and validation
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and validation."""
    
    def test_not_preflop_returns_none(self, engine):
        """Engine should return None for non-preflop stages."""
        obs = Observation(
            timestamp=datetime.now(),
            window_id="test",
            stage=Stage.FLOP,  # Not preflop
            hero_position=Position.BTN,
            dealer_seat=0,
            active_players_count=2,
            active_positions=(),
            hero_cards=HoleCards(
                card1=Card(rank="A", suit="s"),
                card2=Card(rank="K", suit="s"),
            ),
            board_cards=BoardCards(cards=(
                Card(rank="Q", suit="h"),
                Card(rank="J", suit="d"),
                Card(rank="T", suit="c"),
            )),
            hero_stack_bb=100.0,
        )
        
        assert engine.get_decision(obs) is None
    
    def test_no_hero_cards_returns_none(self, engine):
        """Engine should return None without hero cards."""
        obs = Observation(
            timestamp=datetime.now(),
            window_id="test",
            stage=Stage.PREFLOP,
            hero_position=Position.BTN,
            dealer_seat=0,
            active_players_count=2,
            active_positions=(),
            hero_cards=None,  # No cards
            board_cards=BoardCards.empty(),
            hero_stack_bb=100.0,
        )
        
        assert engine.get_decision(obs) is None
    
    def test_unknown_position_returns_none(self, engine):
        """Engine should return None for unknown position."""
        obs = make_observation(
            hero_cards=(("A", "s"), ("A", "h")),
            hero_position=Position.UNKNOWN,
        )
        
        assert engine.get_decision(obs) is None
    
    def test_hand_notation_consistency(self):
        """Test that hand notation works correctly."""
        # Suited
        hole = HoleCards(
            card1=Card(rank="A", suit="s"),
            card2=Card(rank="K", suit="s"),
        )
        assert hole.hand_notation() == "AKs"
        
        # Offsuit
        hole = HoleCards(
            card1=Card(rank="A", suit="s"),
            card2=Card(rank="K", suit="h"),
        )
        assert hole.hand_notation() == "AKo"
        
        # Pair
        hole = HoleCards(
            card1=Card(rank="Q", suit="s"),
            card2=Card(rank="Q", suit="h"),
        )
        assert hole.hand_notation() == "QQ"
        
        # Order doesn't matter
        hole = HoleCards(
            card1=Card(rank="K", suit="h"),
            card2=Card(rank="A", suit="s"),
        )
        assert hole.hand_notation() == "AKo"


# -----------------------------------------------------------------------------
# Factory function tests
# -----------------------------------------------------------------------------

class TestFactory:
    """Tests for create_engine factory."""
    
    def test_default_creates_ranges_engine(self):
        """Default should create RangesBasedEngine."""
        engine = create_engine()
        assert isinstance(engine, RangesBasedEngine)
    
    def test_explicit_ranges_type(self):
        """Explicit 'ranges' type should work."""
        engine = create_engine("ranges")
        assert isinstance(engine, RangesBasedEngine)
    
    def test_placeholder_type(self):
        """Placeholder type should create legacy engine."""
        from src.poker.preflop_engine import PlaceholderPreflopEngine
        engine = create_engine("placeholder")
        assert isinstance(engine, PlaceholderPreflopEngine)


# -----------------------------------------------------------------------------
# Range data validation
# -----------------------------------------------------------------------------

class TestRangeDataValidation:
    """Tests to validate range data integrity."""
    
    def test_all_open_positions_have_ranges(self):
        """All expected positions should have open ranges."""
        expected = {"UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB"}
        assert set(OPEN_RANGES.keys()) == expected
    
    def test_open_ranges_not_empty(self):
        """Open ranges should not be empty."""
        for pos, range_set in OPEN_RANGES.items():
            assert len(range_set) > 0, f"Empty range for {pos}"
    
    def test_defense_ranges_structure(self):
        """Defense ranges should have correct structure."""
        for def_pos, openers in DEFENSE_VS_OPEN.items():
            for open_pos, actions in openers.items():
                assert "3bet" in actions, f"Missing 3bet for {def_pos} vs {open_pos}"
                assert "call" in actions, f"Missing call for {def_pos} vs {open_pos}"
    
    def test_hand_notation_format(self):
        """All hands should be in valid notation format."""
        valid_ranks = set("23456789TJQKA")
        
        for pos, range_set in OPEN_RANGES.items():
            for hand in range_set:
                assert 2 <= len(hand) <= 3, f"Invalid hand length: {hand}"
                
                if len(hand) == 2:
                    # Pair: "AA", "KK", etc.
                    assert hand[0] in valid_ranks, f"Invalid rank in {hand}"
                    assert hand[1] in valid_ranks, f"Invalid rank in {hand}"
                else:
                    # Suited/offsuit: "AKs", "AKo"
                    assert hand[0] in valid_ranks, f"Invalid rank in {hand}"
                    assert hand[1] in valid_ranks, f"Invalid rank in {hand}"
                    assert hand[2] in "so", f"Invalid suffix in {hand}"
