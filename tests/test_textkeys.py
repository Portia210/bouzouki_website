import pytest

from textkeys import make_slug, phonetic_key


@pytest.mark.parametrize("variants", [
    ["mou", "moy", "μου", "Μου"],
    ["mavra matia", "mayra matia", "μαύρα μάτια", "mavramatia"],
    ["Aggelokamomeni", "angelokamomeni", "αγγελοκαμωμένη"],
    ["Giannis", "Yiannis", "Yannis", "Γιάννης"],
    ["Pseytikos Ntoynias", "psefticos dounias", "ψεύτικος ντουνιάς"],
    ["Zeimpekiko", "zeibekiko", "ζεϊμπέκικο"],
])
def test_spelling_variants_share_a_key(variants):
    assert len({phonetic_key(v) for v in variants}) == 1


def test_different_words_keep_different_keys():
    assert phonetic_key("kardia") != phonetic_key("matia")


def test_every_song_matches_its_greek_name(catalog):
    bad = [s.en_name for s in catalog.songs if phonetic_key(s.en_name) != phonetic_key(s.gr_name)]
    assert len(bad) <= len(catalog.songs) * 0.01, bad[:10]


def test_slug_is_short_ascii_and_skips_filler_words():
    assert make_slug("An Theleis Na Me Deis Gampro") == "theleis-deis-gampro"
    assert make_slug("Aggelokamomeni Moy") == "aggelokamomeni"
    assert make_slug("Vamvakaris Markos") == "vamvakaris-markos"
    assert make_slug("O Ti") == "o-ti"  # never empty, even if everything is filler
    assert make_slug("") == "item"
    assert len(make_slug("Kalimera Sas Kyrie Mpampa Kai Ola Ta Alla")) <= 26
