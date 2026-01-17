"""
UI state detection using pixel-based checks.
Detects dealer position, active players, and hero's turn.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging

from ..app.config import PixelCoord, PixelCheck, TableConfig
from ..capture.screen_capture import ScreenCapture, capture_pixel


logger = logging.getLogger(__name__)


@dataclass
class DealerDetectionResult:
    """Result of dealer position detection."""
    seat_index: Optional[int]
    pixel_color: Optional[Tuple[int, int, int]]
    confidence: float


@dataclass
class ActivePlayersResult:
    """Result of active players detection."""
    active_seats: List[int]
    seat_colors: dict  # seat_index -> (R, G, B)
    count: int


@dataclass
class TurnDetectionResult:
    """Result of hero turn detection."""
    is_hero_turn: bool
    pixel_color: Optional[Tuple[int, int, int]]
    confidence: float


class UIStateDetector:
    """
    Detects UI state by checking pixel colors at specific positions.
    All coordinates are window-relative.
    """
    
    def __init__(
        self,
        config: TableConfig,
        capture: Optional[ScreenCapture] = None
    ):
        """
        Initialize UI state detector.
        
        Args:
            config: Table configuration with pixel coordinates
            capture: Screen capture instance (creates new if not provided)
        """
        self.config = config
        self._capture = capture or ScreenCapture()
    
    def detect_dealer(
        self,
        window_offset: Tuple[int, int],
        r_min: int = 200,
        r_max: int = 255
    ) -> DealerDetectionResult:
        """
        Find the dealer button by checking pixel colors.
        
        Args:
            window_offset: (x, y) screen offset of window client area
            r_min: Minimum red channel value for dealer detection
            r_max: Maximum red channel value for dealer detection
        
        Returns:
            DealerDetectionResult with seat index or None
        """
        for seat_idx, pixel in enumerate(self.config.dealer_pixels):
            color = self._capture.capture_pixel(
                pixel.left, pixel.top, window_offset
            )
            
            if color is None:
                continue
            
            r, g, b = color
            
            # Check if red channel is in expected range (dealer button is red/white)
            if r_min <= r <= r_max:
                logger.debug(f"Dealer detected at seat {seat_idx}, color=RGB({r},{g},{b})")
                return DealerDetectionResult(
                    seat_index=seat_idx,
                    pixel_color=color,
                    confidence=1.0
                )
        
        logger.debug("Dealer not detected")
        return DealerDetectionResult(
            seat_index=None,
            pixel_color=None,
            confidence=0.0
        )
    
    def detect_active_players(
        self,
        window_offset: Tuple[int, int],
        tolerance: int = 5
    ) -> ActivePlayersResult:
        """
        Detect which seats have active players.
        
        Args:
            window_offset: (x, y) screen offset of window client area
            tolerance: Color matching tolerance
        
        Returns:
            ActivePlayersResult with list of active seat indices
        """
        active_seats = []
        seat_colors = {}
        
        # Build seat index mapping - active_player_pixels excludes hero seat
        # So we need to map list index to actual seat index
        all_seats = list(range(8))
        check_seats = [s for s in all_seats if s != self.config.hero_seat_index]
        
        for list_idx, check in enumerate(self.config.active_player_pixels):
            if list_idx >= len(check_seats):
                break
                
            seat_idx = check_seats[list_idx]
            
            color = self._capture.capture_pixel(
                check.left, check.top, window_offset
            )
            
            if color is None:
                continue
            
            r, g, b = color
            
            # Check if red channel matches expected value within tolerance
            if abs(r - check.r_target) <= tolerance:
                active_seats.append(seat_idx)
                seat_colors[seat_idx] = color
                logger.debug(f"Active player at seat {seat_idx}, color=RGB({r},{g},{b})")
        
        return ActivePlayersResult(
            active_seats=active_seats,
            seat_colors=seat_colors,
            count=len(active_seats)
        )
    
    def detect_hero_turn(
        self,
        window_offset: Tuple[int, int]
    ) -> TurnDetectionResult:
        """
        Detect if it's hero's turn to act.
        
        Args:
            window_offset: (x, y) screen offset of window client area
        
        Returns:
            TurnDetectionResult indicating if hero should act
        """
        pixel = self.config.turn_indicator_pixel
        color = self._capture.capture_pixel(
            pixel.left, pixel.top, window_offset
        )
        
        if color is None:
            return TurnDetectionResult(
                is_hero_turn=False,
                pixel_color=None,
                confidence=0.0
            )
        
        r, g, b = color
        r_min, r_max = self.config.turn_indicator_color_range
        
        is_turn = r_min <= r <= r_max
        confidence = 1.0 if is_turn else 0.0
        
        logger.debug(f"Turn detection: is_turn={is_turn}, color=RGB({r},{g},{b})")
        
        return TurnDetectionResult(
            is_hero_turn=is_turn,
            pixel_color=color,
            confidence=confidence
        )
    
    def get_full_state(
        self,
        window_offset: Tuple[int, int]
    ) -> dict:
        """
        Get complete UI state in one call.
        
        Args:
            window_offset: (x, y) screen offset of window client area
        
        Returns:
            Dict with dealer, active_players, and hero_turn results
        """
        return {
            "dealer": self.detect_dealer(window_offset),
            "active_players": self.detect_active_players(window_offset),
            "hero_turn": self.detect_hero_turn(window_offset),
        }


def is_valid_rgb(color: Optional[Tuple[int, int, int]]) -> bool:
    """Check if color tuple is valid."""
    if color is None:
        return False
    if len(color) != 3:
        return False
    return all(0 <= c <= 255 for c in color)
