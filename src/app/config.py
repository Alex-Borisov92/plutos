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
    """
    # Hero cards regions (relative to window)
    hero_card1_number: Region = field(default_factory=lambda: Region(60, 700, 28, 43))
    hero_card1_suit: Region = field(default_factory=lambda: Region(61, 742, 17, 24))
    hero_card2_number: Region = field(default_factory=lambda: Region(92, 700, 28, 43))
    hero_card2_suit: Region = field(default_factory=lambda: Region(92, 742, 17, 24))
    
    # Board cards regions (5 cards for flop/turn/river)
    board_card_regions: List[Dict] = field(default_factory=list)
    
    # Dealer button pixel checks (one per seat, 8 max)
    dealer_pixels: List[PixelCoord] = field(default_factory=list)
    
    # Active player pixel checks (excluding hero seat)
    active_player_pixels: List[PixelCheck] = field(default_factory=list)
    
    # Hero's fixed seat index (0-7)
    hero_seat_index: int = 4
    
    # Turn detection pixel (when hero needs to act)
    turn_indicator_pixel: PixelCoord = field(default_factory=lambda: PixelCoord(100, 750))
    turn_indicator_color_range: tuple = (200, 255)  # R channel range
    
    # Pot region for OCR
    pot_region: Region = field(default_factory=lambda: Region(400, 300, 130, 35))
    
    # Position names for 8-max table
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
