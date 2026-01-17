-- Plutos Database Schema
-- SQLite database for poker session tracking

-- Sessions table - one per app run
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT,
    app_version TEXT,
    notes TEXT
);

-- Tracked windows table
CREATE TABLE IF NOT EXISTS windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    window_id TEXT NOT NULL,
    title TEXT,
    hwnd INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Observations - snapshots of table state
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    window_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    stage TEXT NOT NULL,
    dealer_seat INTEGER,
    hero_position TEXT,
    active_players_count INTEGER,
    active_positions_json TEXT,
    hero_cards_json TEXT,
    board_cards_json TEXT,
    pot_bb REAL,
    raw_confidence_json TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Events - significant occurrences like hero turn
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    window_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    type TEXT NOT NULL,
    payload_json TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Decisions - recommended actions
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    window_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    stage TEXT NOT NULL,
    hero_position TEXT,
    recommended_action TEXT NOT NULL,
    source TEXT,
    confidence REAL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_observations_session ON observations(session_id);
CREATE INDEX IF NOT EXISTS idx_observations_window ON observations(window_id);
CREATE INDEX IF NOT EXISTS idx_observations_ts ON observations(ts);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id);
