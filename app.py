from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_bootstrap import Bootstrap5
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from classes import import_db
from dotenv import load_dotenv
from io import BytesIO
import os
import re
from urllib.parse import unquote
from markupsafe import escape
from logger import logger
load_dotenv()

app = Flask(__name__)

# Require SECRET_KEY to be set in environment
secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    logger.error("FLASK_SECRET_KEY environment variable not set")
    raise RuntimeError("FLASK_SECRET_KEY environment variable is required for security")
app.config['SECRET_KEY'] = secret_key

Bootstrap5(app)

# Configure caching
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 2592000  # 30 days in seconds
})

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Input validation functions
def sanitize_route_param(param):
    """Sanitize route parameters to prevent injection attacks"""
    if not param:
        logger.warning("Empty parameter provided")
        return None

    # URL decode the parameter
    param = unquote(param)

    # Remove any potentially dangerous characters
    param = re.sub(r'[<>"\'\/\\&]', '', param)

    # Limit length to prevent DoS
    if len(param) > 200:
        logger.warning(f"Parameter too long: {len(param)} characters")
        param = param[:200]

    return param.strip()

def validate_search_term(term):
    """Validate and sanitize search terms"""
    if not term or not isinstance(term, str):
        logger.debug("Invalid or empty search term")
        return None

    # Limit search term length
    if len(term) > 100:
        logger.warning(f"Search term too long: {len(term)} characters")
        return None

    # Allow only alphanumeric, spaces, and some Greek characters
    if not re.match(r'^[\w\s\u0370-\u03FF\u1F00-\u1FFF-]+$', term, re.UNICODE):
        logger.warning(f"Invalid characters in search term: {term}")
        return None

    return term.strip()

# Global variable to store all artists (loaded once at startup)
try:
    all_artists = import_db()
    logger.info(f"Successfully loaded {len(all_artists)} artists from database")
except Exception as e:
    logger.error(f"Failed to load database: {e}")
    all_artists = []

@app.route("/")
def home():
    # Sort artists by the number of songs
    sorted_artists = sorted(all_artists, key=lambda x: x.number_of_songs, reverse=True)
    return render_template("index.html", all_artists=sorted_artists)


@app.route("/artist/<artist_name>")
def artist_songs(artist_name):
    logger.info(f"Artist page requested: {artist_name}")

    # Sanitize the artist name parameter
    sanitized_name = sanitize_route_param(artist_name)
    if not sanitized_name:
        logger.warning(f"Invalid artist name parameter: {artist_name}")
        abort(400)

    # Use a dictionary for efficient artist lookup
    artist = next((artist for artist in all_artists if artist.en_name == sanitized_name), None)
    if not artist:
        logger.warning(f"Artist not found: {sanitized_name}")
        abort(404)

    try:
        logger.info(f"Serving artist page for: {sanitized_name}")
        return render_template("artist_songs.html", artist=artist)
    except Exception as e:
        logger.error(f"Error rendering artist page for {sanitized_name}: {e}")
        abort(500)


@app.route("/search", methods=["GET"])
@limiter.limit("30 per minute")
def search_songs():
    try:
        term = request.args.get("term")
        logger.debug(f"Search request received: {term}")

        # Validate and sanitize the search term
        sanitized_term = validate_search_term(term)
        if not sanitized_term:
            logger.debug(f"Invalid search term rejected: {term}")
            return jsonify([])

        logger.info(f"Processing search for: {sanitized_term}")
        results = []

        # Use the global all_artists variable (no need to fetch from database again)
        if not all_artists:
            logger.warning("No artists available for search")
            return jsonify([])

        for artist in all_artists:
            for song in artist.songs:
                # Check if the term is in either the English or Greek song name
                if (sanitized_term.lower() in song.en_name.lower() or
                    sanitized_term.lower() in song.gr_name.lower()):
                    results.append({
                        'label': escape(song.en_name),  # Escape output for security
                        'value': escape(song.en_name),
                        'url': f"/song/{song.en_name}"
                    })

                    # Limit results to prevent performance issues
                    if len(results) >= 50:
                        logger.debug("Search results limited to 50 items")
                        break
            if len(results) >= 50:
                break

        logger.info(f"Search for '{sanitized_term}' returned {len(results)} results")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        return jsonify([])


@app.route("/song/<song_name>")
def view_song(song_name):
    logger.info(f"Song page requested: {song_name}")

    # Sanitize the song name parameter
    sanitized_name = sanitize_route_param(song_name)
    if not sanitized_name:
        logger.warning(f"Invalid song name parameter: {song_name}")
        abort(400)

    # Find the song from the list of artists
    song = None
    artist_obj = None
    for artist in all_artists:
        for s in artist.songs:
            if s.en_name == sanitized_name:
                song = s
                artist_obj = artist
                break
        if song:
            break

    if not song:
        logger.warning(f"Song not found: {sanitized_name}")
        abort(404)

    try:
        logger.info(f"Serving song page for: {sanitized_name}")
        return render_template("song_details.html", artist=artist_obj, song=song)
    except Exception as e:
        logger.error(f"Error rendering song page for {sanitized_name}: {e}")
        abort(500)


@app.route("/images/<artist_name>")
@limiter.limit("100 per minute")  # Rate limit image requests to prevent abuse
@cache.cached(timeout=2592000)  # Cache for 30 days
def images(artist_name):
    logger.debug(f"Image request for artist: {artist_name}")

    # Sanitize the artist name parameter
    sanitized_name = sanitize_route_param(artist_name)
    if not sanitized_name:
        logger.warning(f"Invalid artist name parameter for image: {artist_name}")
        abort(400)

    artist = next((artist for artist in all_artists if artist.en_name == sanitized_name), None)
    if not artist or not artist.artist_img:
        logger.warning(f"Artist image not found: {sanitized_name}")
        abort(404)

    try:
        logger.debug(f"Serving image for: {sanitized_name}")
        # Add security headers for image serving
        response = send_file(
            BytesIO(artist.artist_img),
            mimetype='image/png',
            as_attachment=False,
            download_name=f"{sanitized_name}.png"
        )
        response.headers['Content-Security-Policy'] = "default-src 'none'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'  # Cache for 30 days
        return response
    except Exception as e:
        logger.error(f"Error serving image for {artist_name}: {e}")
        abort(500)

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"400 Bad Request: {error}")
    return render_template('error.html',
                         error_code=400,
                         error_message="Bad Request - Invalid input provided"), 400

@app.errorhandler(404)
def not_found(error):
    logger.info(f"404 Not Found: {error}")
    return render_template('error.html',
                         error_code=404,
                         error_message="Page Not Found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Internal Server Error: {error}")
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal Server Error"), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Rebetiko Music application on port {port}")
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        raise
