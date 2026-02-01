"""
Position and seat mapping logic.
Handles conversion between seat indices and position names based on dealer location.

9-max MTT positions: UTG, UTG+1, UTG+2, LJ, HJ, CO, BTN, SB, BB
8-max positions: UTG, UTG+1, LJ, HJ, CO, BTN, SB, BB
"""
from typing import List, Optional
from .models import Position


# Standard 9-max position order starting from BTN (going clockwise)
POSITIONS_9MAX = [
    Position.BTN,
    Position.SB,
    Position.BB,
    Position.UTG,
    Position.UTG1,    # UTG+1
    Position.UTG2,    # UTG+2
    Position.LJ,      # Lojack
    Position.HJ,      # Hijack
    Position.CO,      # Cutoff
]

# 8-max positions (no UTG+2)
POSITIONS_8MAX = [
    Position.BTN,
    Position.SB,
    Position.BB,
    Position.UTG,
    Position.UTG1,    # UTG+1
    Position.LJ,      # Lojack
    Position.HJ,      # Hijack
    Position.CO,      # Cutoff
]

# 6-max positions
POSITIONS_6MAX = [
    Position.BTN,
    Position.SB,
    Position.BB,
    Position.UTG,
    Position.HJ,
    Position.CO,
]

# Heads-up / 2-max
POSITIONS_2MAX = [
    Position.BTN,  # BTN is also SB heads-up
    Position.BB,
]


def get_positions_for_table_size(total_seats: int) -> List[Position]:
    """
    Get position list for given table size.
    
    Args:
        total_seats: Number of players at the table
    
    Returns:
        List of Position enums in action order (BTN first)
    """
    if total_seats <= 2:
        return POSITIONS_2MAX
    elif total_seats <= 6:
        return POSITIONS_6MAX
    elif total_seats <= 8:
        return POSITIONS_8MAX
    else:
        return POSITIONS_9MAX


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
    positions = get_positions_for_table_size(total_seats)
    
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


# Position classification helpers

def is_position_late(position: Position) -> bool:
    """Check if position is considered late (CO, BTN)."""
    return position in (Position.CO, Position.BTN)


def is_position_blind(position: Position) -> bool:
    """Check if position is a blind (SB, BB)."""
    return position in (Position.SB, Position.BB)


def is_position_early(position: Position) -> bool:
    """Check if position is early (UTG, UTG+1, UTG+2)."""
    return position in (Position.UTG, Position.UTG1, Position.UTG2)


def is_position_middle(position: Position) -> bool:
    """Check if position is middle (LJ, HJ)."""
    return position in (Position.LJ, Position.HJ)


# Preflop action order (first to act -> last to act)
PREFLOP_ACTION_ORDER = [
    Position.UTG,
    Position.UTG1,
    Position.UTG2,
    Position.LJ,
    Position.HJ,
    Position.CO,
    Position.BTN,
    Position.SB,
    Position.BB,
]


def get_preflop_action_index(position: Position) -> int:
    """
    Get position's index in preflop action order.
    
    Returns:
        0 for UTG (first), 8 for BB (last), -1 if unknown
    """
    try:
        return PREFLOP_ACTION_ORDER.index(position)
    except ValueError:
        return -1


def is_before_hero(
    villain_position: Position,
    hero_position: Position
) -> bool:
    """
    Check if villain acts before hero in preflop action.
    
    Args:
        villain_position: Villain's position
        hero_position: Hero's position
    
    Returns:
        True if villain acts before hero
    """
    villain_idx = get_preflop_action_index(villain_position)
    hero_idx = get_preflop_action_index(hero_position)
    
    if villain_idx < 0 or hero_idx < 0:
        return False
    
    return villain_idx < hero_idx


def position_to_range_key(position: Position) -> Optional[str]:
    """
    Convert Position enum to range lookup key (for preflop_ranges).
    
    Args:
        position: Position enum
    
    Returns:
        String key like "UTG+1", "LJ", etc.
    """
    mapping = {
        Position.BTN: "BTN",
        Position.SB: "SB",
        Position.BB: "BB",
        Position.UTG: "UTG",
        Position.UTG1: "UTG+1",
        Position.UTG2: "UTG+2",
        Position.LJ: "LJ",
        Position.HJ: "HJ",
        Position.CO: "CO",
        # Legacy
        Position.MP: "UTG+2",
        Position.MP1: "LJ",
    }
    return mapping.get(position)
