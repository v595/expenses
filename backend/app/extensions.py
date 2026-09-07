from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
# Storage defaults to in-memory, which is fine for a single-process deploy;
# swap in a redis:// STORAGE_URI once this runs on more than one worker, or
# every worker enforces its own separate limit instead of a shared one.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
