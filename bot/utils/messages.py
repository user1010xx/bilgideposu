from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.config import MAX_MESSAGE_LENGTH


async def send_long_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    *,
    reply_to_message_id=None,
) -> None:
    """Telegram 4096 sınırını aşan metinleri parçalayarak gönderir."""
    if not text:
        return

    chat_id = update.effective_chat.id
    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= MAX_MESSAGE_LENGTH:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, MAX_MESSAGE_LENGTH)
        if split_at < MAX_MESSAGE_LENGTH // 2:
            split_at = remaining.rfind("\n", 0, MAX_MESSAGE_LENGTH)
        if split_at < MAX_MESSAGE_LENGTH // 2:
            split_at = remaining.rfind(" ", 0, MAX_MESSAGE_LENGTH)
        if split_at < 1:
            split_at = MAX_MESSAGE_LENGTH
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    message = update.message
    for i, chunk in enumerate(chunks):
        if i == 0 and message and reply_to_message_id is None:
            await message.reply_html(chunk)
            continue
        if i == 0 and reply_to_message_id:
            await context.bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=reply_to_message_id,
            )
            continue
        await context.bot.send_message(
            chat_id=chat_id,
            text=chunk,
            parse_mode=ParseMode.HTML,
        )


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
