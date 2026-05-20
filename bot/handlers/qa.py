import time

from telegram import Update
from telegram.ext import ContextTypes

from bot.cache import get_cached, invalidate, set_cached
from bot.config import COOLDOWN_SECONDS
from bot.database import all_questions_for_group
from bot.utils.auth import is_allowed_group, is_group_chat, reject_private
from bot.utils.emoji import answer_emoji
from bot.utils.messages import escape_html, send_long_text
from bot.utils.text import find_best_match

_cooldowns: dict[tuple[int, int], float] = {}


def _get_group_questions(group_id: int):
    cached = get_cached(group_id)
    if cached is not None:
        return cached
    rows = all_questions_for_group(group_id)
    set_cached(group_id, rows)
    return rows


def _on_cooldown(group_id: int, user_id: int) -> bool:
    key = (group_id, user_id)
    last = _cooldowns.get(key, 0)
    if time.time() - last < COOLDOWN_SECONDS:
        return True
    _cooldowns[key] = time.time()
    return False


async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_private(update):
        return
    if not is_group_chat(update) or not is_allowed_group(update):
        return

    message = update.message
    if not message or not message.text:
        return
    if message.text.startswith("/"):
        return
    if message.from_user and message.from_user.is_bot:
        return

    user = message.from_user
    if user and _on_cooldown(update.effective_chat.id, user.id):
        return

    query = message.text.strip()
    if len(query) < 3:
        return

    group_id = update.effective_chat.id
    rows = _get_group_questions(group_id)
    if not rows:
        return

    candidates = [(row.id, row.normalized_question) for row in rows]
    match = find_best_match(query, candidates)
    if not match:
        return

    qid, _, _ = match
    row = next((r for r in rows if r.id == qid), None)
    if not row:
        return

    icon = answer_emoji(row.question_text, row.answer_text)
    await send_long_text(
        update,
        context,
        f"{icon} {escape_html(row.answer_text)}",
        reply_to_message_id=message.message_id,
    )

    if row.media_file_id and row.media_type == "photo":
        await context.bot.send_photo(
            chat_id=group_id,
            photo=row.media_file_id,
            reply_to_message_id=message.message_id,
        )
    elif row.media_file_id and row.media_type == "video":
        await context.bot.send_video(
            chat_id=group_id,
            video=row.media_file_id,
            reply_to_message_id=message.message_id,
        )


def clear_group_cache(group_id: int) -> None:
    invalidate(group_id)
