"""
Application configuration and constants.
All paths, thresholds, and settings are centralized here.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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
    background_alpha: float = 0.95
    text_color: str = "#00FF00"  # Bright green for visibility
    background_color: str = "#000000"  # Pure black
    accent_color: str = "#FFFF00"  # Yellow


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
    # Calibrated for Pokerdom - from pixel picker coordinates
    hero_card1_number: Region = field(default_factory=lambda: Region(1166, 986, 35, 46))
    hero_card1_suit: Region = field(default_factory=lambda: Region(1170, 1045, 36, 35))
    hero_card2_number: Region = field(default_factory=lambda: Region(1289, 988, 36, 47))
    hero_card2_suit: Region = field(default_factory=lambda: Region(1287, 1046, 36, 38))
    
    # Board cards regions (5 cards for flop/turn/river) (+462 offset applied)
    board_card_regions: List[Dict] = field(default_factory=lambda: [
        {"number": Region(690, 454, 30, 44), "suit": Region(690, 495, 17, 24)},  # Card 1
        {"number": Region(775, 454, 30, 44), "suit": Region(775, 495, 17, 24)},  # Card 2
        {"number": Region(863, 454, 30, 44), "suit": Region(861, 495, 17, 24)},  # Card 3
        {"number": Region(947, 454, 30, 44), "suit": Region(947, 495, 17, 24)},  # Card 4
        {"number": Region(1033, 454, 30, 44), "suit": Region(1033, 495, 17, 24)},  # Card 5
    ])
    
    # Dealer button pixel checks (one per seat, 8 max)
    # Calibrated for Pokerdom (+462 offset applied)
    # R channel threshold: 50-70 (gray dealer chip)
    dealer_pixels: List[PixelCoord] = field(default_factory=lambda: [
        PixelCoord(1596, 395),   # Seat 0 (+462)
        PixelCoord(2056, 404),   # Seat 1 (+462)
        PixelCoord(2311, 540),   # Seat 2 (+462)
        PixelCoord(2189, 858),   # Seat 3 (+462)
        PixelCoord(1860, 940),   # Seat 4 hero (+462)
        PixelCoord(1292, 858),   # Seat 5 (+462)
        PixelCoord(1164, 539),   # Seat 6 (+462)
        PixelCoord(1418, 400),   # Seat 7 (+462)
    ])
    
    # Active player pixel checks (excluding hero seat)
    # Calibrated for Pokerdom - checks card back presence
    # r_target ~240 (white/light when cards visible, dark when folded)
    active_player_pixels: List[PixelCheck] = field(default_factory=lambda: [
        PixelCheck(1297, 276, r_target=240),    # Seat 0
        PixelCheck(1713, 339, r_target=240),   # Seat 1
        PixelCheck(1936, 673, r_target=240),   # Seat 2
        PixelCheck(1812, 1040, r_target=240),  # Seat 3 (1350+462)
        # Seat 4 is hero - no check needed
        PixelCheck(790, 1040, r_target=240),   # Seat 5 (328+462)
        PixelCheck(599, 673, r_target=240),    # Seat 6 (137+462)
        PixelCheck(820, 338, r_target=240),    # Seat 7 (358+462)
    ])
    
    # Hero's fixed seat index (0-7)
    hero_seat_index: int = 4
    
    # Turn detection pixel (when hero needs to act)
    # Calibrated for Pokerdom - green highlight when hero's turn
    # RGB(113, 205, 134) when active
    turn_indicator_pixel: PixelCoord = field(default_factory=lambda: PixelCoord(982, 1297))
    turn_indicator_color_range: tuple = (100, 130)  # R channel range when active
    
    # Pot region for OCR (relative to window) (+462 offset)
    pot_region: Region = field(default_factory=lambda: Region(841, 320, 130, 35))
    
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
    use_monitor: Optional[int] = None  # Full monitor mode (0=primary, 1=secondary)
    
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
