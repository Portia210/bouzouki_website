import re
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

import pytest

import storage
from app import create_app
from classes import DEFAULT_DB

PASSWORD = "correct horse battery"


@pytest.fixture
def pdf_db(tmp_path):
    """A copy of the real catalog where song 1 has both PDFs and song 2 has only a sheet."""
    path = tmp_path / "music.db"
    shutil.copy(DEFAULT_DB, path)
    conn = sqlite3.connect(path)
    conn.execute("UPDATE songs SET score_key = 'pdf/1/sheet.pdf', tab_key = 'pdf/1/tab.pdf' WHERE song_id = 1")
    conn.execute("UPDATE songs SET score_key = 'pdf/2/sheet.pdf' WHERE song_id = 2")
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def app(pdf_db, monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HOPS", raising=False)
    monkeypatch.setenv("DEV_SERVER", "1")  # plain-http test client: the cookie must not be Secure
    app = create_app(pdf_db, secret_key="test-key", admin_password=PASSWORD)
    monkeypatch.setattr(storage, "presigned_url", lambda key, filename, expires=300: f"https://r2.test/{key}?name={filename}")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def token(client):
    html = client.get("/admin").get_data(as_text=True)
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


def sign_in(client, password=PASSWORD, **extra):
    return client.post("/admin", data={"csrf": token(client), "password": password, **extra})


def is_admin(client):
    return client.get("/admin/session").get_json()["admin"]


def test_admin_is_off_without_a_password(pdf_db, monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    client = create_app(pdf_db, secret_key="test-key", admin_password="").test_client()
    assert client.get("/admin").status_code == 404
    assert client.get("/pdf/1/sheet").status_code == 404
    page = client.get("/artist/" + client.application.extensions["catalog"].song_by_id[1].artist.slug).get_data(as_text=True)
    assert "data-sheet" not in page and "data-tab-pdf" not in page


def test_wrong_password_and_missing_csrf_do_not_sign_in(client):
    r = sign_in(client, "nope")
    assert r.status_code == 401 and b"Wrong password" in r.data and not is_admin(client)
    assert client.post("/admin", data={"password": PASSWORD}).status_code == 400  # no CSRF token
    assert not is_admin(client)


def test_login_sets_a_week_long_session_that_renews_on_every_visit(client):
    r = sign_in(client)
    assert r.status_code == 302 and r.headers["Location"] == "/"
    assert is_admin(client)
    expires = client.get_cookie("session").expires
    assert timedelta(days=6, hours=23) < expires - datetime.now(timezone.utc) <= timedelta(days=7)
    assert "HttpOnly" in r.headers["Set-Cookie"] and "SameSite=Lax" in r.headers["Set-Cookie"]


@pytest.mark.parametrize("target,expected", [
    ("/artist/vamvakaris-markos#alaniaris", "/artist/vamvakaris-markos#alaniaris"),
    ("//evil.example/x", "/"), ("/\\evil.example", "/"), ("https://evil.example", "/"), ("", "/"),
])
def test_next_only_accepts_same_site_paths(client, target, expected):
    assert sign_in(client, next=target).headers["Location"] == expected


def test_login_attempts_are_rate_limited(client):
    csrf = token(client)
    codes = [client.post("/admin", data={"csrf": csrf, "password": "x"}).status_code for _ in range(7)]
    assert codes[:5] == [401] * 5 and codes[-1] == 429


def test_logout_needs_the_token_and_ends_the_session(client):
    sign_in(client)
    assert client.post("/admin/logout").status_code == 400 and is_admin(client)
    r = client.post("/admin/logout", data={"csrf": token(client)})
    assert r.status_code == 302 and not is_admin(client)


def test_pdf_redirects_visitors_to_sign_in_whether_or_not_the_song_has_one(client):
    for song_id in (1, 3, 999999):  # has PDFs / has none / does not exist: same answer, nothing to probe
        r = client.get(f"/pdf/{song_id}/sheet")
        assert r.status_code == 302 and r.headers["Location"] == f"/admin?next=/pdf/{song_id}/sheet"
    assert "r2.test" not in client.get("/pdf/1/sheet").headers["Location"]


def test_admin_gets_a_presigned_url_named_after_the_current_song_and_artist(client, app):
    sign_in(client)
    song = app.extensions["catalog"].song_by_id[1]
    r = client.get("/pdf/1/sheet")
    assert r.status_code == 302 and r.headers["Location"].startswith("https://r2.test/pdf/1/sheet.pdf?name=")
    assert f"{song.en_name} - {song.artist.en_name}.pdf" in unquote(r.headers["Location"])
    assert "Tablature.pdf" in unquote(client.get("/pdf/1/tab").headers["Location"])
    assert r.headers["Cache-Control"] == "private, no-store"


def test_missing_keys_unknown_songs_and_bad_kinds_are_404_for_the_admin(client):
    sign_in(client)
    assert client.get("/pdf/2/tab").status_code == 404  # sheet only
    assert client.get("/pdf/3/sheet").status_code == 404  # no PDFs
    assert client.get("/pdf/999999/sheet").status_code == 404
    assert client.get("/pdf/1/mp3").status_code == 404


def test_unconfigured_storage_gives_a_generic_503(client, monkeypatch):
    def boom(*args, **kwargs):
        raise storage.StorageError("missing environment variables: R2_BUCKET")

    monkeypatch.setattr(storage, "presigned_url", boom)
    sign_in(client)
    r = client.get("/pdf/1/sheet")
    assert r.status_code == 503 and b"R2_BUCKET" not in r.data


def test_artist_page_is_the_same_for_everyone_and_never_touches_the_session(client, app):
    song = app.extensions["catalog"].song_by_id[1]
    url = f"/artist/{song.artist.slug}"
    anonymous = client.get(url)
    assert anonymous.headers.get("Set-Cookie") is None and "Cookie" not in anonymous.headers.get("Vary", "")
    assert f'data-sheet="/pdf/1/sheet"' in anonymous.get_data(as_text=True) and 'data-tab-pdf="/pdf/1/tab"' in anonymous.get_data(as_text=True)
    assert "pdf/1/sheet.pdf" not in anonymous.get_data(as_text=True)  # the R2 key never reaches the page
    sign_in(client)
    assert client.get(url).get_data() == anonymous.get_data()


def test_signed_in_admin_gets_no_cookie_on_public_or_static_responses(client):
    # A shared cache must never be able to store the admin's cookie next to a public page.
    sign_in(client)
    for url in ("/", "/artist/vamvakaris-markos", "/find?q=mou", "/healthz", "/images/vamvakaris-markos", "/static/css/styles.css"):
        r = client.get(url)
        assert r.status_code == 200 and "Set-Cookie" not in r.headers and "Cookie" not in r.headers.get("Vary", ""), url


def test_only_the_no_store_session_endpoint_renews_the_week(client):
    sign_in(client)
    r = client.get("/admin/session")
    assert "session=" in r.headers["Set-Cookie"] and r.headers["Cache-Control"] == "private, no-store"
    assert "session=" in client.get("/pdf/1/sheet").headers["Set-Cookie"]


def test_changing_the_password_signs_everybody_out(pdf_db, client):
    sign_in(client)
    other = create_app(pdf_db, secret_key="test-key", admin_password="a different password")
    twin = other.test_client()
    twin.set_cookie("session", client.get_cookie("session").value)
    assert is_admin(client) and not is_admin(twin)


def test_a_long_password_still_works(pdf_db, monkeypatch):
    monkeypatch.setenv("DEV_SERVER", "1")
    long_password = "x" * 300
    client = create_app(pdf_db, secret_key="test-key", admin_password=long_password).test_client()
    assert sign_in(client, long_password).status_code == 302 and is_admin(client)


def test_session_cookie_is_secure_unless_running_the_dev_server(pdf_db, monkeypatch):
    monkeypatch.delenv("DEV_SERVER", raising=False)
    assert create_app(pdf_db, secret_key="test-key", admin_password=PASSWORD).config["SESSION_COOKIE_SECURE"] is True
    monkeypatch.setenv("DEV_SERVER", "1")
    assert create_app(pdf_db, secret_key="test-key", admin_password=PASSWORD).config["SESSION_COOKIE_SECURE"] is False


def test_pdf_requests_are_rate_limited(client):
    sign_in(client)
    codes = [client.get("/pdf/1/sheet").status_code for _ in range(62)]
    assert codes[:60] == [302] * 60 and codes[-1] == 429


def test_content_disposition_cannot_be_injected_into():
    header = storage.content_disposition('x"; evil=1\r\nSet-Cookie: a=b - Μαρκος.pdf')
    assert "\r" not in header and "\n" not in header and header.count('"') == 2
    assert header.startswith('inline; filename="')
