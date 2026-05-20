import logging
import os
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.config import ADMIN_IDS, BOT_TOKEN
from bot.database import init_db
from bot.handlers.add_flow import build_add_conversation
from bot.handlers.commands import (
    cmd_bul,
    cmd_guncelle,
    cmd_sil,
    cmd_sorular,
    cmd_start,
    cmd_yardim,
)
from bot.handlers.qa import answer_question
from bot.singleton import ensure_single_instance
from bot.utils.auth import notify_private_only_groups, reject_private

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def ignore_private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_private(update):
        await notify_private_only_groups(update)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("İşlenmeyen hata: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Bir hata oluştu. Lütfen tekrar deneyin."
            )
        except Exception:
            logger.exception("Hata mesajı gönderilemedi.")


def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN tanımlı değil. .env dosyasını kontrol edin.")
        sys.exit(1)

    if not ADMIN_IDS:
        logger.warning("ADMIN_IDS boş — yetkili komutlar devre dışı.")

    ensure_single_instance()
    init_db()
    logger.info("Veritabanı hazır.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)

    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, ignore_private), group=-1)

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("yardim", cmd_yardim))
    app.add_handler(CommandHandler("sorular", cmd_sorular))
    app.add_handler(CommandHandler("bul", cmd_bul))
    app.add_handler(CommandHandler("sil", cmd_sil))
    app.add_handler(CommandHandler("guncelle", cmd_guncelle))
    app.add_handler(build_add_conversation())

    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            answer_question,
        ),
        group=1,
    )

    logger.info("Bot başlatılıyor...")
    app.run_polling(allowed_updates=["message"], drop_pending_updates=True)


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    port = os.getenv("PORT")
    if port:
        logger.info("Railway PORT=%s (polling modu)", port)
    main()
