"""
SQLite database helper.
Provides simple interface for reading/writing poker data.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging
import sqlite3
import threading

from ..app.config import DATA_DIR


logger = logging.getLogger(__name__)

# Current schema version for future migrations
SCHEMA_VERSION = 1

# Path to schema file
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    """
    SQLite database connection and operations.
    Thread-safe with connection per thread.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database.
        
        Args:
            db_path: Path to SQLite file (creates default if not provided)
        """
        self.db_path = db_path or (DATA_DIR / "plutos.db")
        self._local = threading.local()
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize schema
        self._init_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_schema(self):
        """Initialize database schema."""
        if not SCHEMA_PATH.exists():
            logger.warning(f"Schema file not found: {SCHEMA_PATH}")
            return
        
        with open(SCHEMA_PATH, "r") as f:
            schema_sql = f.read()
        
        conn = self._get_connection()
        try:
            conn.executescript(schema_sql)
            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Schema initialization error: {e}")
    
    def close(self):
        """Close the database connection."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
    
    # Session operations
    
    def create_session(
        self,
        app_version: str = "1.0.0",
        notes: Optional[str] = None
    ) -> int:
        """
        Create a new session.
        
        Returns:
            New session ID
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO sessions (app_version, notes)
            VALUES (?, ?)
            """,
            (app_version, notes)
        )
        conn.commit()
        session_id = cursor.lastrowid
        logger.info(f"Created session {session_id}")
        return session_id
    
    def end_session(self, session_id: int):
        """Mark session as ended."""
        conn = self._get_connection()
        conn.execute(
            """
            UPDATE sessions SET ended_at = datetime('now')
            WHERE id = ?
            """,
            (session_id,)
        )
        conn.commit()
    
    # Window operations
    
    def register_window(
        self,
        session_id: int,
        window_id: str,
        title: Optional[str] = None,
        hwnd: Optional[int] = None
    ) -> int:
        """
        Register a tracked window.
        
        Returns:
            Window record ID
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO windows (session_id, window_id, title, hwnd)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, window_id, title, hwnd)
        )
        conn.commit()
        return cursor.lastrowid
    
    # Observation operations
    
    def insert_observation(
        self,
        session_id: Optional[int],
        window_id: str,
        timestamp: datetime,
        stage: str,
        dealer_seat: Optional[int],
        hero_position: Optional[str],
        active_players_count: Optional[int],
        active_positions_json: Optional[str],
        hero_cards_json: Optional[str],
        board_cards_json: Optional[str],
        pot_bb: Optional[float],
        raw_confidence_json: Optional[str]
    ) -> int:
        """
        Insert an observation record.
        
        Returns:
            Observation ID
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO observations (
                session_id, window_id, ts, stage, dealer_seat,
                hero_position, active_players_count, active_positions_json,
                hero_cards_json, board_cards_json, pot_bb, raw_confidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id, window_id, timestamp.isoformat(), stage, dealer_seat,
                hero_position, active_players_count, active_positions_json,
                hero_cards_json, board_cards_json, pot_bb, raw_confidence_json
            )
        )
        conn.commit()
        return cursor.lastrowid
    
    # Event operations
    
    def insert_event(
        self,
        session_id: Optional[int],
        window_id: str,
        timestamp: datetime,
        event_type: str,
        payload_json: Optional[str]
    ) -> int:
        """
        Insert an event record.
        
        Returns:
            Event ID
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO events (session_id, window_id, ts, type, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, window_id, timestamp.isoformat(), event_type, payload_json)
        )
        conn.commit()
        return cursor.lastrowid
    
    # Decision operations
    
    def insert_decision(
        self,
        session_id: Optional[int],
        window_id: str,
        timestamp: datetime,
        stage: str,
        hero_position: Optional[str],
        recommended_action: str,
        source: Optional[str],
        confidence: Optional[float]
    ) -> int:
        """
        Insert a decision record.
        
        Returns:
            Decision ID
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO decisions (
                session_id, window_id, ts, stage, hero_position,
                recommended_action, source, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id, window_id, timestamp.isoformat(), stage,
                hero_position, recommended_action, source, confidence
            )
        )
        conn.commit()
        return cursor.lastrowid
    
    # Query operations
    
    def get_session_observations(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[dict]:
        """Get observations for a session."""
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT * FROM observations
            WHERE session_id = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (session_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session_events(
        self,
        session_id: int,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """Get events for a session."""
        conn = self._get_connection()
        
        if event_type:
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE session_id = ? AND type = ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (session_id, event_type, limit)
            )
        else:
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE session_id = ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (session_id, limit)
            )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session_decisions(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[dict]:
        """Get decisions for a session."""
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT * FROM decisions
            WHERE session_id = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (session_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        conn = self._get_connection()
        
        stats = {}
        for table in ["sessions", "windows", "observations", "events", "decisions"]:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()["count"]
        
        return stats


# Module-level singleton
_db: Optional[Database] = None


def get_database(db_path: Optional[Path] = None) -> Database:
    """Get or create database singleton."""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db
