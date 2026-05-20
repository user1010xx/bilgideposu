from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    or_,
    select,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from bot.config import DATABASE_URL, MAX_NORMALIZED_LENGTH

Base = declarative_base()


class DuplicateQuestionError(Exception):
    """Aynı grupta normalize edilmiş soru zaten kayıtlı."""


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, index=True, nullable=False)
    question_text = Column(Text, nullable=False)
    normalized_question = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    media_type = Column(String(16), nullable=True)
    media_file_id = Column(String(256), nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("group_id", "normalized_question", name="uq_group_question"),
        Index("ix_questions_group_norm", "group_id", "normalized_question"),
    )


_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


def _trim_normalized(value: str) -> str:
    if len(value) <= MAX_NORMALIZED_LENGTH:
        return value
    return value[:MAX_NORMALIZED_LENGTH]


def question_exists(group_id, normalized_question: str) -> bool:
    norm = _trim_normalized(normalized_question)
    with get_session() as session:
        row = session.scalar(
            select(Question.id).where(
                Question.group_id == group_id,
                Question.normalized_question == norm,
            )
        )
        return row is not None


def add_question(
    *,
    group_id,
    question_text,
    normalized_question,
    answer_text,
    created_by,
    media_type=None,
    media_file_id=None,
):
    norm = _trim_normalized(normalized_question)
    if question_exists(group_id, norm):
        raise DuplicateQuestionError("Bu soru zaten kayıtlı.")

    with get_session() as session:
        row = Question(
            group_id=group_id,
            question_text=question_text,
            normalized_question=norm,
            answer_text=answer_text,
            created_by=created_by,
            media_type=media_type,
            media_file_id=media_file_id,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row


def get_question_by_id(group_id, question_id):
    with get_session() as session:
        row = session.get(Question, question_id)
        if row and row.group_id == group_id:
            return row
        return None


def get_question_by_list_index(group_id, index: int):
    """1 tabanlı sıra numarası (/sorular listesi ile aynı)."""
    rows = list_questions(group_id)
    if 1 <= index <= len(rows):
        return rows[index - 1]
    return None


def delete_question(group_id, question_id):
    with get_session() as session:
        row = session.get(Question, question_id)
        if not row or row.group_id != group_id:
            return False
        session.delete(row)
        session.commit()
        return True


def delete_by_question_text(group_id, question_text):
    with get_session() as session:
        rows = session.scalars(
            select(Question).where(
                Question.group_id == group_id,
                Question.question_text == question_text,
            )
        ).all()
        for row in rows:
            session.delete(row)
        session.commit()
        return len(rows)


def delete_by_id(group_id, question_id):
    return delete_question(group_id, question_id)


def update_answer(group_id, question_id, new_answer: str):
    with get_session() as session:
        row = session.get(Question, question_id)
        if not row or row.group_id != group_id:
            return False
        row.answer_text = new_answer
        session.commit()
        return True


def list_questions(group_id):
    with get_session() as session:
        return list(
            session.scalars(
                select(Question)
                .where(Question.group_id == group_id)
                .order_by(Question.id.asc())
            ).all()
        )


def search_questions(group_id, keyword):
    pattern = f"%{keyword.lower()}%"
    with get_session() as session:
        return list(
            session.scalars(
                select(Question)
                .where(
                    Question.group_id == group_id,
                    or_(
                        Question.normalized_question.like(pattern),
                        func.lower(Question.answer_text).like(pattern),
                        func.lower(Question.question_text).like(pattern),
                    ),
                )
                .order_by(Question.id.asc())
            ).all()
        )


def all_questions_for_group(group_id):
    return list_questions(group_id)
