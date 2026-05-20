"""Soru/cevap metnine göre sade bir yanıt emojisi seçer."""

from bot.utils.text import normalize_text

_DEFAULT = "✅"

_RULES = (
    (("uzunluk", "santim", "metre", "kilometre", "genislik", "yukseklik", "derinlik", "agirlik"), "📏"),
    (("nufus", "milyon", "milyar", "yuzde"), "🔢"),
    (("tarih", "hangi yil",), "📅"),
    (("nerede", "baskent", "konum", "adres"), "📍"),
    (("kimdir", "baskan",), "👤"),
    (("fiyat", "dolar", "euro", "ucret", "maas", "maliyet"), "💰"),
    (("sicaklik", "derece",), "🌡️"),
    (("renk",), "🎨"),
)


def _contains_word(haystack: str, keyword: str) -> bool:
    if keyword in haystack.split():
        return True
    return f" {keyword} " in f" {haystack} "


def answer_emoji(question: str, answer: str = "") -> str:
    combined = normalize_text(f"{question} {answer}")
    if not combined:
        return _DEFAULT

    for keywords, emoji in _RULES:
        if any(_contains_word(combined, kw) for kw in keywords):
            return emoji
    if _contains_word(combined, "boy") or _contains_word(combined, "kilo"):
        return "📏"
    if _contains_word(combined, "sayi") or _contains_word(combined, "adet"):
        return "🔢"
    if _contains_word(combined, "kim"):
        return "👤"
    if _contains_word(combined, "nerede") or _contains_word(combined, "sehir"):
        return "📍"
    return _DEFAULT
