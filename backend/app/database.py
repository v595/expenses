import os
import sqlite3

# Render's free tier has no persistent disk, so SQLite gets wiped on every
# redeploy. In production DATABASE_URL points at a real (free) Postgres
# instance; locally and in tests it's unset, so everything falls back to the
# original SQLite file with zero setup required.
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "database", "expense_tracker.db")


class DBConnection:
    """Wraps either a sqlite3 or psycopg2 connection behind the same
    `conn.execute(sql, params).fetchone()/.fetchall()` interface the model
    layer already uses, so that code doesn't need to know which database
    it's talking to. `?` placeholders are translated to `%s` for Postgres."""

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=()):
        if IS_POSTGRES:
            sql = sql.replace("?", "%s")
        cursor = self._raw.cursor()
        cursor.execute(sql, params)
        return cursor

    def executescript(self, sql):
        if IS_POSTGRES:
            self._raw.cursor().execute(sql)
        else:
            self._raw.executescript(sql)

    def commit(self):
        self._raw.commit()

    def close(self):
        self._raw.close()


def get_db_path():
    # Read at call-time (not import-time) so tests can point this at a
    # temp file via the DATABASE_PATH env var, set up in tests/conftest.py.
    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)


def get_db_connection():
    if IS_POSTGRES:
        raw = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return DBConnection(raw)

    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    raw = sqlite3.connect(db_path)
    raw.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["email"]
    raw.execute("PRAGMA foreign_keys = ON")
    return DBConnection(raw)


def init_db():
    conn = get_db_connection()

    if IS_POSTGRES:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                token TEXT,
                avatar TEXT,
                is_admin INTEGER NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'USD',
                notify_budget_alerts INTEGER NOT NULL DEFAULT 1,
                notify_bill_reminders INTEGER NOT NULL DEFAULT 1,
                last_login_at TEXT
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'cash',
                balance REAL NOT NULL DEFAULT 0,
                color TEXT,
                UNIQUE (user_id, name)
            );

            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                color TEXT,
                UNIQUE (user_id, name, type)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                account_id INTEGER,
                receipt TEXT
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                UNIQUE (user_id, category)
            );

            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                category TEXT NOT NULL,
                description TEXT,
                frequency TEXT NOT NULL CHECK (frequency IN ('weekly', 'monthly', 'yearly')),
                next_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS goals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL DEFAULT 0,
                target_date TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bills (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                due_date TEXT NOT NULL,
                is_paid INTEGER NOT NULL DEFAULT 0,
                repeat_frequency TEXT
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                ref_key TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                name TEXT NOT NULL,
                UNIQUE (user_id, name)
            );

            CREATE TABLE IF NOT EXISTS transaction_tags (
                transaction_id INTEGER NOT NULL REFERENCES transactions (id),
                tag_id INTEGER NOT NULL REFERENCES tags (id),
                PRIMARY KEY (transaction_id, tag_id)
            );

            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()

        # Idempotent column additions for databases created before these
        # features existed — Postgres supports IF NOT EXISTS natively here,
        # so no try/except dance is needed like on the SQLite side below.
        conn.executescript(
            """
            ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin INTEGER NOT NULL DEFAULT 0;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS currency TEXT NOT NULL DEFAULT 'USD';
            ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_budget_alerts INTEGER NOT NULL DEFAULT 1;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_bill_reminders INTEGER NOT NULL DEFAULT 1;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TEXT;
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS account_id INTEGER;
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS receipt TEXT;
            """
        )
        conn.commit()
        conn.close()
        return

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

        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'cash',
            balance REAL NOT NULL DEFAULT 0,
            color TEXT,
            UNIQUE (user_id, name),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            color TEXT,
            UNIQUE (user_id, name, type),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0,
            target_date TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            is_paid INTEGER NOT NULL DEFAULT 0,
            repeat_frequency TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            ref_key TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE (user_id, name),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS transaction_tags (
            transaction_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (transaction_id, tag_id),
            FOREIGN KEY (transaction_id) REFERENCES transactions (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
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

    # Phase: settings, notifications, accounts, goals, bills, categories, tags.
    for statement in (
        "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'",
        "ALTER TABLE users ADD COLUMN notify_budget_alerts INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE users ADD COLUMN notify_bill_reminders INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE users ADD COLUMN last_login_at TEXT",
        "ALTER TABLE transactions ADD COLUMN account_id INTEGER",
        "ALTER TABLE transactions ADD COLUMN receipt TEXT",
    ):
        try:
            conn.execute(statement)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    # The very first account ever registered becomes the admin, so there's
    # always someone who can see the admin dashboard without a manual DB edit.
    row = conn.execute("SELECT COUNT(*) AS count FROM users WHERE is_admin = 1").fetchone()
    if row["count"] == 0:
        first_user = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
        if first_user:
            conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (first_user["id"],))
            conn.commit()

    conn.close()
