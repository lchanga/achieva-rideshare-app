"""
Flask application factory.

This module wires together the HTTP layer (Flask) with the route blueprints.
Keeping this as a factory (`create_app`) makes the app easier to test and
configure (and avoids side effects at import time).
"""

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_smorest import Api
from sqlalchemy import text
from sqlalchemy.orm import Session

from server.bootstrap import ensure_database_ready
from server.db import get_db_connection, get_engine
from server.routes.auth import auth_blp
from server.routes.client import client_blp
from server.routes.driver import driver_blp
from server.routes.optimizer import optimizer_blp
from server.routes.staff import staff_blp
from server.scheduler import start_nightly_optimizer


def create_app() -> Flask:
    """
    Build and configure the Flask app instance.

    Blueprints map URL routes to handlers for each role area:
    - client routes: "/api/client/*"
    - driver routes: "/api/driver/*"
    - staff routes:  "/api/staff/*"
    - optimizer routes: "/api/optimizer/*"
    """
    app = Flask(__name__)
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    ensure_database_ready()
    start_nightly_optimizer()
    app.config.update(
        API_TITLE="AchievaPath API",
        API_VERSION="0.1.0",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_JSON_PATH="openapi.json",
        # End with "/" so both "/apidocs" and "/apidocs/" work (Flask redirects).
        OPENAPI_SWAGGER_UI_PATH="/apidocs/",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/",
    )
    api = Api(app)

    @app.get("/")
    def home():
        return (
            "AchievaPath API is running.\n\n"
            "Try:\n"
            "- POST /api/auth/login\n"
            "- GET  /api/client/ride-requests\n"
            "- GET  /api/client/<client_id>/permanent-locations\n"
            "- GET  /api/driver/routes/available\n"
            "- GET  /api/driver/<driver_id>/today-route\n"
            "- GET  /api/staff/clients\n"
            "- POST /api/optimizer/run\n"
            "- Open /ui/ (role landing page)\n"
            "- Swagger UI: /apidocs/\n"
        )

    @app.get("/ui/")
    def ui_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/ui/<path:filename>")
    def ui_static(filename: str):
        return send_from_directory(frontend_dir, filename)

    @app.get("/test-db")
    def test_db():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            conn.close()

            return jsonify(
                {
                    "status": "Success!",
                    "database_version": row[0],
                    "message": "The bridge to SQL Server is working.",
                }
            )
        except Exception as e:
            return jsonify({"status": "Error", "error_details": str(e)}), 500

    @app.get("/healthcheck")
    def healthcheck():
        try:
            with Session(get_engine()) as session:
                session.execute(text("SELECT 1"))
            return jsonify({"database": "connected"})
        except Exception as e:
            return jsonify({"database": "disconnected", "error_details": str(e)}), 500

    # Attach role-based API route groups to a single Flask app + OpenAPI.
    api.register_blueprint(auth_blp)
    api.register_blueprint(client_blp)
    api.register_blueprint(driver_blp)
    api.register_blueprint(staff_blp)
    api.register_blueprint(optimizer_blp)

    return app