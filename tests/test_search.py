import pytest


def songs(index, term, **kw):
    return [s.en_name for s in index.search(term, **kw)[1]]


@pytest.mark.parametrize("term, expected", [
    ("mou", "Aggelokamomeni Moy"),
    ("angelokamomeni", "Aggelokamomeni Moy"),
    ("mavra matia", "Mayra Matia Mayra Frydia"),
    ("αγγελοκαμωμένη", "Aggelokamomeni Moy"),
    ("psefticos dounias", "Pseytikos Ntoynias"),
    ("s ayton", "S' Ayton Ton Kosmo Ton Kako"),
])
def test_finds_song_despite_spelling(index, term, expected):
    assert expected in songs(index, term, song_limit=20)


def test_typo_falls_back_to_closest_word(index):
    assert "Aggelokamomeni Moy" in songs(index, "angelokamomenni")


def test_artist_name_finds_artist_and_their_songs(index):
    artists, found = index.search("tsitsanis")
    assert artists[0].en_name == "Vasilis Tsitsanis"
    assert found and all(s.artist.en_name == "Vasilis Tsitsanis" for s in found)


def test_artist_filter_limits_songs(index, catalog):
    artist = catalog.artist_by_slug["vamvakaris-markos"]
    artists, found = index.search("mou", artist=artist, song_limit=200)
    assert artists == [] and found
    assert all(s.artist is artist for s in found)


def test_exact_title_ranks_first(index):
    assert songs(index, "alaniaris")[0] == "Alaniaris"


@pytest.mark.parametrize("term", ["", "  ", "!!!", "x" * 500])
def test_junk_queries_return_nothing_or_fast(index, term):
    artists, found = index.search(term)
    assert len(artists) <= 4 and len(found) <= 8
