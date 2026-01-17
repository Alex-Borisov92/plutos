"""
Screen capture module using MSS library.
Provides window-relative capture for multi-monitor and multi-window support.
"""
from typing import Optional, Tuple
import logging

import mss
import numpy as np
from PIL import Image

from ..app.config import Region


logger = logging.getLogger(__name__)


class ScreenCapture:
    """
    Screen capture utility using MSS.
    Thread-safe - each instance maintains its own mss context.
    """
    
    def __init__(self):
        self._sct = None
    
    def _get_sct(self) -> mss.mss:
        """Get or create mss instance."""
        if self._sct is None:
            self._sct = mss.mss()
        return self._sct
    
    def capture_region(
        self,
        region: Region,
        window_offset: Tuple[int, int] = (0, 0)
    ) -> Optional[Image.Image]:
        """
        Capture a screen region and return as PIL Image.
        
        Args:
            region: Region to capture (relative coordinates)
            window_offset: (x, y) offset to add for window-relative capture
        
        Returns:
            PIL Image or None if capture failed
        """
        abs_left = region.left + window_offset[0]
        abs_top = region.top + window_offset[1]
        
        monitor = {
            "left": abs_left,
            "top": abs_top,
            "width": region.width,
            "height": region.height,
        }
        
        try:
            sct = self._get_sct()
            sct_img = sct.grab(monitor)
            return Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        except mss.exception.ScreenShotError as e:
            logger.error(f"Screen capture failed at ({abs_left}, {abs_top}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected capture error: {e}")
            return None
    
    def capture_pixel(
        self,
        x: int,
        y: int,
        window_offset: Tuple[int, int] = (0, 0)
    ) -> Optional[Tuple[int, int, int]]:
        """
        Capture a single pixel color.
        
        Args:
            x: X coordinate (relative to window if offset provided)
            y: Y coordinate (relative to window if offset provided)
            window_offset: (x, y) offset to add for window-relative capture
        
        Returns:
            (R, G, B) tuple or None if capture failed
        """
        abs_x = x + window_offset[0]
        abs_y = y + window_offset[1]
        
        monitor = {
            "left": abs_x,
            "top": abs_y,
            "width": 1,
            "height": 1,
        }
        
        try:
            sct = self._get_sct()
            sct_img = sct.grab(monitor)
            pixel = np.array(sct_img)[0, 0]
            # MSS returns BGRA, convert to RGB
            return (int(pixel[2]), int(pixel[1]), int(pixel[0]))
        except mss.exception.ScreenShotError as e:
            logger.debug(f"Pixel capture failed at ({abs_x}, {abs_y}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected pixel capture error: {e}")
            return None
    
    def capture_multiple_pixels(
        self,
        coords: list,
        window_offset: Tuple[int, int] = (0, 0)
    ) -> dict:
        """
        Capture multiple pixels efficiently.
        
        Args:
            coords: List of (x, y) tuples (relative coordinates)
            window_offset: Window offset to add
        
        Returns:
            Dict mapping (x, y) to (R, G, B) or None
        """
        results = {}
        for x, y in coords:
            results[(x, y)] = self.capture_pixel(x, y, window_offset)
        return results
    
    def close(self):
        """Release resources."""
        if self._sct is not None:
            self._sct.close()
            self._sct = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# Module-level convenience instance
_default_capture: Optional[ScreenCapture] = None


def get_capture() -> ScreenCapture:
    """Get default screen capture instance."""
    global _default_capture
    if _default_capture is None:
        _default_capture = ScreenCapture()
    return _default_capture


def capture_region(
    region: Region,
    window_offset: Tuple[int, int] = (0, 0)
) -> Optional[Image.Image]:
    """Convenience function to capture a region."""
    return get_capture().capture_region(region, window_offset)


def capture_pixel(
    x: int,
    y: int,
    window_offset: Tuple[int, int] = (0, 0)
) -> Optional[Tuple[int, int, int]]:
    """Convenience function to capture a single pixel."""
    return get_capture().capture_pixel(x, y, window_offset)
