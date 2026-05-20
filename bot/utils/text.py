import difflib
import re
import unicodedata

from bot.config import MATCH_THRESHOLD, MIN_QUERY_WORDS


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def query_word_count(text: str) -> int:
    return len(normalize_text(text).split())


def _token_set_ratio(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 100.0

    tokens_left = set(left.split())
    tokens_right = set(right.split())
    intersection = tokens_left & tokens_right
    if not intersection:
        return difflib.SequenceMatcher(None, left, right).ratio() * 100

    sorted_intersection = " ".join(sorted(intersection))
    ratio_left = difflib.SequenceMatcher(None, left, sorted_intersection).ratio()
    ratio_right = difflib.SequenceMatcher(None, right, sorted_intersection).ratio()
    ratio_full = difflib.SequenceMatcher(None, left, right).ratio()
    return max(ratio_left, ratio_right, ratio_full) * 100


def find_best_match(query, candidates):
    """candidates: [(id, normalized_question), ...]"""
    if not candidates:
        return None

    normalized = normalize_text(query)
    if not normalized:
        return None
    if query_word_count(query) < MIN_QUERY_WORDS:
        return None

    best_id = None
    best_norm = ""
    best_score = 0.0

    for cid, norm in candidates:
        score = _token_set_ratio(normalized, norm)
        if score > best_score:
            best_score = score
            best_id = cid
            best_norm = norm

    if best_id is None or best_score < MATCH_THRESHOLD:
        return None
    return best_id, best_norm, best_score
