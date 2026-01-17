"""
Tests for poker models.
"""
import pytest
from datetime import datetime

from src.poker.models import (
    Card, HoleCards, BoardCards, Stage, Action, Position,
    Observation, PreflopDecision
)


class TestCard:
    """Tests for Card model."""
    
    def test_valid_card_creation(self):
        """Test creating valid cards."""
        card = Card(rank="A", suit="h")
        assert card.rank == "A"
        assert card.suit == "h"
        assert str(card) == "Ah"
    
    def test_all_ranks(self):
        """Test all valid ranks."""
        for rank in "23456789TJQKA":
            card = Card(rank=rank, suit="s")
            assert card.rank == rank
    
    def test_all_suits(self):
        """Test all valid suits."""
        for suit in "shdc":
            card = Card(rank="A", suit=suit)
            assert card.suit == suit
    
    def test_invalid_rank(self):
        """Test invalid rank raises error."""
        with pytest.raises(ValueError, match="Invalid rank"):
            Card(rank="X", suit="h")
    
    def test_invalid_suit(self):
        """Test invalid suit raises error."""
        with pytest.raises(ValueError, match="Invalid suit"):
            Card(rank="A", suit="x")
    
    def test_from_string(self):
        """Test parsing card from string."""
        card = Card.from_string("Ah")
        assert card.rank == "A"
        assert card.suit == "h"
    
    def test_from_string_case_insensitive(self):
        """Test case insensitivity in parsing."""
        card = Card.from_string("ah")
        assert card.rank == "A"
        assert card.suit == "h"
    
    def test_from_string_invalid_length(self):
        """Test invalid string length."""
        with pytest.raises(ValueError, match="2 chars"):
            Card.from_string("A")
    
    def test_to_treys(self):
        """Test treys format conversion."""
        card = Card(rank="K", suit="d")
        assert card.to_treys() == "Kd"
    
    def test_from_ui_format_unicode(self):
        """Test parsing Unicode suit symbols."""
        card = Card.from_ui_format("K♥")
        assert card.rank == "K"
        assert card.suit == "h"
    
    def test_from_ui_format_10(self):
        """Test parsing 10 as T."""
        card = Card.from_ui_format("10♠")
        assert card.rank == "T"
        assert card.suit == "s"
    
    def test_card_equality(self):
        """Test card equality (frozen dataclass)."""
        card1 = Card(rank="A", suit="h")
        card2 = Card(rank="A", suit="h")
        assert card1 == card2
    
    def test_card_inequality(self):
        """Test card inequality."""
        card1 = Card(rank="A", suit="h")
        card2 = Card(rank="A", suit="s")
        assert card1 != card2


class TestHoleCards:
    """Tests for HoleCards model."""
    
    def test_create_hole_cards(self):
        """Test creating hole cards."""
        c1 = Card(rank="A", suit="h")
        c2 = Card(rank="K", suit="h")
        hole = HoleCards(card1=c1, card2=c2)
        assert hole.card1 == c1
        assert hole.card2 == c2
    
    def test_to_list(self):
        """Test conversion to list."""
        hole = HoleCards(
            card1=Card(rank="A", suit="h"),
            card2=Card(rank="K", suit="s")
        )
        assert hole.to_list() == ["Ah", "Ks"]
    
    def test_is_pocket_pair_true(self):
        """Test pocket pair detection - true case."""
        hole = HoleCards(
            card1=Card(rank="Q", suit="h"),
            card2=Card(rank="Q", suit="s")
        )
        assert hole.is_pocket_pair() is True
    
    def test_is_pocket_pair_false(self):
        """Test pocket pair detection - false case."""
        hole = HoleCards(
            card1=Card(rank="A", suit="h"),
            card2=Card(rank="K", suit="s")
        )
        assert hole.is_pocket_pair() is False
    
    def test_is_suited_true(self):
        """Test suited detection - true case."""
        hole = HoleCards(
            card1=Card(rank="A", suit="h"),
            card2=Card(rank="K", suit="h")
        )
        assert hole.is_suited() is True
    
    def test_is_suited_false(self):
        """Test suited detection - false case."""
        hole = HoleCards(
            card1=Card(rank="A", suit="h"),
            card2=Card(rank="K", suit="s")
        )
        assert hole.is_suited() is False
    
    def test_hand_notation_pocket_pair(self):
        """Test hand notation for pocket pairs."""
        hole = HoleCards(
            card1=Card(rank="T", suit="h"),
            card2=Card(rank="T", suit="s")
        )
        assert hole.hand_notation() == "TT"
    
    def test_hand_notation_suited(self):
        """Test hand notation for suited hands."""
        hole = HoleCards(
            card1=Card(rank="A", suit="h"),
            card2=Card(rank="K", suit="h")
        )
        assert hole.hand_notation() == "AKs"
    
    def test_hand_notation_offsuit(self):
        """Test hand notation for offsuit hands."""
        hole = HoleCards(
            card1=Card(rank="A", suit="h"),
            card2=Card(rank="K", suit="s")
        )
        assert hole.hand_notation() == "AKo"
    
    def test_hand_notation_order_independent(self):
        """Test that hand notation is order independent."""
        hole1 = HoleCards(
            card1=Card(rank="K", suit="h"),
            card2=Card(rank="A", suit="s")
        )
        hole2 = HoleCards(
            card1=Card(rank="A", suit="s"),
            card2=Card(rank="K", suit="h")
        )
        assert hole1.hand_notation() == hole2.hand_notation() == "AKo"


