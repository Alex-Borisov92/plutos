"""
Tests for database storage.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.storage.db import Database


class TestDatabase:
    """Tests for Database class."""
    
    @pytest.fixture
    def db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            database = Database(db_path)
            yield database
            database.close()
    
    def test_database_initialization(self, db):
        """Test database can be initialized."""
        assert db.db_path.exists()
    
    def test_create_session(self, db):
        """Test creating a session."""
        session_id = db.create_session(app_version="1.0.0", notes="Test session")
        
        assert session_id is not None
        assert session_id > 0
    
    def test_multiple_sessions(self, db):
        """Test creating multiple sessions."""
        id1 = db.create_session()
        id2 = db.create_session()
        id3 = db.create_session()
        
        assert id1 < id2 < id3
    
    def test_end_session(self, db):
        """Test ending a session."""
        session_id = db.create_session()
        db.end_session(session_id)
        # Should not raise
    
    def test_register_window(self, db):
        """Test registering a window."""
        session_id = db.create_session()
        
        window_id = db.register_window(
            session_id=session_id,
            window_id="table_1",
            title="Test Poker Window",
            hwnd=12345
        )
        
        assert window_id is not None
        assert window_id > 0
    
    def test_insert_observation(self, db):
        """Test inserting an observation."""
        session_id = db.create_session()
        
        obs_id = db.insert_observation(
            session_id=session_id,
            window_id="table_1",
            timestamp=datetime.now(),
            stage="preflop",
            dealer_seat=3,
            hero_position="BTN",
            active_players_count=4,
            active_positions_json='["BTN", "SB", "BB", "UTG"]',
            hero_cards_json='["Ah", "Ks"]',
            board_cards_json='[]',
            pot_bb=1.5,
            raw_confidence_json='{"dealer": 1.0}'
        )
        
        assert obs_id is not None
        assert obs_id > 0
    
    def test_insert_event(self, db):
        """Test inserting an event."""
        session_id = db.create_session()
        
        event_id = db.insert_event(
            session_id=session_id,
            window_id="table_1",
            timestamp=datetime.now(),
            event_type="HERO_TURN",
            payload_json='{"position": "BTN"}'
        )
        
        assert event_id is not None
        assert event_id > 0
    
    def test_insert_decision(self, db):
        """Test inserting a decision."""
        session_id = db.create_session()
        
        decision_id = db.insert_decision(
            session_id=session_id,
            window_id="table_1",
            timestamp=datetime.now(),
            stage="preflop",
            hero_position="BTN",
            recommended_action="raise",
            source="placeholder",
            confidence=1.0
        )
        
        assert decision_id is not None
        assert decision_id > 0
    
    def test_get_session_observations(self, db):
        """Test retrieving observations."""
        session_id = db.create_session()
        
        # Insert some observations
        for i in range(5):
            db.insert_observation(
                session_id=session_id,
                window_id="table_1",
                timestamp=datetime.now(),
                stage="preflop",
                dealer_seat=i,
                hero_position="BTN",
                active_players_count=4,
                active_positions_json='[]',
                hero_cards_json='[]',
                board_cards_json='[]',
                pot_bb=1.5,
                raw_confidence_json=None
            )
        
        observations = db.get_session_observations(session_id, limit=10)
        
        assert len(observations) == 5
    
    def test_get_session_events(self, db):
        """Test retrieving events."""
        session_id = db.create_session()
        
        # Insert events
        db.insert_event(session_id, "table_1", datetime.now(), "HERO_TURN", None)
        db.insert_event(session_id, "table_1", datetime.now(), "HERO_TURN", None)
        db.insert_event(session_id, "table_1", datetime.now(), "OTHER", None)
        
        all_events = db.get_session_events(session_id)
        assert len(all_events) == 3
        
        hero_events = db.get_session_events(session_id, event_type="HERO_TURN")
        assert len(hero_events) == 2
    
    def test_get_stats(self, db):
        """Test getting database statistics."""
        session_id = db.create_session()
        db.insert_observation(
            session_id, "table_1", datetime.now(), "preflop",
            0, "BTN", 4, "[]", "[]", "[]", 1.5, None
        )
        db.insert_event(session_id, "table_1", datetime.now(), "TEST", None)
        
        stats = db.get_stats()
        
        assert stats["sessions"] >= 1
        assert stats["observations"] >= 1
        assert stats["events"] >= 1


class TestDatabaseThreadSafety:
    """Tests for database thread safety."""
    
    def test_multiple_connections(self):
        """Test that connections work across multiple threads."""
        import concurrent.futures
        
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            
            results = []
            
            def worker(worker_id):
                session_id = db.create_session(notes=f"Worker {worker_id}")
                return session_id
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(worker, i) for i in range(10)]
                results = [f.result() for f in futures]
            
            # All sessions should be created
            assert len(results) == 10
            assert len(set(results)) == 10  # All unique
            
            db.close()
        finally:
            # On Windows, SQLite may hold file locks briefly after close
            import time
            time.sleep(0.1)
            try:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors on Windows
