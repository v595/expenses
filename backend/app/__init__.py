from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.database import init_db
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.health import health_bp
from app.routes.transactions import transactions_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Allow the React dev server (running on a different port) to call this API.
    CORS(app)

    # Make sure the database file and tables exist before handling any request.
    init_db()

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

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
