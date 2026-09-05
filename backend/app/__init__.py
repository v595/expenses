from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.database import get_sqlalchemy_uri
from app.extensions import db, migrate
from app.routes.accounts import accounts_bp
from app.routes.activity import activity_bp
from app.routes.admin import admin_bp
from app.routes.admin_dashboard import admin_dashboard_bp
from app.routes.auth import auth_bp
from app.routes.bills import bills_bp
from app.routes.books import books_bp
from app.routes.budgets import budgets_bp
from app.routes.cashbook import cashbook_bp
from app.routes.categories import categories_bp
from app.routes.dashboard import dashboard_bp
from app.routes.goals import goals_bp
from app.routes.health import health_bp
from app.routes.ledger import ledger_bp
from app.routes.notifications import notifications_bp
from app.routes.parties import parties_bp
from app.routes.party_reports import party_reports_bp
from app.routes.recurring import recurring_bp
from app.routes.reminders import reminders_bp
from app.routes.settings import settings_bp
from app.routes.super_admin import super_admin_bp
from app.routes.tags import tags_bp
from app.routes.transactions import transactions_bp

BASELINE_REVISION = "0001_baseline"


def _ensure_database(app):
    """Bring the configured database up to the latest schema.

    A brand-new database (fresh dev checkout, or the temp SQLite file each
    test spins up) just gets every migration applied in order. A database
    that already has the pre-Alembic, hand-rolled schema on it (the local
    dev SQLite file, or an already-provisioned Postgres instance) has its
    tables but no `alembic_version` row — that gets stamped to the baseline
    revision first (marking "already has the original schema" without
    re-running those CREATE TABLEs) and then upgraded the rest of the way,
    so existing data is never touched, only new columns/tables are added.
    """
    import os

    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config as AlembicConfig

    script_location = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")
    if not os.path.isdir(script_location):
        # Not scaffolded yet (e.g. this import is itself part of running
        # `flask db init`/`migrate` for the first time) — nothing to do.
        return

    alembic_cfg = AlembicConfig(os.path.join(script_location, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", script_location)

    with app.app_context():
        inspector = sa.inspect(db.engine)
        has_legacy_schema = inspector.has_table("users")
        has_alembic_version = inspector.has_table("alembic_version")

        if has_legacy_schema and not has_alembic_version:
            command.stamp(alembic_cfg, BASELINE_REVISION)
        command.upgrade(alembic_cfg, "head")


def _ensure_admin_exists(app):
    """Also checked at boot (in addition to right after each registration —
    see `user_model.promote_first_user_if_no_admin`), so the app recovers on
    its own if it's ever left with zero admins."""
    from app.models import user as user_model

    with app.app_context():
        user_model.promote_first_user_if_no_admin()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_sqlalchemy_uri()

    # Allow the React dev server (running on a different port) to call this API.
    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")

    _ensure_database(app)
    _ensure_admin_exists(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(bills_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(parties_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(cashbook_bp)
    app.register_blueprint(party_reports_bp)

    # Fallbacks so even unexpected errors come back as JSON, matching every
    # other response this API sends, instead of Flask's default HTML pages.
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "Internal server error"}), 500

    return app
