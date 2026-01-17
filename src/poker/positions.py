"""
Position and seat mapping logic.
Handles conversion between seat indices and position names based on dealer location.
"""
from typing import List, Optional
from .models import Position


# Standard 8-max position order starting from BTN
POSITIONS_8MAX = [
    Position.BTN,
    Position.SB,
    Position.BB,
    Position.UTG,
    Position.UTG1,
    Position.MP,
    Position.HJ,
    Position.CO,
]

# Position order for fewer players
POSITIONS_6MAX = [
    Position.BTN,
    Position.SB,
    Position.BB,
    Position.UTG,
    Position.HJ,
    Position.CO,
]

POSITIONS_4MAX = [
    Position.BTN,
    Position.SB,
    Position.BB,
    Position.CO,
]


def get_position_from_seat(
    seat_index: int,
    dealer_seat: int,
    total_seats: int = 8
) -> Position:
    """
    Determine position name for a given seat based on dealer location.
    
    Args:
        seat_index: The seat to get position for (0-based)
        dealer_seat: The seat where dealer button is (0-based)
        total_seats: Total number of seats at the table
    
    Returns:
        Position enum value
    """
    if total_seats <= 0 or total_seats > 9:
        return Position.UNKNOWN
    
    # Calculate relative position from dealer
    relative_pos = (seat_index - dealer_seat) % total_seats
    
    # Select appropriate position list based on table size
    if total_seats <= 4:
        positions = POSITIONS_4MAX
    elif total_seats <= 6:
        positions = POSITIONS_6MAX
    else:
        positions = POSITIONS_8MAX
    
    # Map relative position to actual position
    if relative_pos < len(positions):
        return positions[relative_pos]
    
    return Position.UNKNOWN


def get_hero_position(
    hero_seat: int,
    dealer_seat: int,
    total_seats: int = 8
) -> Position:
    """
    Get hero's position based on their seat and dealer location.
    
    Args:
        hero_seat: Hero's seat index (0-based)
        dealer_seat: Dealer button seat index (0-based)
        total_seats: Total number of seats at the table
    
    Returns:
        Position enum value for hero
    """
    return get_position_from_seat(hero_seat, dealer_seat, total_seats)


def get_active_positions(
    active_seat_indices: List[int],
    dealer_seat: int,
    total_seats: int = 8
) -> List[Position]:
    """
    Get list of positions for all active players.
    
    Args:
        active_seat_indices: List of seat indices with active players
        dealer_seat: Dealer button seat index
        total_seats: Total number of seats
    
    Returns:
        List of Position enum values
    """
    return [
        get_position_from_seat(seat, dealer_seat, total_seats)
        for seat in active_seat_indices
    ]


def seats_in_position_order(
    active_seats: List[int],
    dealer_seat: int,
    total_seats: int = 8
) -> List[int]:
    """
    Sort seats in action order (starting from UTG preflop or SB postflop).
    
    Args:
        active_seats: List of active seat indices
        dealer_seat: Dealer seat index
        total_seats: Total seats at table
    
    Returns:
        Sorted list of seat indices in action order
    """
    def sort_key(seat: int) -> int:
        # Calculate position relative to dealer
        return (seat - dealer_seat) % total_seats
    
    return sorted(active_seats, key=sort_key)


def is_position_late(position: Position) -> bool:
    """Check if position is considered late (CO, BTN)."""
    return position in (Position.CO, Position.BTN)


def is_position_blind(position: Position) -> bool:
    """Check if position is a blind (SB, BB)."""
    return position in (Position.SB, Position.BB)


def is_position_early(position: Position) -> bool:
    """Check if position is early (UTG, UTG+1)."""
    return position in (Position.UTG, Position.UTG1)
