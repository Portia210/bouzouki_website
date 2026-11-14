"""Local development server with auto-reload: `uv run python main.py`.

Restarts on Python changes and re-reads templates on every request. Never use this on
Railway — production runs gunicorn (see Procfile).
"""

import logging
import os
import re

os.environ.setdefault("LOG_LEVEL", "WARNING")  # dev console: problems only (set LOG_LEVEL=INFO for more)

import flask.cli

from app import app

flask.cli.show_server_banner = lambda *args, **kwargs: None  # "Serving Flask app… development server" banner

# One access-log line per page, not per image/script/keystroke; errors are always shown.
_QUIET = re.compile(r'"(?:GET|HEAD) (?:/images/|/static/|/bootstrap/|/favicon\.ico|/search\?|/healthz)\S* HTTP/[\d.]+" [23]\d\d')
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_STARTUP_CHATTER = ("development server", "Press CTRL+C", "Restarting with", "Running on")


class _PagesOnly(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = _ANSI.sub("", record.getMessage())  # werkzeug colours status codes
        return not (_QUIET.search(message) or any(chatter in message for chatter in _STARTUP_CHATTER))


logging.getLogger("werkzeug").addFilter(_PagesOnly())

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":  # the reloader child; print once, not twice
        print(f"Bouzouki Rebetico dev server: http://localhost:{port}  (auto-reload on, Ctrl+C to stop)", flush=True)
    # Localhost only, and no in-browser debugger (it would allow code execution from the page).
    app.run(host="127.0.0.1", port=port, debug=True, use_debugger=False)
