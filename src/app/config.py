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
    offset_x: int = 800   # Offset from window left edge
    offset_y: int = 900   # Offset from window top edge
    width: int = 224
    height: int = 96
    font_size: int = 10
    background_alpha: float = 0.95
    text_color: str = "#00FF00"  # Bright green
    background_color: str = "#000000"  # Black
    accent_color: str = "#FFFF00"  # Yellow


@dataclass
class VisionConfig:
    """Configuration for card recognition."""
    # OCR config for card ranks (digits + face cards)
    rank_ocr_config: str = "--psm 10 -c tessedit_char_whitelist=23456789TJQKA"
    # OCR config for stacks (digits + comma + BB)
    stack_ocr_config: str = "--psm 7 -c tessedit_char_whitelist=0123456789,."
    # OCR config for pot
    pot_ocr_config: str = "--psm 7 -c tessedit_char_whitelist=0123456789,."
    
    # Valid card values for validation
    valid_ranks: str = "23456789TJQKA"
    valid_suits: str = "shdc"


@dataclass
class TableConfig:
    """Configuration for a single poker table window.
    
    All coordinates are RELATIVE to the window client area origin (0,0).
    Calibrated for new screen - 2025-02-01.
    
    9-max MTT positions: UTG, UTG+1, UTG+2, LJ, HJ, CO, BTN, SB, BB
    """
    
    # Hero cards - number regions for Tesseract OCR
    hero_card1_number: Region = field(default_factory=lambda: Region(871, 824, 30, 43))
    hero_card2_number: Region = field(default_factory=lambda: Region(968, 827, 27, 37))
    
    # Hero cards - suit pixel for color-based detection
    hero_card1_suit_pixel: PixelCoord = field(default_factory=lambda: PixelCoord(876, 891))
    hero_card2_suit_pixel: PixelCoord = field(default_factory=lambda: PixelCoord(973, 888))
    
    # Board cards - number regions for Tesseract OCR (5 cards)
    # Card 5 placeholder - needs calibration
    board_card_regions: List[Region] = field(default_factory=lambda: [
        Region(725, 512, 32, 41),   # Card 1
        Region(823, 513, 32, 43),   # Card 2
        Region(919, 514, 35, 40),   # Card 3
        Region(1109, 512, 38, 45),  # Card 4
        Region(1110, 513, 36, 40),  # Card 5
    ])
    
    # Board cards - suit pixels for color-based detection
    # Card 5 placeholder - needs calibration
    board_suit_pixels: List[PixelCoord] = field(default_factory=lambda: [
        PixelCoord(730, 576),   # Card 1
        PixelCoord(827, 578),   # Card 2
        PixelCoord(925, 576),   # Card 3
        PixelCoord(1116, 581),  # Card 4
        PixelCoord(1117, 575),  # Card 5
    ])
    
    # Dealer button pixel checks (one per seat, 9 max)
    # Seat order: 0=top-center, going clockwise
    dealer_pixels: List[PixelCoord] = field(default_factory=lambda: [
        PixelCoord(839, 344),   # Seat 0
        PixelCoord(1216, 347),  # Seat 1
        PixelCoord(1423, 458),  # Seat 2
        PixelCoord(1320, 717),  # Seat 3
        PixelCoord(1054, 784),  # Seat 4 (hero)
        PixelCoord(590, 718),   # Seat 5
        PixelCoord(488, 458),   # Seat 6
        PixelCoord(695, 345),   # Seat 7
    ])
    
    # Active player pixel checks (card back presence)
    # r_target ~240 (white/light when cards visible)
    active_player_pixels: List[PixelCheck] = field(default_factory=lambda: [
        PixelCheck(933, 246, r_target=240),   # Seat 0
        PixelCheck(1302, 295, r_target=220),  # Seat 1
        PixelCheck(1498, 566, r_target=240),  # Seat 2
        PixelCheck(1333, 865, r_target=240),  # Seat 3
        # Seat 4 is hero - no check needed
        PixelCheck(565, 865, r_target=238),   # Seat 5
        PixelCheck(408, 568, r_target=240),   # Seat 6
        PixelCheck(594, 297, r_target=248),   # Seat 7
    ])
    
    # Player stack regions for OCR (all seats including hero)
    player_stack_regions: List[Optional[Region]] = field(default_factory=lambda: [
        Region(895, 313, 122, 27),   # Seat 0
        Region(1283, 362, 120, 26),  # Seat 1
        Region(1460, 638, 109, 28),  # Seat 2
        Region(1299, 935, 120, 22),  # Seat 3
        Region(894, 985, 129, 28),   # Seat 4 (hero)
        Region(499, 931, 112, 31),   # Seat 5
        Region(337, 642, 115, 27),   # Seat 6
        Region(523, 365, 102, 30),   # Seat 7
    ])
    
    # Hero's fixed seat index (0-7 for 8-max, 0-8 for 9-max)
    hero_seat_index: int = 4
    
    # Turn detection pixel (green highlight when hero's turn)
    # RGB(84, 208, 136) when active
    turn_indicator_pixel: PixelCoord = field(default_factory=lambda: PixelCoord(705, 1070))
    turn_indicator_color_range: tuple = (70, 100)  # R channel range when active (green has low R)
    
    # Pot region for OCR (format: "Банк: 2,35 ББ")
    pot_region: Region = field(default_factory=lambda: Region(837, 463, 211, 36))
    
    # Hand ID region for detecting new hands
    hand_id_region: Region = field(default_factory=lambda: Region(418, 6, 101, 10))
    
    # Hero stack region (same as player_stack_regions[hero_seat_index])
    hero_stack_region: Region = field(default_factory=lambda: Region(894, 985, 129, 28))
    
    # Position names for 9-max MTT (from preflop ranges)
    # Order matches seat indices starting from BTN
    positions_9max: List[str] = field(default_factory=lambda: [
        "BTN", "SB", "BB", "UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"
    ])
    
    # Position names for 8-max (no UTG+2)
    positions_8max: List[str] = field(default_factory=lambda: [
        "BTN", "SB", "BB", "UTG", "UTG+1", "LJ", "HJ", "CO"
    ])
    
    # Default player count
    player_count: int = 8


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
    use_monitor: Optional[int] = None  # Full monitor mode
    
    # Default table config
    default_table: TableConfig = field(default_factory=TableConfig)
    
    # Game settings
    player_count: int = 8  # Default 8 players (can be 6, 8, or 9)
    table_count: int = 1   # Number of tables to track
    
    # Feature flags
    debug_screenshots: bool = False
    verbose_logging: bool = False
    rfi_only_mode: bool = True  # Only show opens when no action before us


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
    logging.getLogger("pytesseract").setLevel(logging.WARNING)
