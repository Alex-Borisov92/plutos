"""
Tests for calibration utilities.
"""
import pytest
import tempfile
from pathlib import Path

from src.capture.calibration import (
    convert_absolute_to_relative,
    convert_legacy_coords,
    save_calibration,
    load_calibration,
)
from src.app.config import TableConfig, Region, PixelCoord, PixelCheck


class TestCoordinateConversion:
    """Tests for coordinate conversion functions."""
    
    def test_absolute_to_relative_simple(self):
        """Test simple absolute to relative conversion."""
        rel_x, rel_y = convert_absolute_to_relative(
            abs_x=500, abs_y=300,
            window_left=100, window_top=50
        )
        assert rel_x == 400
        assert rel_y == 250
    
    def test_absolute_to_relative_at_origin(self):
        """Test when absolute coords equal window position."""
        rel_x, rel_y = convert_absolute_to_relative(
            abs_x=100, abs_y=50,
            window_left=100, window_top=50
        )
        assert rel_x == 0
        assert rel_y == 0
    
    def test_legacy_negative_coords(self):
        """Test conversion of legacy negative coordinates."""
        # Original used -860 on a 1920px screen
        # This means 1920 + (-860) = 1060 absolute
        # If window is at 0,0, relative is also 1060
        rel_x, rel_y = convert_legacy_coords(
            legacy_left=-860,
            legacy_top=500,
            screen_width=1920,
            window_left=0,
            window_top=0
        )
        assert rel_x == 1060
        assert rel_y == 500
    
    def test_legacy_negative_with_window_offset(self):
        """Test legacy coords with window not at origin."""
        rel_x, rel_y = convert_legacy_coords(
            legacy_left=-860,
            legacy_top=500,
            screen_width=1920,
            window_left=100,
            window_top=100
        )
        assert rel_x == 960  # 1060 - 100
        assert rel_y == 400  # 500 - 100
    
    def test_legacy_positive_coords(self):
        """Test that positive coords still work."""
        rel_x, rel_y = convert_legacy_coords(
            legacy_left=500,
            legacy_top=300,
            screen_width=1920,
            window_left=100,
            window_top=50
        )
        assert rel_x == 400
        assert rel_y == 250


class TestCalibrationPersistence:
    """Tests for saving/loading calibration files."""
    
    def test_save_and_load_calibration(self):
        """Test round-trip save and load."""
        config = TableConfig(
            hero_seat_index=4,
            hero_card1_number=Region(100, 200, 30, 40),
            hero_card1_suit=Region(100, 250, 20, 25),
            hero_card2_number=Region(140, 200, 30, 40),
            hero_card2_suit=Region(140, 250, 20, 25),
            dealer_pixels=[
                PixelCoord(50, 50),
                PixelCoord(100, 50),
            ],
            active_player_pixels=[
                PixelCheck(60, 60, 40),
                PixelCheck(110, 60, 42),
            ],
            pot_region=Region(400, 300, 130, 35),
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "calibration.json"
            
            # Save
            result = save_calibration(config, path)
            assert result is True
            assert path.exists()
            
            # Load
            loaded = load_calibration(path)
            assert loaded is not None
            assert loaded.hero_seat_index == config.hero_seat_index
            assert loaded.hero_card1_number.left == config.hero_card1_number.left
            assert loaded.hero_card1_number.top == config.hero_card1_number.top
            assert len(loaded.dealer_pixels) == len(config.dealer_pixels)
    
    def test_load_missing_file(self):
        """Test loading non-existent file returns None."""
        loaded = load_calibration(Path("/nonexistent/path.json"))
        assert loaded is None
    
    def test_save_creates_directory(self):
        """Test that save creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "nested" / "calibration.json"
            
            config = TableConfig()
            result = save_calibration(config, path)
            
            assert result is True
            assert path.exists()
