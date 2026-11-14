import os
from functools import lru_cache
from hashlib import sha1
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, abort, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_bootstrap import Bootstrap5
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from classes import Catalog, load_artist_image, load_catalog
from logger import logger
from search import MAX_QUERY_LEN, SearchIndex

load_dotenv()

CSP = (
    "default-src 'self'; img-src 'self' data:; "
    "frame-src https://www.youtube-nocookie.com; "
    "base-uri 'self'; form-action 'self'; frame-ancestors 'self'"
)


def _sniff_image(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def create_app(db_file: str | Path | None = None, secret_key: str | None = None) -> Flask:
    app = Flask(__name__)

    secret_key = secret_key or os.getenv("FLASK_SECRET_KEY")
    if not secret_key:
        logger.error("FLASK_SECRET_KEY environment variable not set")
        raise RuntimeError("FLASK_SECRET_KEY environment variable is required")
    app.config["SECRET_KEY"] = secret_key
    app.config["BOOTSTRAP_SERVE_LOCAL"] = True  # no CDN: faster, and the CSP stays strict

    # Behind Railway's proxy the client IP and scheme arrive in X-Forwarded-* headers.
    proxy_hops = int(os.getenv("TRUST_PROXY_HOPS", "0"))
    if proxy_hops:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_hops, x_proto=proxy_hops, x_host=proxy_hops)

    Bootstrap5(app)

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["600 per hour"],
        storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )
    limiter.init_app(app)

    @limiter.request_filter
    def _exempt():
        return request.endpoint in ("healthz",) or (request.endpoint or "").endswith("static")

    catalog: Catalog = load_catalog(db_file)
    index = SearchIndex(catalog)
    app.extensions["catalog"] = catalog
    db_source = db_file

    @lru_cache(maxsize=128)
    def artist_image(artist_id: int):
        data = load_artist_image(artist_id, db_source)
        if not data:
            return None
        return data, _sniff_image(data), sha1(data).hexdigest()

    # ---------------------------------------------------------------- pages
    @app.route("/")
    def home():
        artists = sorted(catalog.artists, key=lambda a: (-a.number_of_songs, a.en_name))
        return render_template("index.html", artists=artists, song_count=len(catalog.songs))

    @app.route("/artist/<slug>")
    def artist_songs(slug):
        artist = catalog.artist_by_slug.get(slug)
        if not artist:
            legacy = catalog.artist_by_name.get(slug)
            if legacy:
                return redirect(url_for("artist_songs", slug=legacy.slug), 301)
            abort(404)
        return render_template("artist_songs.html", artist=artist)

    @app.route("/song/<slug>")
    def view_song(slug):
        # Songs have no page of their own: the artist page opens on the song.
        song = catalog.song_by_slug.get(slug) or catalog.song_by_name.get(slug)  # name = pre-slug URLs
        if not song:
            abort(404)
        return redirect(url_for("artist_songs", slug=song.artist.slug, _anchor=song.slug), 301)

    @app.route("/find")
    def find():
        term = (request.args.get("q") or "")[:MAX_QUERY_LEN].strip()
        artists, songs = index.search(term, song_limit=100, artist_limit=10)
        return render_template("search_results.html", term=term, artists=artists, songs=songs)

    # ------------------------------------------------------------------ API
    @app.route("/search")
    @limiter.limit("90 per minute")
    def search_songs():
        term = (request.args.get("term") or "").strip()
        if not term or len(term) > MAX_QUERY_LEN:
            return jsonify([])
        only_artist = catalog.artist_by_slug.get(request.args.get("artist", ""))
        if request.args.get("artist") and not only_artist:
            return jsonify([])
        try:
            limit = min(max(int(request.args.get("limit", 8)), 1), 200)
        except ValueError:
            limit = 8
        artists, songs = index.search(term, song_limit=limit, artist_limit=4, artist=only_artist)
        results = [
            {"type": "artist", "slug": a.slug, "label": a.en_name, "label_gr": a.gr_name,
             "sub": f"{a.number_of_songs} songs", "url": url_for("artist_songs", slug=a.slug)}
            for a in artists
        ] + [
            {"type": "song", "slug": s.slug, "label": s.en_name, "label_gr": s.gr_name,
             "sub": s.artist.en_name, "url": url_for("artist_songs", slug=s.artist.slug, _anchor=s.slug)}
            for s in songs
        ]
        return jsonify(results)

    @app.route("/images/<slug>")
    @limiter.limit("300 per minute")
    def images(slug):
        artist = catalog.artist_by_slug.get(slug)
        if not artist or not artist.has_image:
            abort(404)
        loaded = artist_image(artist.artist_id)
        if not loaded:
            abort(404)
        data, mimetype, etag = loaded
        if request.headers.get("If-None-Match") == f'"{etag}"':
            return Response(status=304, headers={"ETag": f'"{etag}"'})
        return Response(data, mimetype=mimetype, headers={
            "ETag": f'"{etag}"',
            "Cache-Control": "public, max-age=604800",
            "X-Content-Type-Options": "nosniff",
        })

    # ----------------------------------------------------------------- misc
    @app.route("/healthz")
    def healthz():
        return "ok"

    @app.route("/favicon.ico")
    def favicon():
        # Browsers request this path by default, whatever the <link rel="icon"> says.
        return send_from_directory(app.static_folder, "favicon.ico", max_age=604800)

    @app.route("/robots.txt")
    def robots():
        return Response(f"User-agent: *\nAllow: /\nSitemap: {url_for('sitemap', _external=True)}\n", mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap():
        urls = [url_for("home", _external=True)]
        urls += [url_for("artist_songs", slug=a.slug, _external=True) for a in catalog.artists]
        body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
        return Response(
            f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>',
            mimetype="application/xml",
        )

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("Content-Security-Policy", CSP)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response

    # --------------------------------------------------------------- errors
    def _error(code: int, message: str):
        return render_template("error.html", error_code=code, error_message=message), code

    @app.errorhandler(400)
    def bad_request(error):
        return _error(400, "Bad Request")

    @app.errorhandler(404)
    def not_found(error):
        logger.info(f"404 {request.path}")
        return _error(404, "Page Not Found")

    @app.errorhandler(429)
    def too_many(error):
        return _error(429, "Too Many Requests")

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 on {request.path}: {error}")
        return _error(500, "Internal Server Error")

    return app


# Module-level instance for `gunicorn app:app`. Skipped when imported for tests that
# build their own app (set SKIP_DEFAULT_APP=1).
app = None if os.getenv("SKIP_DEFAULT_APP") else create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port)
