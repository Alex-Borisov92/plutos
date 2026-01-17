"""
UI state detection using pixel-based checks.
Detects dealer position, active players, and hero's turn.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging

import re
try:
    import pytesseract
    from PIL import Image
    # Set Tesseract path for Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from ..app.config import PixelCoord, PixelCheck, TableConfig, Region
from ..capture.screen_capture import ScreenCapture, capture_pixel


logger = logging.getLogger(__name__)


@dataclass
class DealerDetectionResult:
    """Result of dealer position detection."""
    seat_index: Optional[int]
    pixel_color: Optional[Tuple[int, int, int]]
    confidence: float


@dataclass
class HandIdResult:
    """Result of hand ID detection."""
    hand_id: Optional[str]
    is_new_hand: bool
    previous_id: Optional[str]


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


@dataclass
class HeroStackResult:
    """Result of hero stack detection."""
    stack_bb: Optional[float]
    raw_text: Optional[str]
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
        self._last_hand_id: Optional[str] = None
    
    def detect_dealer(
        self,
        window_offset: Tuple[int, int],
        r_min: int = 50,
        r_max: int = 75
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
        debug_colors = []
        for seat_idx, pixel in enumerate(self.config.dealer_pixels):
            color = self._capture.capture_pixel(
                pixel.left, pixel.top, window_offset
            )
            
            if color is None:
                debug_colors.append(f"S{seat_idx}:None")
                continue
            
            r, g, b = color
            debug_colors.append(f"S{seat_idx}:({r},{g},{b})")
            
            # Dealer button is gray: R,G,B all in range 50-75 and similar to each other
            is_gray = (r_min <= r <= r_max and 
                       r_min <= g <= r_max and 
                       r_min <= b <= r_max and
                       abs(r - g) < 15 and abs(g - b) < 15)
            
            if is_gray:
                logger.debug(f"Dealer found at S{seat_idx}: {color}")
                return DealerDetectionResult(
                    seat_index=seat_idx,
                    pixel_color=color,
                    confidence=1.0
                )
        
        logger.debug(f"Dealer colors: {' '.join(debug_colors)}")
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
        
        # All seats enabled
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
            
            # Debug logging disabled
            # logger.debug(f"Seat {seat_idx}: RGB({r},{g},{b})")
            
            # Card back is white/light (~240 RGB). Check if all channels > 200
            # When folded, pixel shows green table or colored avatar
            if r > 200 and g > 200 and b > 200:
                active_seats.append(seat_idx)
                seat_colors[seat_idx] = color
        
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
        # Turn indicator is green - check G channel > 150 and G > R
        is_turn = g > 150 and g > r
        confidence = 1.0 if is_turn else 0.0
        
        return TurnDetectionResult(
            is_hero_turn=is_turn,
            pixel_color=color,
            confidence=confidence
        )
    
    def detect_hand_id(
        self,
        window_offset: Tuple[int, int]
    ) -> HandIdResult:
        """
        Detect hand ID from screen using OCR.
        Compares with previous ID to detect new hand.
        
        Args:
            window_offset: (x, y) screen offset of window client area
            
        Returns:
            HandIdResult with current hand ID and new hand flag
        """
        if not HAS_OCR:
            return HandIdResult(hand_id=None, is_new_hand=False, previous_id=self._last_hand_id)
        
        region = self.config.hand_id_region
        img = self._capture.capture_region(region, window_offset)
        
        if img is None:
            return HandIdResult(hand_id=None, is_new_hand=False, previous_id=self._last_hand_id)
        
        # OCR the region
        try:
            text = pytesseract.image_to_string(img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
            # Extract digits only
            digits = re.sub(r'\D', '', text)
            hand_id = digits if digits else None
        except Exception as e:
            logger.debug(f"OCR error: {e}")
            hand_id = None
        
        # Check if new hand
        is_new = hand_id is not None and hand_id != self._last_hand_id and len(hand_id) > 5
        previous = self._last_hand_id
        
        if is_new:
            logger.info(f"New hand detected: {hand_id} (prev: {previous})")
            self._last_hand_id = hand_id
        
        return HandIdResult(hand_id=hand_id, is_new_hand=is_new, previous_id=previous)
    
    def detect_hero_stack(
        self,
        window_offset: Tuple[int, int]
    ) -> HeroStackResult:
        """
        Detect hero's stack size using OCR.
        Format expected: "XX,XX BB" or "XX.XX BB"
        
        Args:
            window_offset: (x, y) screen offset of window client area
            
        Returns:
            HeroStackResult with stack in BB
        """
        if not HAS_OCR:
            return HeroStackResult(stack_bb=None, raw_text=None, confidence=0.0)
        
        region = self.config.hero_stack_region
        img = self._capture.capture_region(region, window_offset)
        
        if img is None:
            return HeroStackResult(stack_bb=None, raw_text=None, confidence=0.0)
        
        # OCR the region
        try:
            # Allow digits, comma, period, space, B
            text = pytesseract.image_to_string(
                img, 
                config='--psm 7 -c tessedit_char_whitelist=0123456789,. BB'
            ).strip()
            
            if not text:
                return HeroStackResult(stack_bb=None, raw_text=None, confidence=0.0)
            
            # Parse the number - format is "50,04 BB" or "50.04 BB"
            # Remove "BB" suffix and whitespace
            number_str = re.sub(r'[Bb\s]+$', '', text)
            # Replace comma with dot for float parsing
            number_str = number_str.replace(',', '.')
            # Extract the number
            match = re.search(r'(\d+\.?\d*)', number_str)
            
            if match:
                stack_bb = float(match.group(1))
                return HeroStackResult(
                    stack_bb=stack_bb,
                    raw_text=text,
                    confidence=1.0
                )
            
            return HeroStackResult(stack_bb=None, raw_text=text, confidence=0.0)
            
        except Exception as e:
            logger.debug(f"Stack OCR error: {e}")
            return HeroStackResult(stack_bb=None, raw_text=None, confidence=0.0)
    
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
