import pytest

from bot.database import (
    DuplicateQuestionError,
    add_question,
    delete_by_id,
    init_db,
    list_questions,
    question_exists,
    search_questions,
    update_answer,
)
from bot.utils.text import normalize_text


@pytest.fixture(autouse=True)
def fresh_db():
    init_db()
    yield


def test_add_and_duplicate():
    gid = -1001
    add_question(
        group_id=gid,
        question_text="Test sorusu",
        normalized_question=normalize_text("Test sorusu"),
        answer_text="Test cevap",
        created_by=1,
    )
    assert question_exists(gid, normalize_text("Test sorusu"))
    with pytest.raises(DuplicateQuestionError):
        add_question(
            group_id=gid,
            question_text="Test sorusu",
            normalized_question=normalize_text("Test sorusu"),
            answer_text="Baska",
            created_by=1,
        )


def test_search_in_answer():
    gid = -1002
    add_question(
        group_id=gid,
        question_text="Baskent neresi",
        normalized_question=normalize_text("Baskent neresi"),
        answer_text="Ankara",
        created_by=1,
    )
    rows = search_questions(gid, "ankara")
    assert len(rows) == 1


def test_update_and_delete():
    gid = -1003
    row = add_question(
        group_id=gid,
        question_text="Silinecek",
        normalized_question=normalize_text("Silinecek"),
        answer_text="Eski",
        created_by=1,
    )
    assert update_answer(gid, row.id, "Yeni")
    rows = list_questions(gid)
    assert rows[0].answer_text == "Yeni"
    assert delete_by_id(gid, row.id)
    assert list_questions(gid) == []
