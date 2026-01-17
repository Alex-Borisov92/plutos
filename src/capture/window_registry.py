"""
Window registry for multi-table support.
Tracks multiple poker windows with their configurations and states.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import logging
import json

from .window_manager import WindowInfo, WindowManager
from .calibration import load_calibration, save_calibration
from ..app.config import TableConfig, DATA_DIR


logger = logging.getLogger(__name__)


@dataclass
class TableWindow:
    """
    A tracked poker table window with its configuration.
    """
    window_id: str
    info: WindowInfo
    config: TableConfig
    calibration_path: Optional[Path] = None
    is_active: bool = True
    error_count: int = 0
    last_error: Optional[str] = None
    
    def get_screen_offset(self):
        """Get screen offset for capture operations."""
        return self.info.get_screen_offset()
    
    def mark_error(self, error: str):
        """Record an error for this window."""
        self.error_count += 1
        self.last_error = error
        logger.warning(f"[{self.window_id}] Error #{self.error_count}: {error}")
    
    def clear_errors(self):
        """Clear error state."""
        self.error_count = 0
        self.last_error = None


class WindowRegistry:
    """
    Registry for tracking multiple poker table windows.
    
    Features:
    - Track up to N windows simultaneously
    - Per-window configuration/calibration
    - Window state management
    - Auto-discovery of new windows
    """
    
    def __init__(
        self,
        max_windows: int = 4,
        title_pattern: str = "",
        default_config: Optional[TableConfig] = None,
        calibrations_dir: Optional[Path] = None
    ):
        """
        Initialize window registry.
        
        Args:
            max_windows: Maximum number of windows to track
            title_pattern: Regex pattern to match poker window titles
            default_config: Default TableConfig for new windows
            calibrations_dir: Directory for storing window calibrations
        """
        self.max_windows = max_windows
        self.title_pattern = title_pattern
        self.default_config = default_config or TableConfig()
        self.calibrations_dir = calibrations_dir or (DATA_DIR / "calibrations")
        
        self._manager = WindowManager(max_windows, title_pattern)
        self._windows: Dict[str, TableWindow] = {}
        self._window_counter = 0
    
    def discover_windows(self) -> List[TableWindow]:
        """
        Discover and register new poker windows.
        
        Returns:
            List of newly registered TableWindow objects
        """
        newly_registered = []
        
        found = self._manager.find_windows(self.title_pattern)
        
        for info in found:
            if len(self._windows) >= self.max_windows:
                break
            
            # Check if already registered
            if any(w.info.hwnd == info.hwnd for w in self._windows.values()):
                continue
            
            # Generate window ID
            self._window_counter += 1
            window_id = f"table_{self._window_counter}"
            
            # Try to load existing calibration
            config = self._load_window_calibration(info.hwnd) or self.default_config
            
            # Create table window
            table_window = TableWindow(
                window_id=window_id,
                info=info,
                config=config,
                calibration_path=self.calibrations_dir / f"{info.hwnd}.json",
            )
            
            self._windows[window_id] = table_window
            newly_registered.append(table_window)
            
            logger.info(
                f"Registered window: {window_id} "
                f"(hwnd={info.hwnd}, title='{info.title[:50]}...')"
            )
        
        return newly_registered
    
    def get_window(self, window_id: str) -> Optional[TableWindow]:
        """Get window by ID."""
        return self._windows.get(window_id)
    
    def get_window_by_hwnd(self, hwnd: int) -> Optional[TableWindow]:
        """Get window by handle."""
        for window in self._windows.values():
            if window.info.hwnd == hwnd:
                return window
        return None
    
    def get_all_windows(self) -> List[TableWindow]:
        """Get all registered windows."""
        return list(self._windows.values())
    
    def get_active_windows(self) -> List[TableWindow]:
        """Get all active (visible) windows."""
        return [w for w in self._windows.values() if w.is_active]
    
    def unregister_window(self, window_id: str):
        """Remove a window from the registry."""
        if window_id in self._windows:
            del self._windows[window_id]
            logger.info(f"Unregistered window: {window_id}")
    
    def refresh_all(self) -> int:
        """
        Refresh all window positions and states.
        
        Returns:
            Count of active windows after refresh
        """
        active_count = 0
        
        for window in list(self._windows.values()):
            if self._refresh_window(window):
                active_count += 1
        
        return active_count
    
    def _refresh_window(self, window: TableWindow) -> bool:
        """
        Refresh a single window's info.
        
        Returns:
            True if window is still active
        """
        # Virtual windows (monitors) don't need refresh - always active
        if window.info.hwnd < 0:
            window.is_active = True
            window.clear_errors()
            return True
        
        try:
            found = self._manager.find_windows()
            
            for info in found:
                if info.hwnd == window.info.hwnd:
                    window.info = info
                    window.is_active = True
                    window.clear_errors()
                    return True
            
            # Window not found
            window.is_active = False
            window.mark_error("Window no longer visible")
            return False
            
        except Exception as e:
            window.mark_error(str(e))
            return False
    
    def set_window_config(self, window_id: str, config: TableConfig):
        """
        Set configuration for a window.
        
        Args:
            window_id: Window ID
            config: New TableConfig
        """
        window = self._windows.get(window_id)
        if window:
            window.config = config
            logger.info(f"Updated config for {window_id}")
    
    def save_window_calibration(self, window_id: str) -> bool:
        """
        Save a window's calibration to disk.
        
        Args:
            window_id: Window ID to save
        
        Returns:
            True if saved successfully
        """
        window = self._windows.get(window_id)
        if not window:
            return False
        
        self.calibrations_dir.mkdir(parents=True, exist_ok=True)
        path = self.calibrations_dir / f"{window.info.hwnd}.json"
        
        if save_calibration(window.config, path):
            window.calibration_path = path
            return True
        return False
    
    def _load_window_calibration(self, hwnd: int) -> Optional[TableConfig]:
        """
        Try to load existing calibration for a window.
        
        Args:
            hwnd: Window handle
        
        Returns:
            TableConfig or None
        """
        path = self.calibrations_dir / f"{hwnd}.json"
        return load_calibration(path)
    
    def get_stats(self) -> dict:
        """Get registry statistics."""
        return {
            "total_registered": len(self._windows),
            "active_count": len(self.get_active_windows()),
            "max_windows": self.max_windows,
            "windows": [
                {
                    "id": w.window_id,
                    "hwnd": w.info.hwnd,
                    "title": w.info.title[:40],
                    "active": w.is_active,
                    "errors": w.error_count,
                }
                for w in self._windows.values()
            ]
        }
    
    def cleanup_inactive(self, max_errors: int = 10):
        """
        Remove windows that have too many errors.
        
        Args:
            max_errors: Maximum errors before removal
        """
        to_remove = [
            w.window_id for w in self._windows.values()
            if w.error_count >= max_errors
        ]
        
        for window_id in to_remove:
            self.unregister_window(window_id)


# Module-level singleton
_registry: Optional[WindowRegistry] = None


def get_window_registry(
    max_windows: int = 4,
    title_pattern: str = "",
    default_config: Optional[TableConfig] = None
) -> WindowRegistry:
    """Get or create window registry singleton."""
    global _registry
    if _registry is None:
        _registry = WindowRegistry(max_windows, title_pattern, default_config)
    return _registry
