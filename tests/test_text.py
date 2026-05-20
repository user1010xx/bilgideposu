from bot.utils.emoji import answer_emoji
from bot.utils.text import find_best_match, normalize_text, query_word_count


def test_normalize_turkish():
    assert normalize_text("Türkiye'nin Nüfusu") == "turkiye nin nufusu"


def test_query_word_count():
    assert query_word_count("boyu kaç") == 2
    assert query_word_count("nedir") == 1


def test_find_best_match_min_words():
    candidates = [(1, "boyu kac santim")]
    assert find_best_match("kaç", candidates) is None
    match = find_best_match("boyu kaç santim", candidates)
    assert match is not None
    assert match[0] == 1


def test_answer_emoji_measurement():
    assert answer_emoji("boyu kaç santim", "2 santim") == "📏"


def test_answer_emoji_default():
    assert answer_emoji("rastgele konu", "cevap") == "✅"
