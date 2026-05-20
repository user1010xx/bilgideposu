from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.cache import invalidate
from bot.database import DuplicateQuestionError, add_question
from bot.utils.auth import is_admin, is_allowed_group, is_group_chat, reject_private
from bot.utils.messages import escape_html
from bot.utils.text import normalize_text

WAITING_ANSWER = 1


def _clear_pending(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("pending_question", None)
    context.user_data.pop("pending_media_type", None)
    context.user_data.pop("pending_media_file_id", None)
    context.user_data.pop("pending_group_id", None)


async def cmd_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await reject_private(update):
        return ConversationHandler.END
    if not is_group_chat(update) or not is_allowed_group(update):
        return ConversationHandler.END
    if not is_admin(update):
        await update.message.reply_text("Bu komut yalnızca yetkililer içindir.")
        return ConversationHandler.END

    if not context.args:
        await update.message.reply_text(
            "Kullanım: /ekle <soru metni>\n\n"
            "1) İsteğe bağlı fotoğraf/video gönderin\n"
            "2) Cevabı metin olarak yazın\n"
            "İptal: /iptal"
        )
        return ConversationHandler.END

    question_text = " ".join(context.args).strip()
    if len(question_text) < 3:
        await update.message.reply_text("Soru en az 3 karakter olmalı.")
        return ConversationHandler.END

    _clear_pending(context)
    context.user_data["pending_question"] = question_text
    context.user_data["pending_group_id"] = update.effective_chat.id

    await update.message.reply_html(
        f"Soru kaydedildi:\n<b>{escape_html(question_text)}</b>\n\n"
        "İsteğe bağlı: fotoğraf veya video gönderin.\n"
        "Son adım: cevabı yazın."
    )
    return WAITING_ANSWER


async def receive_media_or_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await reject_private(update):
        _clear_pending(context)
        return ConversationHandler.END
    if not is_group_chat(update) or not is_allowed_group(update):
        _clear_pending(context)
        return ConversationHandler.END
    if not is_admin(update):
        return ConversationHandler.END

    pending = context.user_data.get("pending_question")
    pending_group = context.user_data.get("pending_group_id")
    if not pending or pending_group != update.effective_chat.id:
        return ConversationHandler.END

    message = update.message

    if message.photo:
        photo = message.photo[-1]
        context.user_data["pending_media_type"] = "photo"
        context.user_data["pending_media_file_id"] = photo.file_id
        await message.reply_text("Fotoğraf eklendi. Şimdi cevabı yazın.")
        return WAITING_ANSWER

    if message.video:
        context.user_data["pending_media_type"] = "video"
        context.user_data["pending_media_file_id"] = message.video.file_id
        await message.reply_text("Video eklendi. Şimdi cevabı yazın.")
        return WAITING_ANSWER

    if message.document and message.document.mime_type:
        mime = message.document.mime_type
        if mime.startswith("image/"):
            context.user_data["pending_media_type"] = "photo"
            context.user_data["pending_media_file_id"] = message.document.file_id
            await message.reply_text("Görsel eklendi. Şimdi cevabı yazın.")
            return WAITING_ANSWER
        if mime.startswith("video/"):
            context.user_data["pending_media_type"] = "video"
            context.user_data["pending_media_file_id"] = message.document.file_id
            await message.reply_text("Video eklendi. Şimdi cevabı yazın.")
            return WAITING_ANSWER

    if not message.text or message.text.startswith("/"):
        await message.reply_text("Lütfen cevabı düz metin olarak yazın.")
        return WAITING_ANSWER

    answer_text = message.text.strip()
    if not answer_text:
        await message.reply_text("Cevap boş olamaz.")
        return WAITING_ANSWER

    group_id = update.effective_chat.id
    user_id = update.effective_user.id

    try:
        add_question(
            group_id=group_id,
            question_text=pending,
            normalized_question=normalize_text(pending),
            answer_text=answer_text,
            created_by=user_id,
            media_type=context.user_data.get("pending_media_type"),
            media_file_id=context.user_data.get("pending_media_file_id"),
        )
    except DuplicateQuestionError:
        await message.reply_text("Bu soru zaten kayıtlı. Önce /sil ile kaldırın veya /guncelle kullanın.")
        _clear_pending(context)
        return ConversationHandler.END

    invalidate(group_id)
    _clear_pending(context)
    await message.reply_html(
        f"✅ Soru-cevap eklendi.\n\n"
        f"<b>S:</b> {escape_html(pending)}\n"
        f"<b>C:</b> {escape_html(answer_text)}"
    )
    return ConversationHandler.END


async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_pending(context)
    await update.message.reply_text("Ekleme iptal edildi.")
    return ConversationHandler.END


def build_add_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("ekle", cmd_ekle)],
        states={
            WAITING_ANSWER: [
                MessageHandler(
                    filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND,
                    receive_media_or_answer,
                ),
            ],
        },
        fallbacks=[CommandHandler("iptal", cancel_add)],
        conversation_timeout=600,
        per_chat=True,
        per_user=True,
        name="add_question_flow",
    )
