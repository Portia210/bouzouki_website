"""Local development server with auto-reload: `uv run python main.py`.

Restarts on Python changes and re-reads templates on every request. Never use this on
Railway — production runs gunicorn (see Procfile).
"""

import os

from app import app

if __name__ == "__main__":
    # Bound to localhost only: debug mode exposes the Werkzeug debugger.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=True)
