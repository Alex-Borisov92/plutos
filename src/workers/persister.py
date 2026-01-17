"""
Database persistence worker.
Handles async writes of observations, events, and decisions to SQLite.
"""
from datetime import datetime
from typing import Optional
import logging
import queue
import threading

from ..poker.models import Observation, PreflopDecision, HeroTurnEvent
from ..storage.db import Database


logger = logging.getLogger(__name__)


class PersistenceWorker:
    """
    Background worker for persisting data to database.
    Uses a queue to batch writes and avoid blocking the main thread.
    """
    
    def __init__(self, db: Database, session_id: Optional[int] = None):
        """
        Initialize persistence worker.
        
        Args:
            db: Database connection
            session_id: Current session ID (created if not provided)
        """
        self.db = db
        self.session_id = session_id
        
        self._queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def _process_item(self, item: dict):
        """
        Process a single queue item.
        
        Args:
            item: Dict with 'type' and 'data' keys
        """
        item_type = item.get("type")
        data = item.get("data")
        
        try:
            if item_type == "observation":
                self._save_observation(data)
            elif item_type == "event":
                self._save_event(data)
            elif item_type == "decision":
                self._save_decision(data)
            else:
                logger.warning(f"Unknown item type: {item_type}")
        except Exception as e:
            logger.error(f"Error persisting {item_type}: {e}")
    
    def _save_observation(self, observation: Observation):
        """Save observation to database."""
        self.db.insert_observation(
            session_id=self.session_id,
            window_id=observation.window_id,
            timestamp=observation.timestamp,
            stage=observation.stage.value,
            dealer_seat=observation.dealer_seat,
            hero_position=observation.hero_position.value,
            active_players_count=observation.active_players_count,
            active_positions_json=str([p.value for p in observation.active_positions]),
            hero_cards_json=str(observation.hero_cards) if observation.hero_cards else None,
            board_cards_json=str(observation.board_cards.to_list()),
            pot_bb=observation.pot_bb,
            raw_confidence_json=str(observation.confidence) if observation.confidence else None
        )
    
    def _save_event(self, event: HeroTurnEvent):
        """Save event to database."""
        self.db.insert_event(
            session_id=self.session_id,
            window_id=event.window_id,
            timestamp=event.timestamp,
            event_type="HERO_TURN",
            payload_json=event.observation.to_json()
        )
    
    def _save_decision(self, data: dict):
        """Save decision to database."""
        observation = data.get("observation")
        decision = data.get("decision")
        
        if observation and decision:
            self.db.insert_decision(
                session_id=self.session_id,
                window_id=observation.window_id,
                timestamp=datetime.now(),
                stage=observation.stage.value,
                hero_position=observation.hero_position.value,
                recommended_action=decision.action.value,
                source=decision.source,
                confidence=decision.confidence
            )
    
    def _worker_loop(self):
        """Main worker loop."""
        logger.info("Persistence worker started")
        
        while self._running:
            try:
                # Get item with timeout to allow checking _running flag
                item = self._queue.get(timeout=0.5)
                self._process_item(item)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
        
        # Process remaining items before stopping
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                self._process_item(item)
                self._queue.task_done()
            except queue.Empty:
                break
        
        logger.info("Persistence worker stopped")
    
    def start(self):
        """Start the worker thread."""
        if self._running:
            return
        
        # Create session if needed
        if self.session_id is None:
            self.session_id = self.db.create_session()
            logger.info(f"Created session: {self.session_id}")
        
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the worker thread."""
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
    
    def queue_observation(self, observation: Observation):
        """Queue an observation for persistence."""
        self._queue.put({"type": "observation", "data": observation})
    
    def queue_event(self, event: HeroTurnEvent):
        """Queue an event for persistence."""
        self._queue.put({"type": "event", "data": event})
    
    def queue_decision(self, observation: Observation, decision: PreflopDecision):
        """Queue a decision for persistence."""
        self._queue.put({
            "type": "decision",
            "data": {"observation": observation, "decision": decision}
        })
    
    @property
    def pending_count(self) -> int:
        """Get count of pending items in queue."""
        return self._queue.qsize()
