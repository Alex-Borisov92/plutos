"""
Plutos - Poker Analysis Helper
Main application entrypoint.
"""
import argparse
import logging
import signal
import sys
import time
from typing import Optional

from .config import get_config, setup_logging, AppConfig
from ..capture.window_manager import WindowManager, get_window_manager
from ..capture.window_registry import WindowRegistry, get_window_registry, TableWindow
from ..overlay.overlay_window import OverlayManager, OverlayWindow
from ..poker.models import Observation, HeroTurnEvent
from ..poker.preflop_engine import create_engine, PreflopEngine
from ..storage.db import get_database, Database
from ..workers.persister import PersistenceWorker
from ..workers.poller import StatePoller


logger = logging.getLogger(__name__)


class PlutosApp:
    """
    Main application class.
    Coordinates all components: window tracking, polling, overlay, persistence.
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the application.
        
        Args:
            config: Application configuration
        """
        self.config = config or get_config()
        setup_logging(self.config)
        
        # Components (initialized in start())
        self._window_registry: Optional[WindowRegistry] = None
        self._window_manager: Optional[WindowManager] = None
        self._overlay_manager: Optional[OverlayManager] = None
        self._poller: Optional[StatePoller] = None
        self._persister: Optional[PersistenceWorker] = None
        self._engine: Optional[PreflopEngine] = None
        self._db: Optional[Database] = None
        
        self._running = False
        self._session_id: Optional[int] = None
        
        # Per-window pollers for multi-table support
        self._window_pollers: dict = {}
    
    def _on_hero_turn(self, event: HeroTurnEvent):
        """
        Handle hero turn event.
        
        Args:
            event: Hero turn event with observation
        """
        observation = event.observation
        
        logger.info(
            f"[{event.window_id}] HERO TURN - "
            f"Position: {observation.hero_position.value}, "
            f"Cards: {observation.hero_cards}, "
            f"Players: {observation.active_players_count}"
        )
        
        # Get decision from engine
        decision = self._engine.get_decision(observation)
        
        if decision:
            logger.info(
                f"[{event.window_id}] DECISION: {decision} "
                f"({decision.reasoning})"
            )
        
        # Update overlay
        overlay = self._overlay_manager.get_overlay(event.window_id)
        if overlay:
            overlay.show_decision(observation, decision)
        
        # Persist event and decision
        if self._persister:
            self._persister.queue_event(event)
            if decision:
                self._persister.queue_decision(observation, decision)
    
    def _on_observation(self, observation: Observation):
        """
        Handle observation (optional logging/persistence).
        
        Args:
            observation: Table state observation
        """
        # Only persist periodically to avoid database spam
        # (hero turn events are always persisted)
        pass
    
    def _setup_windows(self):
        """Discover and setup poker windows."""
        logger.info("Discovering poker windows...")
        
        # Initialize window registry
        self._window_registry = get_window_registry(
            max_windows=self.config.max_tables,
            title_pattern=self.config.window_title_pattern,
            default_config=self.config.default_table
        )
        
        # Also keep window manager for backward compatibility
        self._window_manager = get_window_manager(
            max_windows=self.config.max_tables,
            title_pattern=self.config.window_title_pattern
        )
        
        # Discover windows
        discovered = self._window_registry.discover_windows()
        
        if not discovered:
            logger.warning("No poker windows found. Waiting for windows...")
        else:
            logger.info(f"Found {len(discovered)} poker window(s)")
            
            # Setup each window
            for table_window in discovered:
                self._setup_single_window(table_window)
    
    def _setup_single_window(self, table_window: TableWindow):
        """
        Setup a single table window with overlay and DB registration.
        
        Args:
            table_window: TableWindow to setup
        """
        # Calculate overlay position
        x = table_window.info.client_left + self.config.overlay.offset_x
        y = table_window.info.client_top + self.config.overlay.offset_y
        
        # Create overlay
        overlay = self._overlay_manager.create_overlay(
            table_window.window_id, x, y
        )
        overlay.show_waiting()
        
        # Register in database
        if self._db and self._session_id:
            self._db.register_window(
                session_id=self._session_id,
                window_id=table_window.window_id,
                title=table_window.info.title,
                hwnd=table_window.info.hwnd
            )
        
        logger.info(
            f"Setup window {table_window.window_id} at "
            f"({table_window.info.client_left}, {table_window.info.client_top})"
        )
    
    def start(self):
        """Start the application."""
        if self._running:
            logger.warning("Application already running")
            return
        
        logger.info("Starting Plutos Poker Helper...")
        
        # Initialize database
        self._db = get_database(self.config.db_path)
        self._session_id = self._db.create_session()
        
        # Initialize components
        self._overlay_manager = OverlayManager(self.config.overlay)
        self._engine = create_engine("placeholder")
        
        # Setup persistence worker
        self._persister = PersistenceWorker(self._db, self._session_id)
        self._persister.start()
        
        # Setup windows
        self._setup_windows()
        
        # Setup poller with window registry for multi-table support
        self._poller = StatePoller(
            window_manager=self._window_manager,
            window_registry=self._window_registry,
            config=self.config.poller,
            table_config=self.config.default_table,
            on_hero_turn=self._on_hero_turn,
            on_observation=self._on_observation
        )
        self._poller.start()
        
        self._running = True
        logger.info("Plutos started successfully")
    
    def stop(self):
        """Stop the application."""
        if not self._running:
            return
        
        logger.info("Stopping Plutos...")
        
        # Stop components in reverse order
        if self._poller:
            self._poller.stop()
        
        if self._overlay_manager:
            self._overlay_manager.stop_all()
        
        if self._persister:
            self._persister.stop()
        
        if self._db and self._session_id:
            self._db.end_session(self._session_id)
            self._db.close()
        
        self._running = False
        logger.info("Plutos stopped")
    
    def run(self):
        """Run the application main loop."""
        self.start()
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Running... Press Ctrl+C to stop")
        
        try:
            while self._running:
                # Periodic tasks
                if self._window_registry:
                    self._window_registry.refresh_all()
                    
                    # Check for new windows
                    newly_discovered = self._window_registry.discover_windows()
                    for table_window in newly_discovered:
                        self._setup_single_window(table_window)
                    
                    # Update overlay positions
                    for table_window in self._window_registry.get_active_windows():
                        overlay = self._overlay_manager.get_overlay(table_window.window_id)
                        if overlay:
                            x = table_window.info.client_left + self.config.overlay.offset_x
                            y = table_window.info.client_top + self.config.overlay.offset_y
                            overlay.update_position(x, y)
                    
                    # Cleanup windows with too many errors
                    self._window_registry.cleanup_inactive(max_errors=10)
                
                time.sleep(1.0)  # Main loop runs at 1 Hz
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Plutos - Poker Analysis Helper"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--window-pattern", "-w",
        type=str,
        default="",
        help="Window title pattern to match"
    )
    parser.add_argument(
        "--max-tables", "-t",
        type=int,
        default=4,
        help="Maximum number of tables to track"
    )
    
    args = parser.parse_args()
    
    # Create config with CLI overrides
    config = get_config()
    config.verbose_logging = args.debug
    
    if args.window_pattern:
        config.window_title_pattern = args.window_pattern
    
    config.max_tables = args.max_tables
    
    # Run application
    app = PlutosApp(config)
    app.run()


if __name__ == "__main__":
    main()
