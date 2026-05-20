from telegram import Update

from bot.config import ADMIN_IDS, ADMIN_USERNAMES, ALLOWED_GROUP_IDS


def is_group_chat(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type in ("group", "supergroup")


def is_allowed_group(update: Update) -> bool:
    if ALLOWED_GROUP_IDS is None:
        return True
    chat = update.effective_chat
    return chat is not None and chat.id in ALLOWED_GROUP_IDS


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
