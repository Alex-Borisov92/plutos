"""
Tests for position calculation.
"""
import pytest

from src.poker.positions import (
    get_position_from_seat, get_hero_position, get_active_positions,
    is_position_late, is_position_blind, is_position_early
)
from src.poker.models import Position


class TestPositionFromSeat:
    """Tests for seat to position mapping."""
    
    def test_dealer_is_btn(self):
        """Test that dealer seat is BTN."""
        pos = get_position_from_seat(seat_index=0, dealer_seat=0)
        assert pos == Position.BTN
    
    def test_next_to_dealer_is_sb(self):
        """Test that seat after dealer is SB."""
        pos = get_position_from_seat(seat_index=1, dealer_seat=0)
        assert pos == Position.SB
    
    def test_two_after_dealer_is_bb(self):
        """Test that 2 seats after dealer is BB."""
        pos = get_position_from_seat(seat_index=2, dealer_seat=0)
        assert pos == Position.BB
    
    def test_utg_position(self):
        """Test UTG position (3 after dealer)."""
        pos = get_position_from_seat(seat_index=3, dealer_seat=0)
        assert pos == Position.UTG
    
    def test_wrap_around(self):
        """Test position calculation with wrap-around."""
        # Dealer at seat 6, hero at seat 0
        # (0 - 6) % 8 = 2 -> BB
        pos = get_position_from_seat(seat_index=0, dealer_seat=6, total_seats=8)
        assert pos == Position.BB
    
    def test_dealer_at_seat_4(self):
        """Test with dealer at different seat."""
        # Seat 4 is dealer (BTN)
        pos = get_position_from_seat(seat_index=4, dealer_seat=4)
        assert pos == Position.BTN
        
        # Seat 5 is SB
        pos = get_position_from_seat(seat_index=5, dealer_seat=4)
        assert pos == Position.SB
    
    def test_6max_positions(self):
        """Test 6-max table positions."""
        dealer_seat = 0
        
        positions = []
        for seat in range(6):
            pos = get_position_from_seat(seat, dealer_seat, total_seats=6)
            positions.append(pos)
        
        assert positions[0] == Position.BTN
        assert positions[1] == Position.SB
        assert positions[2] == Position.BB
        assert positions[3] == Position.UTG
    
    def test_invalid_total_seats(self):
        """Test invalid seat count returns UNKNOWN."""
        pos = get_position_from_seat(0, 0, total_seats=0)
        assert pos == Position.UNKNOWN
        
        pos = get_position_from_seat(0, 0, total_seats=10)
        assert pos == Position.UNKNOWN


class TestHeroPosition:
    """Tests for hero position calculation."""
    
    def test_hero_is_dealer(self):
        """Test hero at dealer button."""
        pos = get_hero_position(hero_seat=3, dealer_seat=3)
        assert pos == Position.BTN
    
    def test_hero_is_bb(self):
        """Test hero in big blind."""
        pos = get_hero_position(hero_seat=2, dealer_seat=0)
        assert pos == Position.BB
    
    def test_hero_is_utg(self):
        """Test hero in UTG."""
        pos = get_hero_position(hero_seat=3, dealer_seat=0)
        assert pos == Position.UTG


class TestActivePositions:
    """Tests for active positions list."""
    
    def test_single_active_player(self):
        """Test with single active player."""
        active = [0]
        positions = get_active_positions(active, dealer_seat=0)
        assert positions == [Position.BTN]
    
    def test_multiple_active_players(self):
        """Test with multiple active players."""
        active = [0, 1, 2]
        positions = get_active_positions(active, dealer_seat=0)
        assert positions == [Position.BTN, Position.SB, Position.BB]
    
    def test_non_sequential_seats(self):
        """Test with non-sequential active seats."""
        active = [0, 4, 7]
        dealer_seat = 0
        positions = get_active_positions(active, dealer_seat)
        
        assert Position.BTN in positions
        assert Position.UTG1 in positions


class TestPositionCategories:
    """Tests for position category helpers."""
    
    def test_late_positions(self):
        """Test late position detection."""
        assert is_position_late(Position.BTN) is True
        assert is_position_late(Position.CO) is True
        assert is_position_late(Position.UTG) is False
        assert is_position_late(Position.BB) is False
    
    def test_blind_positions(self):
        """Test blind position detection."""
        assert is_position_blind(Position.SB) is True
        assert is_position_blind(Position.BB) is True
        assert is_position_blind(Position.BTN) is False
        assert is_position_blind(Position.UTG) is False
    
    def test_early_positions(self):
        """Test early position detection."""
        assert is_position_early(Position.UTG) is True
        assert is_position_early(Position.UTG1) is True
        assert is_position_early(Position.BTN) is False
        assert is_position_early(Position.BB) is False
