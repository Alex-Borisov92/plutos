"""
PyQt5-based overlay window for displaying recommendations.
"""
from typing import Optional, Callable
import logging
from queue import Queue, Empty
from threading import Thread

from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, 
    QComboBox, QPushButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from ..app.config import OverlayConfig

logger = logging.getLogger(__name__)


class QtOverlayWindow:
    """PyQt5-based overlay window."""
    
    def __init__(self, window_id: str, config: Optional[OverlayConfig] = None,
                 on_cards_override: Optional[Callable[[str, str], None]] = None,
                 on_action_override: Optional[Callable[[str, str], None]] = None):
        """
        Args:
            window_id: Window identifier
            config: Overlay configuration
            on_cards_override: Callback(window_id, cards_str) when user manually enters cards
            on_action_override: Callback(window_id, action) when user clicks FOLD/RAISE
        """
        self.window_id = window_id
        self.config = config or OverlayConfig()
        self._on_cards_override = on_cards_override
        self._on_action_override = on_action_override
        
        self._app: Optional[QApplication] = None
        self._window: Optional[QWidget] = None
        self._label: Optional[QLabel] = None
        self._rank1_combo: Optional[QComboBox] = None
        self._suit1_combo: Optional[QComboBox] = None
        self._rank2_combo: Optional[QComboBox] = None
        self._suit2_combo: Optional[QComboBox] = None
        self._thread: Optional[Thread] = None
        self._running = False
        self._x = 0
        self._y = 0
        
        self._update_queue: Queue = Queue()
        self._text = "PLUTOS\nReady"
        
        # Card options with Unicode suit symbols
        self._ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        # Symbol, internal code, color
        self._suits = [
            ('\u2660', 's', '#333333'),  # Spades - black
            ('\u2665', 'h', '#FF3333'),  # Hearts - red
            ('\u2666', 'd', '#3366FF'),  # Diamonds - blue
            ('\u2663', 'c', '#33AA33'),  # Clubs - green
        ]
    
    def _create_window(self):
        """Create the Qt window."""
        self._app = QApplication([])
        
        self._window = QWidget()
        self._window.setWindowTitle(f"Plutos - {self.window_id}")
        
        # Frameless, always on top
        self._window.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self._window.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Set size and position (extra height for card selectors)
        controls_height = 30
        self._window.setGeometry(self._x, self._y, self.config.width + 20, self.config.height + controls_height)
        self._window.setStyleSheet("background-color: #1a1a2e;")
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Status label
        self._label = QLabel(self._text)
        self._label.setFont(QFont("Consolas", 11, QFont.Bold))
        self._label.setStyleSheet("color: #FFFF00;")
        self._label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label)
        
        # Card selection row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(2)
        
        combo_style = """
            QComboBox {
                background-color: #2a2a4e;
                color: #00FF00;
                border: 1px solid #4a4a6e;
                padding: 2px;
                min-width: 35px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2a2a4e;
                color: #00FF00;
                selection-background-color: #4a4a6e;
            }
        """
        
        # Card 1: Rank + Suit
        self._rank1_combo = QComboBox()
        self._rank1_combo.addItems(self._ranks)
        self._rank1_combo.setStyleSheet(combo_style)
        self._rank1_combo.setFont(QFont("Consolas", 9))
        cards_layout.addWidget(self._rank1_combo)
        
        self._suit1_combo = QComboBox()
        for symbol, code, color in self._suits:
            self._suit1_combo.addItem(symbol)
        self._suit1_combo.setStyleSheet(combo_style)
        self._suit1_combo.setFont(QFont("Segoe UI Symbol", 12))
        cards_layout.addWidget(self._suit1_combo)
        
        # Card 2: Rank + Suit
        self._rank2_combo = QComboBox()
        self._rank2_combo.addItems(self._ranks)
        self._rank2_combo.setStyleSheet(combo_style)
        self._rank2_combo.setFont(QFont("Consolas", 9))
        cards_layout.addWidget(self._rank2_combo)
        
        self._suit2_combo = QComboBox()
        for symbol, code, color in self._suits:
            self._suit2_combo.addItem(symbol)
        self._suit2_combo.setStyleSheet(combo_style)
        self._suit2_combo.setFont(QFont("Segoe UI Symbol", 12))
        cards_layout.addWidget(self._suit2_combo)
        
        # Apply button
        apply_btn = QPushButton("OK")
        apply_btn.setStyleSheet(
            "background-color: #3a3a5e; color: #FFFFFF; "
            "border: 1px solid #5a5a7e; padding: 2px 8px;"
        )
        apply_btn.setFont(QFont("Consolas", 9))
        apply_btn.clicked.connect(self._on_cards_apply)
        cards_layout.addWidget(apply_btn)
        
        layout.addLayout(cards_layout)
        
        self._window.setLayout(layout)
        self._window.show()
        
        # Timer for processing queue
        timer = QTimer()
        timer.timeout.connect(self._process_queue)
        timer.start(50)  # 20 Hz
        
        logger.info(f"Qt overlay started at ({self._x}, {self._y})")
        
        self._running = True
        self._app.exec_()
    
    def _on_cards_apply(self):
        """Handle card selection apply."""
        if not all([self._rank1_combo, self._suit1_combo, self._rank2_combo, self._suit2_combo]):
            return
        
        rank1 = self._rank1_combo.currentText()
        suit1_idx = self._suit1_combo.currentIndex()
        rank2 = self._rank2_combo.currentText()
        suit2_idx = self._suit2_combo.currentIndex()
        
        # Get suit code from index
        suit1 = self._suits[suit1_idx][1]  # 's', 'h', 'd', or 'c'
        suit2 = self._suits[suit2_idx][1]
        
        cards_str = f"{rank1}{suit1}{rank2}{suit2}"
        logger.info(f"[{self.window_id}] Manual cards override: {cards_str}")
        
        if self._on_cards_override:
            self._on_cards_override(self.window_id, cards_str)
    
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
    
    def show_debug(self, dealer_seat, active_count: int, is_turn: bool, 
                    hero_position=None, active_positions=None, 
                    decision: str = None, cards: str = None, stack_bb: float = None):
        """Display debug state with position info, decision, and stack."""
        pos_text = hero_position.value if hero_position else "?"
        cards_text = cards if cards else "-"
        stack_text = f"{stack_bb:.1f}BB" if stack_bb else "-"
        
        # Always show decision if available, otherwise show turn indicator
        if decision:
            action_text = decision.upper()
        else:
            action_text = "..." if not is_turn else "?"
        
        # Convert positions to short names
        if active_positions:
            pos_names = [p.value for p in active_positions]
            positions_text = " ".join(pos_names)
        else:
            positions_text = "-"
        
        text = f"{pos_text} | {active_count}p | {stack_text}\n{cards_text} | {action_text}\n{positions_text}"
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
