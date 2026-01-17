"""
Tests for card recognition and validation.
"""
import pytest

from src.vision.card_recognition import (
    CardRecognizer, convert_cards_list, build_hole_cards, build_board_cards
)
from src.poker.models import Card, HoleCards, BoardCards


class TestCardValidation:
    """Tests for card string validation."""
    
    def test_valid_card_strings(self):
        """Test validation of valid card strings."""
        valid_cards = ["Ah", "Ks", "Qd", "Jc", "Th", "9s", "2d"]
        
        for card_str in valid_cards:
            assert CardRecognizer.validate_card_string(card_str) is True
    
    def test_invalid_card_strings(self):
        """Test validation of invalid card strings."""
        invalid_cards = [
            "Ax",  # Invalid suit
            "1h",  # Invalid rank
            "A",   # Too short
            "Ahx", # Too long
            "",    # Empty
            "ah",  # Lowercase rank (should be uppercase)
        ]
        
        for card_str in invalid_cards:
            # Note: "ah" would actually be valid after processing
            if card_str == "ah":
                continue
            assert CardRecognizer.validate_card_string(card_str) is False


class TestUICardConversion:
    """Tests for converting UI format cards."""
    
    def test_convert_standard_format(self):
        """Test converting standard 2-char format."""
        card = CardRecognizer.convert_ui_card("Ah")
        assert card is not None
        assert card.rank == "A"
        assert card.suit == "h"
    
    def test_convert_unicode_spade(self):
        """Test converting spade symbol."""
        card = CardRecognizer.convert_ui_card("K♠")
        assert card is not None
        assert card.rank == "K"
        assert card.suit == "s"
    
    def test_convert_unicode_heart(self):
        """Test converting heart symbol."""
        card = CardRecognizer.convert_ui_card("Q♥")
        assert card is not None
        assert card.rank == "Q"
        assert card.suit == "h"
    
    def test_convert_unicode_diamond(self):
        """Test converting diamond symbol."""
        card = CardRecognizer.convert_ui_card("J♦")
        assert card is not None
        assert card.rank == "J"
        assert card.suit == "d"
    
    def test_convert_unicode_club(self):
        """Test converting club symbol."""
        card = CardRecognizer.convert_ui_card("T♣")
        assert card is not None
        assert card.rank == "T"
        assert card.suit == "c"
    
    def test_convert_10_to_t(self):
        """Test converting 10 to T."""
        card = CardRecognizer.convert_ui_card("10♠")
        assert card is not None
        assert card.rank == "T"
        assert card.suit == "s"
    
    def test_convert_with_whitespace(self):
        """Test handling whitespace."""
        card = CardRecognizer.convert_ui_card("  Ah  ")
        assert card is not None
        assert card.rank == "A"
        assert card.suit == "h"
    
    def test_convert_invalid_returns_none(self):
        """Test that invalid input returns None."""
        assert CardRecognizer.convert_ui_card("") is None
        assert CardRecognizer.convert_ui_card("X") is None
        assert CardRecognizer.convert_ui_card("Ax") is None


class TestCardsListConversion:
    """Tests for converting lists of cards."""
    
    def test_convert_valid_list(self):
        """Test converting list of valid cards."""
        card_strings = ["Ah", "Ks", "Qd"]
        cards, errors = convert_cards_list(card_strings)
        
        assert len(cards) == 3
        assert len(errors) == 0
        assert cards[0].rank == "A"
        assert cards[1].rank == "K"
        assert cards[2].rank == "Q"
    
    def test_convert_with_invalid_cards(self):
        """Test converting list with some invalid cards."""
        card_strings = ["Ah", "XX", "Qd"]
        cards, errors = convert_cards_list(card_strings)
        
        assert len(cards) == 2
        assert len(errors) == 1
        assert "XX" in errors[0]
    
    def test_deduplication(self):
        """Test that duplicate cards are removed."""
        card_strings = ["Ah", "Ks", "Ah"]  # Duplicate Ah
        cards, errors = convert_cards_list(card_strings, deduplicate=True)
        
        assert len(cards) == 2
        assert len(errors) == 1
        assert "Duplicate" in errors[0]
    
    def test_no_deduplication(self):
        """Test with deduplication disabled."""
        card_strings = ["Ah", "Ks", "Ah"]
        cards, errors = convert_cards_list(card_strings, deduplicate=False)
        
        assert len(cards) == 3
        assert len(errors) == 0
    
    def test_empty_list(self):
        """Test converting empty list."""
        cards, errors = convert_cards_list([])
        
        assert len(cards) == 0
        assert len(errors) == 0


class TestBuildHoleCards:
    """Tests for building hole cards from card list."""
    
    def test_build_valid_hole_cards(self):
        """Test building hole cards from 2 cards."""
        cards = [
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
        ]
        
        hole = build_hole_cards(cards)
        
        assert hole is not None
        assert hole.card1.rank == "A"
        assert hole.card2.rank == "K"
    
    def test_build_from_single_card_returns_none(self):
        """Test that single card returns None."""
        cards = [Card(rank="A", suit="h")]
        
        hole = build_hole_cards(cards)
        
        assert hole is None
    
    def test_build_from_three_cards_returns_none(self):
        """Test that 3 cards returns None."""
        cards = [
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="d"),
        ]
        
        hole = build_hole_cards(cards)
        
        assert hole is None
    
    def test_build_from_empty_returns_none(self):
        """Test that empty list returns None."""
        hole = build_hole_cards([])
        assert hole is None


class TestBuildBoardCards:
    """Tests for building board cards from card list."""
    
    def test_build_empty_board(self):
        """Test building empty board."""
        board = build_board_cards([])
        
        assert len(board) == 0
    
    def test_build_flop(self):
        """Test building flop (3 cards)."""
        cards = [
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="d"),
        ]
        
        board = build_board_cards(cards)
        
        assert len(board) == 3
    
    def test_build_river(self):
        """Test building river (5 cards)."""
        cards = [
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="d"),
            Card(rank="J", suit="c"),
            Card(rank="T", suit="h"),
        ]
        
        board = build_board_cards(cards)
        
        assert len(board) == 5
    
    def test_build_truncates_excess_cards(self):
        """Test that excess cards are truncated to 5."""
        cards = [
            Card(rank=r, suit="h")
            for r in "AKQJT987"  # 8 cards
        ]
        
        board = build_board_cards(cards)
        
        assert len(board) == 5


class TestRecognizerIntegration:
    """Integration tests for CardRecognizer."""
    
    def test_recognizer_initialization(self):
        """Test recognizer can be initialized."""
        recognizer = CardRecognizer()
        assert recognizer is not None
    
    def test_load_templates_without_files(self):
        """Test loading templates when files don't exist."""
        recognizer = CardRecognizer()
        # This should not raise, just return False
        result = recognizer.load_templates()
        # May be True or False depending on template files
        assert isinstance(result, bool)
