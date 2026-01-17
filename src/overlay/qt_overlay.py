"""
PyQt5-based overlay window for displaying recommendations.
"""
from typing import Optional
import logging
from queue import Queue, Empty
from threading import Thread

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from ..app.config import OverlayConfig

logger = logging.getLogger(__name__)


class QtOverlayWindow:
    """PyQt5-based overlay window."""
    
    def __init__(self, window_id: str, config: Optional[OverlayConfig] = None):
        self.window_id = window_id
        self.config = config or OverlayConfig()
        
        self._app: Optional[QApplication] = None
        self._window: Optional[QWidget] = None
        self._label: Optional[QLabel] = None
        self._thread: Optional[Thread] = None
        self._running = False
        self._x = 0
        self._y = 0
        
        self._update_queue: Queue = Queue()
        self._text = "PLUTOS\nReady"
    
    def _create_window(self):
        """Create the Qt window."""
        self._app = QApplication([])
        
        self._window = QWidget()
        self._window.setWindowTitle(f"Plutos - {self.window_id}")
        
        # Frameless, always on top, transparent background
        self._window.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self._window.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Set size and position
        self._window.setGeometry(self._x, self._y, self.config.width, self.config.height)
        self._window.setStyleSheet("background-color: #1a1a2e;")
        
        # Create label
        layout = QVBoxLayout()
        self._label = QLabel(self._text)
        self._label.setFont(QFont("Consolas", 14, QFont.Bold))
        self._label.setStyleSheet("color: #FFFF00; padding: 10px;")
        self._label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label)
        
        self._window.setLayout(layout)
        self._window.show()
        
        # Timer for processing queue
        timer = QTimer()
        timer.timeout.connect(self._process_queue)
        timer.start(50)  # 20 Hz
        
        logger.info(f"Qt overlay started at ({self._x}, {self._y})")
        
        self._running = True
        self._app.exec_()
    
    def _process_queue(self):
        """Process pending updates."""
        try:
            while True:
                text = self._update_queue.get_nowait()
                if self._label:
                    self._label.setText(text)
        except Empty:
            pass
    
    def start(self, x: int = 100, y: int = 100):
        """Start overlay in separate thread."""
        if self._running:
            return
        
        self._x = x
        self._y = y
        
        self._thread = Thread(target=self._create_window, daemon=True)
        self._thread.start()
        
        logger.info(f"Started Qt overlay {self.window_id} at ({x}, {y})")
    
    def stop(self):
        """Stop overlay."""
        self._running = False
        if self._app:
            self._app.quit()
        logger.info(f"Stopped overlay {self.window_id}")
    
    def update_text(self, text: str):
        """Update displayed text."""
        self._update_queue.put(text)
    
    def show_debug(self, dealer_seat, active_count: int, is_turn: bool, cards: str = "-"):
        """Display debug state."""
        dealer_text = f"D:{dealer_seat}" if dealer_seat is not None else "D:?"
        turn_text = "TURN!" if is_turn else "wait"
        text = f"{dealer_text} | {turn_text}\nActive: {active_count} | {cards}"
        self.update_text(text)
    
    def show_waiting(self):
        """Display waiting state."""
        self.update_text("PLUTOS\nWaiting...")
    
    def update_position(self, x: int, y: int):
        """Update window position (not supported in thread)."""
        pass
    
    def update_content(self, content):
        """Update from OverlayContent."""
        text = f"{content.action_text}\n{content.position_text}"
        self.update_text(text)
    
    def show_decision(self, observation, decision):
        """Display decision."""
        if decision:
            text = f"{decision}\n{observation.hero_position.value}"
        else:
            text = f"NO DECISION\n{observation.hero_position.value}"
        self.update_text(text)
