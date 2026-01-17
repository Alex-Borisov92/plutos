"""
Application configuration and constants.
All paths, thresholds, and settings are centralized here.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
import logging


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
NUMBER_TEMPLATES_DIR = PROJECT_ROOT / "number_templates"
DATA_DIR = PROJECT_ROOT / "data"

# Tesseract configuration
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass(frozen=True)
class Region:
    """Screen region definition relative to window origin."""
    left: int
    top: int
    width: int
    height: int


@dataclass(frozen=True)
class PixelCoord:
    """Single pixel coordinate relative to window origin."""
    left: int
    top: int


@dataclass(frozen=True)
class PixelCheck:
    """Pixel check with expected color channel value."""
    left: int
    top: int
    r_target: int  # Expected red channel value for active detection


@dataclass
class PollerConfig:
    """Configuration for the state polling worker."""
    poll_frequency_hz: float = 10.0  # Polls per second
    debounce_ms: int = 100  # Debounce time in milliseconds
    max_consecutive_errors: int = 5  # Max errors before backing off


@dataclass
class OverlayConfig:
    """Configuration for the overlay window."""
    offset_x: int = 10  # Offset from window left edge
    offset_y: int = 10  # Offset from window top edge
    width: int = 280
    height: int = 120
    font_size: int = 12
    background_alpha: float = 0.85
    text_color: str = "#FFFFFF"
    background_color: str = "#1a1a2e"
    accent_color: str = "#e94560"


@dataclass
class VisionConfig:
    """Configuration for card recognition."""
    template_match_threshold: float = 0.4
    suit_match_threshold: float = 0.3
    ocr_config: str = "--psm 7 -c tessedit_char_whitelist=0123456789,."
    
    # Valid card values for validation
    valid_ranks: str = "23456789TJQKA"
    valid_suits: str = "shdc"


@dataclass
class TableConfig:
    """Configuration for a single poker table window.
    
    All coordinates are RELATIVE to the window client area origin (0,0).
    This allows the same config to work regardless of window position on screen.
    
    NOTE: You need to calibrate these values for your specific poker client.
    Use the calibration tool (coming soon) or manually measure pixel positions.
    
    The original script used negative screen coordinates, which were tied to
    a specific monitor setup. These relative coords should be positive offsets
    from the top-left of the poker window's client area.
    """
    # Hero cards regions (relative to window client area)
    # Example values for a ~1000px wide window - CALIBRATE FOR YOUR CLIENT
    hero_card1_number: Region = field(default_factory=lambda: Region(430, 690, 28, 43))
    hero_card1_suit: Region = field(default_factory=lambda: Region(431, 732, 17, 24))
    hero_card2_number: Region = field(default_factory=lambda: Region(462, 690, 28, 43))
    hero_card2_suit: Region = field(default_factory=lambda: Region(462, 732, 17, 24))
    
    # Board cards regions (5 cards for flop/turn/river)
    board_card_regions: List[Dict] = field(default_factory=lambda: [
        {"number": Region(228, 454, 30, 44), "suit": Region(228, 495, 17, 24)},  # Card 1
        {"number": Region(313, 454, 30, 44), "suit": Region(313, 495, 17, 24)},  # Card 2
        {"number": Region(401, 454, 30, 44), "suit": Region(399, 495, 17, 24)},  # Card 3
        {"number": Region(485, 454, 30, 44), "suit": Region(485, 495, 17, 24)},  # Card 4
        {"number": Region(571, 454, 30, 44), "suit": Region(571, 495, 17, 24)},  # Card 5
    ])
    
    # Dealer button pixel checks (one per seat, 8 max)
    # Calibrated for Pokerdom - window at (-470, -1448)
    # R channel threshold: 50-70 (gray dealer chip)
    dealer_pixels: List[PixelCoord] = field(default_factory=lambda: [
        PixelCoord(1141, 403),   # Seat 0
        PixelCoord(1603, 407),   # Seat 1
        PixelCoord(1859, 547),   # Seat 2
        PixelCoord(1735, 866),   # Seat 3
        PixelCoord(1406, 948),   # Seat 4 (hero seat)
        PixelCoord(833, 865),    # Seat 5
        PixelCoord(709, 547),    # Seat 6
        PixelCoord(965, 407),    # Seat 7
    ])
    
    # Active player pixel checks (excluding hero seat)
    # r_target is the expected red channel value when player is active
    active_player_pixels: List[PixelCheck] = field(default_factory=lambda: [
        PixelCheck(220, 233, r_target=37),   # Seat 0
        PixelCheck(710, 231, r_target=40),   # Seat 1
        PixelCheck(942, 409, r_target=40),   # Seat 2
        PixelCheck(925, 635, r_target=44),   # Seat 3
        # Seat 4 is hero - no check needed
        PixelCheck(310, 730, r_target=43),   # Seat 5
        PixelCheck(-3, 645, r_target=38),    # Seat 6
        PixelCheck(-18, 403, r_target=42),   # Seat 7
    ])
    
    # Hero's fixed seat index (0-7)
    hero_seat_index: int = 4
    
    # Turn detection pixel (when hero needs to act)
    # This should be a pixel that changes color when it's hero's turn
    # Often the action timer bar or hero card highlight
    turn_indicator_pixel: PixelCoord = field(default_factory=lambda: PixelCoord(450, 750))
    turn_indicator_color_range: tuple = (200, 255)  # R channel range when active
    
    # Pot region for OCR (relative to window)
    pot_region: Region = field(default_factory=lambda: Region(379, 320, 130, 35))
    
    # Position names for 8-max table (starting from dealer, going clockwise)
    positions: List[str] = field(default_factory=lambda: [
        "BTN", "SB", "BB", "UTG", "UTG+1", "MP", "HJ", "CO"
    ])


@dataclass
class AppConfig:
    """Main application configuration."""
    # Database
    db_path: Path = field(default_factory=lambda: DATA_DIR / "plutos.db")
    
    # Component configs
    poller: PollerConfig = field(default_factory=PollerConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    
    # Multi-table settings
    max_tables: int = 4
    window_title_pattern: str = "NL Hold'em"  # Pattern to match poker windows
    
    # Default table config (will be calibrated per window)
    default_table: TableConfig = field(default_factory=TableConfig)
    
    # Feature flags
    debug_screenshots: bool = False
    verbose_logging: bool = False


def get_config() -> AppConfig:
    """Get application configuration singleton."""
    return AppConfig()


def setup_logging(config: AppConfig) -> None:
    """Configure logging based on app config."""
    level = logging.DEBUG if config.verbose_logging else LOG_LEVEL
    logging.basicConfig(level=level, format=LOG_FORMAT)
    
    # Reduce noise from external libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("mss").setLevel(logging.WARNING)
