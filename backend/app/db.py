import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plans (
  project_id TEXT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  original_name TEXT NOT NULL,
  stored_name TEXT NOT NULL,
  ext TEXT NOT NULL,
  size INTEGER NOT NULL,
  uploaded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inputs (
  project_id TEXT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  data TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def migrate(conn):
    """Add the drawing-reading columns to databases created before the reader was connected."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(plans)")}
    if "reading" not in cols:
        conn.execute("ALTER TABLE plans ADD COLUMN reading TEXT")
    if "reading_status" not in cols:
        conn.execute("ALTER TABLE plans ADD COLUMN reading_status TEXT")
    # A reading that was running when the server stopped will never finish; let it be started again.
    conn.execute("UPDATE plans SET reading_status=NULL WHERE reading_status='pending'")
    conn.commit()


def connect(path):
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        migrate(db)
