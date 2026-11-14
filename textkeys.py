"""Text normalisation shared by search and slug generation.

Song names exist in Greek and in a hand-made Latin transliteration that is not
consistent (``Moy``/``Mou``, ``Mayra``/``Mavra``, ``Aggelos``/``Angelos``). Users
type yet another variant. ``phonetic_key`` maps all of them onto one coarse,
ASCII "sound" so they can be compared.
"""

import re
import unicodedata

_GREEK_TO_LATIN = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "ks",
    "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y",
    "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "o",
}
_GREEK_RE = re.compile("[" + "".join(_GREEK_TO_LATIN) + "]")

# Uppercase letters are placeholders for finished sounds, so later rules can't
# re-read them (e.g. the "i" produced by "ei" must not start a new "ai").
_DIGRAPHS = [
    ("ou", "U"), ("oy", "U"),
    ("ai", "E"), ("ei", "I"), ("oi", "I"), ("ui", "I"), ("yi", "I"),
    ("ay", "av"), ("au", "av"), ("ey", "ev"), ("eu", "ev"),
    ("th", "t"), ("ph", "f"), ("ch", "h"), ("kh", "h"),
    ("x", "ks"), ("mp", "b"), ("nt", "d"),
    ("ng", "g"), ("gk", "g"), ("gg", "g"), ("gh", "g"),
]
_SINGLES = str.maketrans({"y": "i", "u": "i", "w": "o", "j": "g", "c": "k", "q": "k",
                          "b": "v", "f": "v", "d": "t", "g": "k",
                          "U": "u", "I": "i", "E": "e"})
_WORD_INITIAL_Y = re.compile(r"\by(?=[aeiouIEU])")
_SILENT_I = re.compile(r"i(?=[aeou])")
_REPEATS = re.compile(r"(.)\1+")


def fold(text: str) -> str:
    """Lowercase, drop accents/diaeresis and punctuation; apostrophes split words."""
    text = unicodedata.normalize("NFD", text.lower().replace("'", " ").replace("’", " "))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zͰ-Ͽ\s]", "", text)


def _word_key(word: str) -> str:
    word = _GREEK_RE.sub(lambda m: _GREEK_TO_LATIN[m.group()], word)
    word = _WORD_INITIAL_Y.sub("g", word)
    for old, new in _DIGRAPHS:
        word = word.replace(old, new)
    word = word.translate(_SINGLES)
    word = _SILENT_I.sub("", word)
    return _REPEATS.sub(r"\1", word)


def phonetic_words(text: str) -> list[str]:
    """Phonetic key of each word of ``text`` (Greek or Latin script)."""
    return [k for k in (_word_key(w) for w in fold(text).split()) if k]


def phonetic_key(text: str) -> str:
    return "".join(phonetic_words(text))


_STOPWORDS = {"o", "i", "to", "ta", "tis", "ton", "tin", "na", "se", "me", "an", "ki",
              "kai", "sto", "ston", "stin", "moy", "soy", "mou", "sou", "mia", "ena",
              "ti", "pou", "poy", "den", "tha", "as", "ap", "apo", "gia", "pia"}


def make_slug(name: str, max_words: int = 3, max_len: int = 26) -> str:
    """Short URL slug from an English name: a few significant words, ASCII only."""
    words = re.sub(r"[^a-z0-9\s]", "", unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()).split()
    significant = [w for w in words if w not in _STOPWORDS] or words
    picked: list[str] = []
    for w in significant[:max_words]:
        if len("-".join(picked + [w])) > max_len and picked:
            break
        picked.append(w)
    return "-".join(picked)[:max_len].strip("-") or "item"
