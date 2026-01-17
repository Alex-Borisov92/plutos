"""
Window manager for finding and tracking poker table windows.
Supports multi-table setups with up to N concurrent windows.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import ctypes
from ctypes import wintypes
import logging
import re


logger = logging.getLogger(__name__)


# Windows API types and constants
user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible
GetWindowRect = user32.GetWindowRect
GetClientRect = user32.GetClientRect
ClientToScreen = user32.ClientToScreen


@dataclass
class WindowInfo:
    """Information about a poker window."""
    hwnd: int
    title: str
    rect: Tuple[int, int, int, int]  # left, top, right, bottom (screen coords)
    client_offset: Tuple[int, int]   # client area offset from window origin
    client_size: Tuple[int, int]     # client area width, height
    
    @property
    def left(self) -> int:
        return self.rect[0]
    
    @property
    def top(self) -> int:
        return self.rect[1]
    
    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]
    
    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]
    
    @property
    def client_left(self) -> int:
        """X coordinate of client area top-left in screen coords."""
        return self.rect[0] + self.client_offset[0]
    
    @property
    def client_top(self) -> int:
        """Y coordinate of client area top-left in screen coords."""
        return self.rect[1] + self.client_offset[1]
    
    def get_screen_offset(self) -> Tuple[int, int]:
        """Get offset to convert window-relative coords to screen coords."""
        return (self.client_left, self.client_top)


@dataclass
class RegisteredWindow:
    """A window registered for tracking."""
    window_id: str
    info: WindowInfo
    table_index: int
    is_active: bool = True
    last_update_ms: int = 0
    config_overrides: dict = field(default_factory=dict)


class WindowManager:
    """
    Manages poker window discovery and tracking.
    
    Supports:
    - Finding windows by title pattern
    - Tracking multiple windows with unique IDs
    - Getting window positions for screen capture
    """
    
    def __init__(self, max_windows: int = 4, title_pattern: str = ""):
        """
        Initialize window manager.
        
        Args:
            max_windows: Maximum number of windows to track
            title_pattern: Regex pattern to match window titles
        """
        self.max_windows = max_windows
        self.title_pattern = title_pattern
        self._registry: Dict[str, RegisteredWindow] = {}
        self._next_table_index = 0
    
    def find_windows(self, pattern: Optional[str] = None) -> List[WindowInfo]:
        """
        Find all visible windows matching the title pattern.
        
        Args:
            pattern: Override title pattern (uses default if not provided)
        
        Returns:
            List of WindowInfo for matching windows
        """
        search_pattern = pattern or self.title_pattern
        found_windows = []
        
        def enum_callback(hwnd: int, lparam: int) -> bool:
            if not IsWindowVisible(hwnd):
                return True
            
            # Get window title
            length = GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            
            buffer = ctypes.create_unicode_buffer(length + 1)
            GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            
            # Check pattern match
            if search_pattern and not re.search(search_pattern, title, re.IGNORECASE):
                return True
            
            # Get window rect
            rect = wintypes.RECT()
            if not GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            
            # Get client rect and offset
            client_rect = wintypes.RECT()
            GetClientRect(hwnd, ctypes.byref(client_rect))
            
            # Calculate client area offset (title bar, borders)
            point = wintypes.POINT(0, 0)
            ClientToScreen(hwnd, ctypes.byref(point))
            client_offset = (point.x - rect.left, point.y - rect.top)
            
            window_info = WindowInfo(
                hwnd=hwnd,
                title=title,
                rect=(rect.left, rect.top, rect.right, rect.bottom),
                client_offset=client_offset,
                client_size=(client_rect.right, client_rect.bottom),
            )
            found_windows.append(window_info)
            
            return True
        
        EnumWindows(EnumWindowsProc(enum_callback), 0)
        return found_windows
    
    def register_window(
        self,
        info: WindowInfo,
        window_id: Optional[str] = None
    ) -> Optional[RegisteredWindow]:
        """
        Register a window for tracking.
        
        Args:
            info: Window information
            window_id: Optional custom ID (auto-generated if not provided)
        
        Returns:
            RegisteredWindow or None if max windows reached
        """
        if len(self._registry) >= self.max_windows:
            logger.warning(f"Max windows ({self.max_windows}) reached, cannot register")
            return None
        
        # Generate ID if not provided
        if window_id is None:
            window_id = f"table_{self._next_table_index}"
        
        # Check if already registered by hwnd
        for reg in self._registry.values():
            if reg.info.hwnd == info.hwnd:
                logger.debug(f"Window {info.hwnd} already registered as {reg.window_id}")
                reg.info = info  # Update info
                return reg
        
        registered = RegisteredWindow(
            window_id=window_id,
            info=info,
            table_index=self._next_table_index,
            is_active=True,
        )
        
        self._registry[window_id] = registered
        self._next_table_index += 1
        
        logger.info(f"Registered window: {window_id} (hwnd={info.hwnd}, title='{info.title}')")
        return registered
    
    def unregister_window(self, window_id: str) -> bool:
        """
        Unregister a window.
        
        Args:
            window_id: ID of window to unregister
        
        Returns:
            True if window was unregistered
        """
        if window_id in self._registry:
            del self._registry[window_id]
            logger.info(f"Unregistered window: {window_id}")
            return True
        return False
    
    def get_window(self, window_id: str) -> Optional[RegisteredWindow]:
        """Get registered window by ID."""
        return self._registry.get(window_id)
    
    def get_all_windows(self) -> List[RegisteredWindow]:
        """Get all registered windows."""
        return list(self._registry.values())
    
    def get_active_windows(self) -> List[RegisteredWindow]:
        """Get all active registered windows."""
        return [w for w in self._registry.values() if w.is_active]
    
    def refresh_window_info(self, window_id: str) -> bool:
        """
        Refresh window info (position, size) for a registered window.
        
        Args:
            window_id: Window ID to refresh
        
        Returns:
            True if window still exists and was updated
        """
        reg = self._registry.get(window_id)
        if reg is None:
            return False
        
        hwnd = reg.info.hwnd
        
        # Check if window still exists
        if not IsWindowVisible(hwnd):
            reg.is_active = False
            logger.warning(f"Window {window_id} no longer visible")
            return False
        
        # Get updated rect
        rect = wintypes.RECT()
        if not GetWindowRect(hwnd, ctypes.byref(rect)):
            reg.is_active = False
            return False
        
        # Get updated client rect
        client_rect = wintypes.RECT()
        GetClientRect(hwnd, ctypes.byref(client_rect))
        
        point = wintypes.POINT(0, 0)
        ClientToScreen(hwnd, ctypes.byref(point))
        client_offset = (point.x - rect.left, point.y - rect.top)
        
        # Update info
        reg.info = WindowInfo(
            hwnd=hwnd,
            title=reg.info.title,
            rect=(rect.left, rect.top, rect.right, rect.bottom),
            client_offset=client_offset,
            client_size=(client_rect.right, client_rect.bottom),
        )
        reg.is_active = True
        
        return True
    
    def refresh_all(self) -> int:
        """
        Refresh all registered windows.
        
        Returns:
            Count of windows that are still active
        """
        active_count = 0
        for window_id in list(self._registry.keys()):
            if self.refresh_window_info(window_id):
                active_count += 1
        return active_count
    
    def auto_discover(self, pattern: Optional[str] = None) -> List[RegisteredWindow]:
        """
        Find and register new windows matching pattern.
        
        Args:
            pattern: Override title pattern
        
        Returns:
            List of newly registered windows
        """
        windows = self.find_windows(pattern)
        newly_registered = []
        
        for info in windows:
            if len(self._registry) >= self.max_windows:
                break
            
            # Check if already registered
            already_registered = any(
                r.info.hwnd == info.hwnd
                for r in self._registry.values()
            )
            
            if not already_registered:
                reg = self.register_window(info)
                if reg:
                    newly_registered.append(reg)
        
        return newly_registered


    def register_monitor(self, monitor_index: int = 0) -> Optional[RegisteredWindow]:
        """
        Register a full monitor as a virtual window.
        Useful for browser-based poker clients.
        
        Args:
            monitor_index: Monitor index (0 = primary, 1 = secondary, etc.)
        
        Returns:
            RegisteredWindow for the monitor
        """
        try:
            import mss
            with mss.mss() as sct:
                # mss.monitors[0] is "all monitors", [1] is primary, [2] is secondary...
                if monitor_index + 1 >= len(sct.monitors):
                    logger.error(f"Monitor {monitor_index} not found. Available: {len(sct.monitors) - 1}")
                    return None
                
                mon = sct.monitors[monitor_index + 1]
                
                # Create virtual WindowInfo
                info = WindowInfo(
                    hwnd=-1,  # Virtual window
                    title=f"Monitor_{monitor_index}",
                    rect=(mon["left"], mon["top"], 
                          mon["left"] + mon["width"], 
                          mon["top"] + mon["height"]),
                    client_offset=(0, 0),  # No borders for full screen
                    client_size=(mon["width"], mon["height"]),
                )
                
                window_id = f"monitor_{monitor_index}"
                
                # Check if already registered
                if window_id in self._registry:
                    self._registry[window_id].info = info
                    return self._registry[window_id]
                
                registered = RegisteredWindow(
                    window_id=window_id,
                    info=info,
                    table_index=self._next_table_index,
                    is_active=True,
                )
                
                self._registry[window_id] = registered
                self._next_table_index += 1
                
                logger.info(f"Registered monitor {monitor_index}: {mon['width']}x{mon['height']} at ({mon['left']}, {mon['top']})")
                return registered
                
        except Exception as e:
            logger.error(f"Failed to register monitor: {e}")
            return None


# Module-level singleton
_window_manager: Optional[WindowManager] = None


def get_window_manager(
    max_windows: int = 4,
    title_pattern: str = ""
) -> WindowManager:
    """Get or create window manager singleton."""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager(max_windows, title_pattern)
    return _window_manager
