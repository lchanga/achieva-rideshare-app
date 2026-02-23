"""
Flask application factory.

This module wires together the HTTP layer (Flask) with the route blueprints.
Keeping this as a factory (`create_app`) makes the app easier to test and
configure (and avoids side effects at import time).
"""

from flask import Flask, jsonify
from flasgger import Swagger
from pathlib import Path
from flask import send_from_directory

from server.routes.client import client_bp
from server.routes.driver import driver_bp
from server.routes.optimizer import optimizer_bp
from server.routes.staff import staff_bp


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

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "AchievaPath API",
            "description": "Swagger/OpenAPI documentation for AchievaPath.",
            "version": "0.1.0",
        },
    }
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }
    Swagger(app, config=swagger_config, template=swagger_template)

    @app.get("/")
    def home():
        """
        Friendly homepage.
        ---
        tags:
          - Root
        responses:
          200:
            description: Plain-text landing page with helpful links.
        """
        return (
            "AchievaPath API is running.\n\n"
            "Try:\n"
            "- GET  /api/client/ride-requests\n"
            "- GET  /api/driver/routes/available\n"
            "- GET  /api/staff/clients\n"
            "- Open /ui/ (frontend demo)\n"
        )

    @app.get("/ui/")
    def ui_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/ui/<path:filename>")
    def ui_static(filename: str):
        return send_from_directory(frontend_dir, filename)

    @app.get("/test-db")
    def test_db():
        """
        Compatibility endpoint.

        This keeps the original smoke test path working while the rest of the
        API lives under `/api/*`.
        ---
        tags:
          - Root
        responses:
          200:
            description: SQL Server connectivity check succeeded.
          500:
            description: SQL Server connectivity check failed.
        """
        try:
            from server.db import get_db_connection

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

    # Attach role-based API route groups to a single Flask app.
    app.register_blueprint(client_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(optimizer_bp)

    return app

