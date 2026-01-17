"""
Transparent overlay window for displaying recommendations.
Uses Tkinter with Windows-specific transparency and click-through features.
"""
from dataclasses import dataclass
from typing import Callable, Optional
import logging
import ctypes
import tkinter as tk
from threading import Thread

from ..app.config import OverlayConfig
from ..poker.models import Observation, PreflopDecision, Action


logger = logging.getLogger(__name__)


# Windows constants for transparent click-through windows
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008


def set_click_through(hwnd: int) -> bool:
    """
    Make a window click-through on Windows.
    
    Args:
        hwnd: Window handle
    
    Returns:
        True if successful
    """
    try:
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        return True
    except Exception as e:
        logger.warning(f"Failed to set click-through: {e}")
        return False


@dataclass
class OverlayContent:
    """Content to display in the overlay."""
    action_text: str
    position_text: str
    cards_text: str
    players_text: str
    stage_text: str
    color: str = "#FFFFFF"


class OverlayWindow:
    """
    Transparent overlay window for a single poker table.
    """
    
    def __init__(
        self,
        window_id: str,
        config: Optional[OverlayConfig] = None
    ):
        """
        Initialize overlay window.
        
        Args:
            window_id: Unique identifier for this overlay
            config: Overlay configuration
        """
        self.window_id = window_id
        self.config = config or OverlayConfig()
        
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._thread: Optional[Thread] = None
        self._running = False
        
        # Text item IDs for updating
        self._action_text_id = None
        self._info_text_id = None
        
        # Current position
        self._x = 0
        self._y = 0
    
    def _create_window(self):
        """Create the Tkinter window (must be called from overlay thread)."""
        self._root = tk.Tk()
        self._root.title(f"Plutos - {self.window_id}")
        
        # Remove window decorations
        self._root.overrideredirect(True)
        
        # Set always on top
        self._root.attributes("-topmost", True)
        
        # Set transparency
        self._root.attributes("-alpha", self.config.background_alpha)
        
        # Set transparent color for click-through
        self._root.attributes("-transparentcolor", "")
        
        # Set geometry
        self._root.geometry(
            f"{self.config.width}x{self.config.height}+{self._x}+{self._y}"
        )
        
        # Create canvas with background
        self._canvas = tk.Canvas(
            self._root,
            width=self.config.width,
            height=self.config.height,
            bg=self.config.background_color,
            highlightthickness=2,
            highlightbackground=self.config.accent_color
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create text elements
        self._action_text_id = self._canvas.create_text(
            self.config.width // 2, 35,
            text="WAITING...",
            font=("Consolas", self.config.font_size + 4, "bold"),
            fill=self.config.accent_color,
            anchor=tk.CENTER
        )
        
        self._info_text_id = self._canvas.create_text(
            10, 70,
            text="Position: -\nCards: -\nPlayers: -",
            font=("Consolas", self.config.font_size),
            fill=self.config.text_color,
            anchor=tk.NW,
            justify=tk.LEFT
        )
        
        # Make click-through after window is created
        self._root.update_idletasks()
        try:
            hwnd = self._root.winfo_id()
            set_click_through(hwnd)
        except Exception as e:
            logger.warning(f"Could not set click-through: {e}")
    
    def _run_loop(self):
        """Main loop for the overlay window."""
        self._create_window()
        self._running = True
        
        try:
            while self._running:
                self._root.update()
                self._root.update_idletasks()
        except tk.TclError:
            pass  # Window was destroyed
        except Exception as e:
            logger.error(f"Overlay loop error: {e}")
        finally:
            self._running = False
    
    def start(self, x: int = 100, y: int = 100):
        """
        Start the overlay window in a separate thread.
        
        Args:
            x: Initial X position (screen coordinates)
            y: Initial Y position (screen coordinates)
        """
        if self._running:
            logger.warning(f"Overlay {self.window_id} already running")
            return
        
        self._x = x
        self._y = y
        
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Started overlay {self.window_id} at ({x}, {y})")
    
    def stop(self):
        """Stop the overlay window."""
        self._running = False
        
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except tk.TclError:
                pass
            self._root = None
        
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        
        logger.info(f"Stopped overlay {self.window_id}")
    
    def update_position(self, x: int, y: int):
        """
        Update overlay position on screen.
        
        Args:
            x: New X position
            y: New Y position
        """
        self._x = x
        self._y = y
        
        if self._root and self._running:
            try:
                self._root.geometry(f"+{x}+{y}")
            except tk.TclError:
                pass
    
    def update_content(self, content: OverlayContent):
        """
        Update displayed content.
        
        Args:
            content: New content to display
        """
        if not self._running or not self._canvas:
            return
        
        try:
            # Update action text
            self._canvas.itemconfig(
                self._action_text_id,
                text=content.action_text,
                fill=content.color
            )
            
            # Update info text
            info_text = (
                f"Position: {content.position_text}\n"
                f"Cards: {content.cards_text}\n"
                f"Players: {content.players_text}"
            )
            self._canvas.itemconfig(
                self._info_text_id,
                text=info_text
            )
        except tk.TclError:
            pass
    
    def show_decision(self, observation: Observation, decision: Optional[PreflopDecision]):
        """
        Display observation and decision.
        
        Args:
            observation: Current table state
            decision: Recommended action (or None)
        """
        if decision:
            action_text = str(decision)
            if decision.action == Action.FOLD:
                color = "#888888"  # Gray for fold
            elif decision.action == Action.RAISE:
                color = "#00ff88"  # Green for raise
            else:
                color = "#ffcc00"  # Yellow for call/check
        else:
            action_text = "NO DECISION"
            color = "#ff4444"  # Red for error
        
        cards_text = str(observation.hero_cards) if observation.hero_cards else "-"
        
        content = OverlayContent(
            action_text=f"[{observation.stage.value.upper()}] {action_text}",
            position_text=observation.hero_position.value,
            cards_text=cards_text,
            players_text=str(observation.active_players_count),
            stage_text=observation.stage.value,
            color=color
        )
        
        self.update_content(content)
    
    def show_waiting(self):
        """Display waiting state."""
        content = OverlayContent(
            action_text="WAITING...",
            position_text="-",
            cards_text="-",
            players_text="-",
            stage_text="-",
            color=self.config.accent_color
        )
        self.update_content(content)
    
    def show_error(self, message: str):
        """Display error state."""
        content = OverlayContent(
            action_text=f"ERROR: {message[:20]}",
            position_text="-",
            cards_text="-",
            players_text="-",
            stage_text="-",
            color="#ff4444"
        )
        self.update_content(content)
    
    @property
    def is_running(self) -> bool:
        """Check if overlay is currently running."""
        return self._running


class OverlayManager:
    """
    Manages multiple overlay windows for multi-table support.
    """
    
    def __init__(self, config: Optional[OverlayConfig] = None):
        """
        Initialize overlay manager.
        
        Args:
            config: Default overlay configuration
        """
        self.config = config or OverlayConfig()
        self._overlays: dict[str, OverlayWindow] = {}
    
    def create_overlay(self, window_id: str, x: int = 100, y: int = 100) -> OverlayWindow:
        """
        Create and start a new overlay.
        
        Args:
            window_id: Unique identifier
            x: Initial X position
            y: Initial Y position
        
        Returns:
            Created OverlayWindow
        """
        if window_id in self._overlays:
            logger.warning(f"Overlay {window_id} already exists")
            return self._overlays[window_id]
        
        overlay = OverlayWindow(window_id, self.config)
        overlay.start(x, y)
        self._overlays[window_id] = overlay
        
        return overlay
    
    def get_overlay(self, window_id: str) -> Optional[OverlayWindow]:
        """Get overlay by ID."""
        return self._overlays.get(window_id)
    
    def remove_overlay(self, window_id: str):
        """Stop and remove an overlay."""
        if window_id in self._overlays:
            self._overlays[window_id].stop()
            del self._overlays[window_id]
    
    def stop_all(self):
        """Stop all overlays."""
        for overlay in self._overlays.values():
            overlay.stop()
        self._overlays.clear()
    
    def get_all(self) -> list[OverlayWindow]:
        """Get all overlays."""
        return list(self._overlays.values())
