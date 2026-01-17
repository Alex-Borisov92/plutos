"""
Data models for poker observations and decisions.
All models are immutable dataclasses with validation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional
import json


class Stage(Enum):
    """Poker game stage."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    UNKNOWN = "unknown"


class Action(Enum):
    """Poker action types."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class Position(Enum):
    """Table positions for up to 9 players."""
    BTN = "BTN"
    SB = "SB"
    BB = "BB"
    UTG = "UTG"
    UTG1 = "UTG+1"
    MP = "MP"
    MP1 = "MP+1"
    HJ = "HJ"
    CO = "CO"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Card:
    """
    A single card representation.
    
    Attributes:
        rank: Card rank (2-9, T, J, Q, K, A)
        suit: Card suit (s, h, d, c)
    """
    rank: str
    suit: str
    
    VALID_RANKS = frozenset("23456789TJQKA")
    VALID_SUITS = frozenset("shdc")
    
    def __post_init__(self):
        if self.rank not in self.VALID_RANKS:
            raise ValueError(f"Invalid rank: {self.rank}")
        if self.suit not in self.VALID_SUITS:
            raise ValueError(f"Invalid suit: {self.suit}")
    
    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"
    
    def to_treys(self) -> str:
        """Convert to treys library format."""
        return str(self)
    
    @classmethod
    def from_string(cls, card_str: str) -> "Card":
        """
        Parse card from string like 'Ah', 'Ts', '2c'.
        
        Raises:
            ValueError: If card string is invalid.
        """
        if len(card_str) != 2:
            raise ValueError(f"Card string must be 2 chars: {card_str}")
        return cls(rank=card_str[0].upper(), suit=card_str[1].lower())
    
    @classmethod
    def from_ui_format(cls, ui_str: str) -> "Card":
        """
        Parse card from UI format like 'K heart' or 'A spade'.
        Maps Unicode suits to letters.
        """
        suit_map = {
            "♠": "s", "spade": "s", "spades": "s",
            "♥": "h", "heart": "h", "hearts": "h",
            "♦": "d", "diamond": "d", "diamonds": "d",
            "♣": "c", "club": "c", "clubs": "c",
        }
        
        ui_str = ui_str.strip()
        if len(ui_str) < 2:
            raise ValueError(f"Invalid UI card format: {ui_str}")
        
        # Handle formats like "K heart" or "Kh"
        rank = ui_str[0].upper()
        if rank == "1" and len(ui_str) > 1 and ui_str[1] == "0":
            rank = "T"
            suit_part = ui_str[2:].strip().lower()
        else:
            suit_part = ui_str[1:].strip().lower()
        
        # Map suit
        suit = suit_map.get(suit_part, suit_part)
        if len(suit) > 1:
            suit = suit_map.get(suit, "")
        
        return cls(rank=rank, suit=suit)


@dataclass(frozen=True)
class HoleCards:
    """Hero's hole cards (exactly 2 cards)."""
    card1: Card
    card2: Card
    
    def __str__(self) -> str:
        return f"{self.card1}{self.card2}"
    
    def to_list(self) -> List[str]:
        """Convert to list of treys format strings."""
        return [self.card1.to_treys(), self.card2.to_treys()]
    
    def is_pocket_pair(self) -> bool:
        """Check if cards form a pocket pair."""
        return self.card1.rank == self.card2.rank
    
    def is_suited(self) -> bool:
        """Check if cards are suited."""
        return self.card1.suit == self.card2.suit
    
    def hand_notation(self) -> str:
        """
        Get standard hand notation like 'AKs', 'TT', 'Q9o'.
        """
        ranks = sorted([self.card1.rank, self.card2.rank],
                       key=lambda r: "23456789TJQKA".index(r),
                       reverse=True)
        
        if self.is_pocket_pair():
            return f"{ranks[0]}{ranks[1]}"
        elif self.is_suited():
            return f"{ranks[0]}{ranks[1]}s"
        else:
            return f"{ranks[0]}{ranks[1]}o"


@dataclass(frozen=True)
class BoardCards:
    """Community cards on the board (0-5 cards)."""
    cards: tuple  # Tuple of Card objects
    
    def __post_init__(self):
        if len(self.cards) > 5:
            raise ValueError(f"Board can have max 5 cards, got {len(self.cards)}")
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards)
    
    def to_list(self) -> List[str]:
        """Convert to list of treys format strings."""
        return [c.to_treys() for c in self.cards]
    
    def get_stage(self) -> Stage:
        """Determine game stage from board card count."""
        count = len(self.cards)
        if count == 0:
            return Stage.PREFLOP
        elif count == 3:
            return Stage.FLOP
        elif count == 4:
            return Stage.TURN
        elif count == 5:
            return Stage.RIVER
        else:
            return Stage.UNKNOWN
    
    @classmethod
    def empty(cls) -> "BoardCards":
        """Create empty board (preflop)."""
        return cls(cards=tuple())


@dataclass(frozen=True)
class Observation:
    """
    A snapshot of the poker table state at a point in time.
    This is the core data structure passed through the pipeline.
    """
    timestamp: datetime
    window_id: str
    
    # Game state
    stage: Stage
    hero_position: Position
    dealer_seat: int
    active_players_count: int
    active_positions: tuple  # Tuple of Position enums
    
    # Cards
    hero_cards: Optional[HoleCards]
    board_cards: BoardCards
    
    # Optional additional info
    pot_bb: Optional[float] = None
    is_hero_turn: bool = False
    
    # Raw recognition confidence for debugging
    confidence: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "window_id": self.window_id,
            "stage": self.stage.value,
            "hero_position": self.hero_position.value,
            "dealer_seat": self.dealer_seat,
            "active_players_count": self.active_players_count,
            "active_positions": [p.value for p in self.active_positions],
            "hero_cards": str(self.hero_cards) if self.hero_cards else None,
            "board_cards": self.board_cards.to_list(),
            "pot_bb": self.pot_bb,
            "is_hero_turn": self.is_hero_turn,
            "confidence": self.confidence,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass(frozen=True)
class PreflopDecision:
    """Recommended preflop action."""
    action: Action
    sizing_bb: Optional[float] = None  # For raises
    confidence: float = 1.0
    source: str = "placeholder"  # e.g., "chart_v1", "rule_based"
    reasoning: str = ""
    
    def __str__(self) -> str:
        if self.action == Action.RAISE and self.sizing_bb:
            return f"RAISE {self.sizing_bb}BB"
        return self.action.value.upper()


@dataclass
class HeroTurnEvent:
    """Event emitted when it's hero's turn to act."""
    timestamp: datetime
    window_id: str
    observation: Observation
    
    def to_dict(self) -> dict:
        return {
            "type": "HERO_TURN",
            "timestamp": self.timestamp.isoformat(),
            "window_id": self.window_id,
            "observation": self.observation.to_dict(),
        }
