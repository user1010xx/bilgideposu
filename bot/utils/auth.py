from telegram import Update

from bot.config import (
    ADMIN_IDS,
    ADMIN_USERNAMES,
    ALLOWED_GROUP_IDS,
    ALLOWED_GROUP_NAMES,
)
from bot.utils.text import normalize_text


def is_group_chat(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type in ("group", "supergroup")


def is_allowed_group(update: Update) -> bool:
    """
    Grup kısıtı yoksa → tüm gruplar.
    ALLOWED_GROUP_IDS ve/veya ALLOWED_GROUP_NAMES tanımlıysa → en az biri eşleşmeli.
    """
    chat = update.effective_chat
    if chat is None:
        return False

    has_id_filter = ALLOWED_GROUP_IDS is not None
    has_name_filter = ALLOWED_GROUP_NAMES is not None

    if not has_id_filter and not has_name_filter:
        return True

    if has_id_filter and chat.id in ALLOWED_GROUP_IDS:
        return True

    if has_name_filter:
        title = normalize_text(chat.title or "")
        if title in ALLOWED_GROUP_NAMES:
            return True

    return False


def is_admin(update: Update) -> bool:
    user = update.effective_user
    if user is None:
        return False
    if user.id in ADMIN_IDS:
        return True
    if user.username and user.username.lower() in ADMIN_USERNAMES:
        return True
    return False


async def reject_private(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type == "private"


async def notify_private_only_groups(update: Update) -> None:
    if update.message:
        await update.message.reply_text(
            "Bu bot yalnızca eklendiği gruplarda çalışır. Özel mesajlara yanıt vermem."
        )
