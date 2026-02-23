"""
Entry point for running the Flask app.

Run locally with:
  python -m server.run

Docker also uses this module entrypoint.
"""

import os

from server.app import create_app

app = create_app()

def main() -> None:
    """
    Start the Flask development server.

    Configuration is controlled via environment variables so the same code
    works in local dev and inside Docker.
    """
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()

