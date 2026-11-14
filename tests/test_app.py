import re


def test_pages_render(client, catalog):
    artist = catalog.artists[0]
    song = artist.songs[0]
    assert client.get("/").status_code == 200
    page = client.get(f"/artist/{artist.slug}")
    assert page.status_code == 200
    # the player starts on the first song; original recording = video_id, lesson = demo_id
    html = page.get_data(as_text=True)
    assert html.index("player-original") < html.index("player-lesson")
    assert f"embed/{song.video_id}" in html and f"embed/{song.demo_id}" in html
    assert f"watch?v={song.video_id}" in html  # plain YouTube link for videos that refuse embedding
    assert f'data-slug="{song.slug}"' in html


def test_song_url_redirects_to_artist_page_opened_on_that_song(client, catalog):
    song = catalog.song_by_slug["alaniaris"]
    r = client.get("/song/alaniaris")
    assert r.status_code == 301
    assert r.headers["Location"].endswith(f"/artist/{song.artist.slug}#alaniaris")


def test_every_artist_has_songs_and_slugs_are_short_and_unique(catalog):
    assert all(a.songs for a in catalog.artists)
    slugs = [s.slug for s in catalog.songs] + [a.slug for a in catalog.artists]
    assert all(re.fullmatch(r"[a-z0-9-]{1,32}", s) for s in slugs)
    assert len({s.slug for s in catalog.songs}) == len(catalog.songs)


def test_duplicate_titles_are_both_reachable(client, catalog):
    pyretos = [s for s in catalog.songs if s.en_name == "Pyretos"]
    assert len(pyretos) == 2
    targets = {client.get(f"/song/{s.slug}").headers["Location"] for s in pyretos}
    assert len(targets) == 2  # each lands on its own artist page / anchor


def test_legacy_name_urls_redirect_permanently(client):
    r = client.get("/song/Alaniaris")
    assert r.status_code == 301 and r.headers["Location"].endswith("#alaniaris")
    r = client.get("/artist/Vamvakaris%20Markos")
    assert r.status_code == 301 and r.headers["Location"].endswith("/artist/vamvakaris-markos")


def test_unknown_urls_give_friendly_404(client):
    for url in ("/song/nope", "/artist/nope", "/images/nope", "/nothing-here"):
        r = client.get(url)
        assert r.status_code == 404 and b"Page Not Found" in r.data


def test_search_api(client):
    data = client.get("/search?term=mou").get_json()
    assert data and {"type", "slug", "label", "label_gr", "sub", "url"} <= data[0].keys()
    song = next(r for r in data if r["type"] == "song")
    assert song["url"] == f"/artist/{client.application.extensions['catalog'].song_by_slug[song['slug']].artist.slug}#{song['slug']}"
    assert client.get("/search?term=").get_json() == []
    assert client.get("/search?term=" + "a" * 200).get_json() == []
    assert client.get("/search?term=mou&artist=unknown").get_json() == []
    assert len(client.get("/search?term=mou&limit=3").get_json()) <= 7  # 3 songs + up to 4 artists


def test_search_results_page_escapes_input(client):
    html = client.get("/find?q=<script>alert(1)</script>").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html


def test_image_is_served_with_etag(client):
    r = client.get("/images/vamvakaris-markos")
    assert r.status_code == 200 and r.mimetype == "image/png"
    again = client.get("/images/vamvakaris-markos", headers={"If-None-Match": r.headers["ETag"]})
    assert again.status_code == 304


def test_security_headers(client):
    h = client.get("/").headers
    assert "frame-src https://www.youtube-nocookie.com" in h["Content-Security-Policy"]
    assert "script-src" not in h["Content-Security-Policy"].replace("default-src", "")  # inline scripts stay blocked
    assert h["X-Content-Type-Options"] == "nosniff"


def test_no_inline_script_or_style_in_pages(client, catalog):
    for url in ("/", f"/artist/{catalog.artists[0].slug}", "/find?q=mou"):
        html = client.get(url).get_data(as_text=True)
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), url
        assert " style=" not in html, url


def test_healthz_robots_sitemap(client, catalog):
    assert client.get("/healthz").data == b"ok"
    assert b"Sitemap:" in client.get("/robots.txt").data
    sitemap = client.get("/sitemap.xml").get_data(as_text=True)
    assert sitemap.count("<url>") == 1 + len(catalog.artists)  # songs live on artist pages


def test_favicon_and_manifest(client):
    ico = client.get("/favicon.ico")
    assert ico.status_code == 200 and ico.data[:4] == b"\x00\x00\x01\x00"
    assert client.get("/static/img/favicon.svg").status_code == 200
    assert client.get("/static/img/apple-touch-icon.png").mimetype == "image/png"
    manifest = client.get("/static/site.webmanifest").get_json(force=True)
    assert manifest["name"] == "Rebetiko Music"
    for icon in manifest["icons"]:
        assert client.get(icon["src"]).status_code == 200
    html = client.get("/").get_data(as_text=True)
    for needle in ("favicon.svg", "/favicon.ico", "apple-touch-icon.png", "site.webmanifest"):
        assert needle in html
