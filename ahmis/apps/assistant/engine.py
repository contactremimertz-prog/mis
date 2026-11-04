"""Moteur de l'assistant : correspondance par mots-clés, sans génération de texte."""
import re
import unicodedata

from django.urls import NoReverseMatch, reverse

from .kb import KB, LANGS

MAX_QUERY = 300


def normalize(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", text.replace("ß", "ss"))


STOP = set("le la les un une des de du et ou a au aux en pour que qui quoi comment est je me mon ma mes on il elle "
           "the a an of to and or is i my how do what when why can in on for "
           "el los las unos de y o es mi como que cuando por en para "
           "der die das ein eine und oder ist ich mein wie was wann warum kann in auf fur zu".split())

_INDEX = []
for _e in KB:
    words = set()
    for _l in LANGS:
        words.update(w for w in normalize(_e[_l]["kw"] + " " + _e[_l]["q"]) if w not in STOP)
    _INDEX.append((_e, words))


def _score(tokens, words):
    score = 0
    for t in tokens:
        if t in words:
            score += 2
        elif len(t) >= 4 and any(w.startswith(t[:5]) or t.startswith(w[:5]) for w in words if len(w) >= 4):
            score += 1
    return score


def _entry(e, lang, user):
    loc = e.get(lang) or e["fr"]
    url = None
    if e.get("url") and (not e.get("perm") or user.has_perm(e["perm"])):
        try:
            url = reverse(e["url"])
        except NoReverseMatch:
            url = None
    tuto = None
    if e.get("tuto"):
        tuto = reverse("help_page", args=[e["tuto"]])
    return {"id": e["id"], "q": loc["q"], "a": loc["a"], "url": url, "tuto": tuto, "refusal": bool(e.get("refusal"))}


def answer(query, lang, user):
    """Réponse validée la plus proche, ou None ; et jusqu'à 3 suggestions."""
    lang = lang if lang in LANGS else "fr"
    tokens = [t for t in normalize((query or "")[:MAX_QUERY]) if t not in STOP]
    ranked = sorted(((_score(tokens, words), i, e) for i, (e, words) in enumerate(_INDEX)), key=lambda r: (-r[0], r[1]))
    best = ranked[0] if ranked and ranked[0][0] >= 2 else None
    suggestions = [_entry(e, lang, user) for s, _, e in ranked[1:4] if s >= 2] if best else []
    return (_entry(best[2], lang, user) if best else None), suggestions


def questions(lang, user):
    lang = lang if lang in LANGS else "fr"
    return [_entry(e, lang, user) for e in KB]
