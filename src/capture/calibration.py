"""
Calibration utilities for setting up window-relative coordinates.

The original script used absolute screen coordinates (often negative on multi-monitor
setups). This module helps convert those to window-relative coordinates and
provides tools for visual calibration.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging
import json
from pathlib import Path

from ..app.config import Region, PixelCoord, PixelCheck, TableConfig


logger = logging.getLogger(__name__)


@dataclass
class CalibrationPoint:
    """A named calibration point with its screen and relative coordinates."""
    name: str
    screen_x: int
    screen_y: int
    relative_x: Optional[int] = None
    relative_y: Optional[int] = None


def convert_absolute_to_relative(
    abs_x: int,
    abs_y: int,
    window_left: int,
    window_top: int
) -> Tuple[int, int]:
    """
    Convert absolute screen coordinates to window-relative coordinates.
    
    Args:
        abs_x: Absolute X coordinate on screen
        abs_y: Absolute Y coordinate on screen
        window_left: Window's left edge screen coordinate
        window_top: Window's top edge screen coordinate
    
    Returns:
        (relative_x, relative_y) tuple
    """
    return (abs_x - window_left, abs_y - window_top)


def convert_legacy_coords(
    legacy_left: int,
    legacy_top: int,
    screen_width: int = 1920,
    window_left: int = 0,
    window_top: int = 0
) -> Tuple[int, int]:
    """
    Convert legacy negative coordinates from original script to relative.
    
    The original script used negative coordinates measured from the right edge
    of a monitor. This function converts them to positive window-relative coords.
    
    Args:
        legacy_left: Original left coordinate (often negative)
        legacy_top: Original top coordinate
        screen_width: Width of the screen the coords were based on
        window_left: Window's left edge on screen
        window_top: Window's top edge on screen
    
    Returns:
        (relative_x, relative_y) tuple
    """
    # If coordinates are negative, they were measured from the right edge
    if legacy_left < 0:
        # Convert to positive screen coordinate
        abs_x = screen_width + legacy_left
    else:
        abs_x = legacy_left
    
    abs_y = legacy_top
    
    return convert_absolute_to_relative(abs_x, abs_y, window_left, window_top)


def create_calibration_from_legacy(
    legacy_dealer_coords: List[Dict[str, int]],
    legacy_active_coords: List[Dict[str, int]],
    legacy_hand_regions: Dict[str, Dict[str, int]],
    legacy_board_regions: List[Dict[str, Dict[str, int]]],
    legacy_pot_region: Dict[str, int],
    screen_width: int = 1920,
    window_left: int = 0,
    window_top: int = 0,
    hero_seat: int = 4
) -> TableConfig:
    """
    Create a TableConfig from legacy coordinate format.
    
    This helps migrate from the old absolute-coordinate system to the new
    window-relative system.
    
    Args:
        legacy_dealer_coords: List of {'left': x, 'top': y} dicts
        legacy_active_coords: List of {'left': x, 'top': y, 'r': target} dicts
        legacy_hand_regions: Dict with card1_number, card1_suit, etc.
        legacy_board_regions: List of dicts with number and suit regions
        legacy_pot_region: {'left': x, 'top': y, 'width': w, 'height': h}
        screen_width: Screen width for negative coord conversion
        window_left: Window left edge
        window_top: Window top edge
        hero_seat: Hero's seat index
    
    Returns:
        TableConfig with converted coordinates
    """
    # Convert dealer pixels
    dealer_pixels = []
    for coord in legacy_dealer_coords:
        rx, ry = convert_legacy_coords(
            coord['left'], coord['top'],
            screen_width, window_left, window_top
        )
        dealer_pixels.append(PixelCoord(rx, ry))
    
    # Convert active player pixels
    active_pixels = []
    for coord in legacy_active_coords:
        rx, ry = convert_legacy_coords(
            coord['left'], coord['top'],
            screen_width, window_left, window_top
        )
        active_pixels.append(PixelCheck(rx, ry, coord.get('r', 40)))
    
    # Convert hand card regions
    def convert_region(reg: Dict[str, int]) -> Region:
        rx, ry = convert_legacy_coords(
            reg['left'], reg['top'],
            screen_width, window_left, window_top
        )
        return Region(rx, ry, reg['width'], reg['height'])
    
    hero_card1_number = convert_region(legacy_hand_regions.get('card1_number', {
        'left': -860, 'top': 1090, 'width': 28, 'height': 43
    }))
    hero_card1_suit = convert_region(legacy_hand_regions.get('card1_suit', {
        'left': -859, 'top': 1132, 'width': 17, 'height': 24
    }))
    hero_card2_number = convert_region(legacy_hand_regions.get('card2_number', {
        'left': -828, 'top': 1090, 'width': 28, 'height': 43
    }))
    hero_card2_suit = convert_region(legacy_hand_regions.get('card2_suit', {
        'left': -828, 'top': 1132, 'width': 17, 'height': 24
    }))
    
    # Convert board regions
    board_regions = []
    for region in legacy_board_regions:
        board_regions.append({
            'number': convert_region(region['number']),
            'suit': convert_region(region['suit']),
        })
    
    # Convert pot region
    pot_rx, pot_ry = convert_legacy_coords(
        legacy_pot_region['left'], legacy_pot_region['top'],
        screen_width, window_left, window_top
    )
    pot_region = Region(
        pot_rx, pot_ry,
        legacy_pot_region['width'], legacy_pot_region['height']
    )
    
    return TableConfig(
        hero_card1_number=hero_card1_number,
        hero_card1_suit=hero_card1_suit,
        hero_card2_number=hero_card2_number,
        hero_card2_suit=hero_card2_suit,
        board_card_regions=board_regions,
        dealer_pixels=dealer_pixels,
        active_player_pixels=active_pixels,
        hero_seat_index=hero_seat,
        pot_region=pot_region,
    )


def save_calibration(config: TableConfig, path: Path) -> bool:
    """
    Save table calibration to JSON file.
    
    Args:
        config: TableConfig to save
        path: Output file path
    
    Returns:
        True if saved successfully
    """
    try:
        data = {
            "hero_seat_index": config.hero_seat_index,
            "hero_card1_number": {
                "left": config.hero_card1_number.left,
                "top": config.hero_card1_number.top,
                "width": config.hero_card1_number.width,
                "height": config.hero_card1_number.height,
            },
            "hero_card1_suit_pixel": {
                "left": config.hero_card1_suit_pixel.left,
                "top": config.hero_card1_suit_pixel.top,
            },
            "hero_card2_number": {
                "left": config.hero_card2_number.left,
                "top": config.hero_card2_number.top,
                "width": config.hero_card2_number.width,
                "height": config.hero_card2_number.height,
            },
            "hero_card2_suit_pixel": {
                "left": config.hero_card2_suit_pixel.left,
                "top": config.hero_card2_suit_pixel.top,
            },
            "dealer_pixels": [
                {"left": p.left, "top": p.top}
                for p in config.dealer_pixels
            ],
            "active_player_pixels": [
                {"left": p.left, "top": p.top, "r_target": p.r_target}
                for p in config.active_player_pixels
            ],
            "pot_region": {
                "left": config.pot_region.left,
                "top": config.pot_region.top,
                "width": config.pot_region.width,
                "height": config.pot_region.height,
            },
            "turn_indicator_pixel": {
                "left": config.turn_indicator_pixel.left,
                "top": config.turn_indicator_pixel.top,
            },
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved calibration to {path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save calibration: {e}")
        return False


def load_calibration(path: Path) -> Optional[TableConfig]:
    """
    Load table calibration from JSON file.
    
    Args:
        path: Path to calibration file
    
    Returns:
        TableConfig or None if load failed
    """
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        def region_from_dict(d: dict) -> Region:
            return Region(d['left'], d['top'], d['width'], d['height'])
        
        def pixel_coord_from_dict(d: dict) -> PixelCoord:
            return PixelCoord(d['left'], d['top'])
        
        config = TableConfig(
            hero_seat_index=data.get('hero_seat_index', 4),
            hero_card1_number=region_from_dict(data['hero_card1_number']),
            hero_card1_suit_pixel=pixel_coord_from_dict(data['hero_card1_suit_pixel']),
            hero_card2_number=region_from_dict(data['hero_card2_number']),
            hero_card2_suit_pixel=pixel_coord_from_dict(data['hero_card2_suit_pixel']),
            dealer_pixels=[
                PixelCoord(p['left'], p['top'])
                for p in data.get('dealer_pixels', [])
            ],
            active_player_pixels=[
                PixelCheck(p['left'], p['top'], p.get('r_target', 40))
                for p in data.get('active_player_pixels', [])
            ],
            pot_region=region_from_dict(data.get('pot_region', {
                'left': 400, 'top': 300, 'width': 130, 'height': 35
            })),
        )
        
        logger.info(f"Loaded calibration from {path}")
        return config
        
    except FileNotFoundError:
        logger.warning(f"Calibration file not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Failed to load calibration: {e}")
        return None
