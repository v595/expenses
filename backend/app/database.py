import os

# Render's free tier has no persistent disk, so SQLite gets wiped on every
# redeploy. In production DATABASE_URL points at a real (free) Postgres
# instance; locally and in tests it's unset, so everything falls back to the
# original SQLite file with zero setup required.
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "database", "expense_tracker.db")


def get_db_path():
    # Read at call-time (not import-time) so tests can point this at a
    # temp file via the DATABASE_PATH env var, set up in tests/conftest.py.
    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)


def get_sqlalchemy_uri():
    """SQLAlchemy connection string for whichever backend is configured.
    Postgres (`postgresql+psycopg2://...`) in production via DATABASE_URL,
    otherwise the local/test SQLite file (created on demand)."""
    if IS_POSTGRES:
        url = DATABASE_URL
        # Render (and some other hosts) hand out `postgres://`, which
        # SQLAlchemy 1.4+/2.x no longer accepts — it wants `postgresql://`.
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url

    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return f"sqlite:///{db_path}"
