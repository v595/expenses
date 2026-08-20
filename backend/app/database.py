import os
import sqlite3

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "database", "expense_tracker.db")


def get_db_path():
    # Read at call-time (not import-time) so tests can point this at a
    # temp file via the DATABASE_PATH env var, set up in tests/conftest.py.
    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)


def get_db_connection():
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["email"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            UNIQUE (user_id, category),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS recurring_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            category TEXT NOT NULL,
            description TEXT,
            frequency TEXT NOT NULL CHECK (frequency IN ('weekly', 'monthly', 'yearly')),
            next_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    conn.commit()

    # Small migration: add a token column for auth (Phase 5), if it's not there yet.
    # ponytail: no migration framework, just a try/except add-column. Reach for
    # Alembic/Flask-Migrate if the schema starts changing often.
    try:
        conn.execute("ALTER TABLE users ADD COLUMN token TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    # Phase: profile pictures. Stored as a data: URI directly in the row
    # (small images only, size-capped in the service layer) rather than on
    # disk, since cloud hosts don't guarantee a persistent filesystem.
    try:
        conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.close()