class TestBoardCards:
    """Tests for BoardCards model."""
    
    def test_empty_board(self):
        """Test empty board (preflop)."""
        board = BoardCards.empty()
        assert len(board) == 0
        assert board.get_stage() == Stage.PREFLOP
    
    def test_flop(self):
        """Test flop detection."""
        cards = (
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="d"),
        )
        board = BoardCards(cards=cards)
        assert len(board) == 3
        assert board.get_stage() == Stage.FLOP
    
    def test_turn(self):
        """Test turn detection."""
        cards = (
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="d"),
            Card(rank="J", suit="c"),
        )
        board = BoardCards(cards=cards)
        assert len(board) == 4
        assert board.get_stage() == Stage.TURN
    
    def test_river(self):
        """Test river detection."""
        cards = (
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="d"),
            Card(rank="J", suit="c"),
            Card(rank="T", suit="h"),
        )
        board = BoardCards(cards=cards)
        assert len(board) == 5
        assert board.get_stage() == Stage.RIVER
    
    def test_invalid_board_too_many_cards(self):
        """Test that too many cards raises error."""
        cards = tuple(Card(rank=r, suit="h") for r in "23456789")
        with pytest.raises(ValueError, match="max 5 cards"):
            BoardCards(cards=cards)
    
    def test_unknown_stage(self):
        """Test unknown stage for invalid card count."""
        cards = (
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
        )
        board = BoardCards(cards=cards)
        assert board.get_stage() == Stage.UNKNOWN
    
    def test_to_list(self):
        """Test conversion to list."""
        cards = (
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
        )
        board = BoardCards(cards=cards)
        assert board.to_list() == ["Ah", "Ks"]


class TestPreflopDecision:
    """Tests for PreflopDecision model."""
    
    def test_fold_decision(self):
        """Test fold decision string representation."""
        decision = PreflopDecision(action=Action.FOLD)
        assert str(decision) == "FOLD"
    
    def test_raise_decision_with_sizing(self):
        """Test raise decision with sizing."""
        decision = PreflopDecision(action=Action.RAISE, sizing_bb=3.0)
        assert str(decision) == "RAISE 3.0BB"
    
    def test_call_decision(self):
        """Test call decision."""
        decision = PreflopDecision(action=Action.CALL)
        assert str(decision) == "CALL"


class TestCardValidation:
    """Integration tests for card validation."""
    
    def test_duplicate_detection_in_set(self):
        """Test that duplicate cards can be detected using set."""
        cards = [
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="A", suit="h"),  # Duplicate
        ]
        unique = set(str(c) for c in cards)
        assert len(unique) == 2
        assert len(cards) == 3
    
    def test_all_52_cards_valid(self):
        """Test that all 52 cards are valid."""
        count = 0
        for rank in "23456789TJQKA":
            for suit in "shdc":
                card = Card(rank=rank, suit=suit)
                assert card.to_treys() == f"{rank}{suit}"
                count += 1
        assert count == 52
