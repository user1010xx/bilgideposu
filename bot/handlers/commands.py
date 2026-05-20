from telegram import Update
from telegram.ext import ContextTypes

from bot.cache import invalidate
from bot.config import QUESTIONS_PAGE_SIZE
from bot.database import (
    all_questions_for_group,
    delete_by_id,
    delete_by_question_text,
    get_question_by_list_index,
    search_questions,
    update_answer,
)
from bot.utils.auth import is_admin, is_allowed_group, is_group_chat, reject_private
from bot.utils.messages import escape_html, send_long_text
from bot.utils.text import find_best_match, normalize_text

HELP_TEXT = (
    "📖 <b>Bilgi Botu komutları</b>\n\n"
    "<b>Herkes:</b>\n"
    "• Soru yaz → otomatik cevap\n"
    "• /sorular [sayfa] — kayıtlı sorular\n"
    "• /bul &lt;kelime&gt; — soru veya cevapta ara\n\n"
    "<b>Yetkililer:</b>\n"
    "• /ekle &lt;soru&gt; → medya (isteğe bağlı) → cevap\n"
    "• /guncelle &lt;no&gt; &lt;yeni cevap&gt;\n"
    "• /sil &lt;no&gt; veya /sil &lt;soru metni&gt;\n"
    "• /iptal — ekleme iptal"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_private(update):
        return
    if not is_group_chat(update) or not is_allowed_group(update):
        return
    await update.message.reply_html(HELP_TEXT)


async def cmd_yardim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_sorular(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_private(update):
        return
    if not is_group_chat(update) or not is_allowed_group(update):
        return

    page = 1
    if context.args:
        if not context.args[0].isdigit():
            await update.message.reply_text("Kullanım: /sorular veya /sorular 2")
            return
        page = int(context.args[0])
        if page < 1:
            await update.message.reply_text("Sayfa numarası 1 veya büyük olmalı.")
            return

    group_id = update.effective_chat.id
    rows = all_questions_for_group(group_id)
    if not rows:
        await update.message.reply_text("Henüz kayıtlı soru yok.")
        return

    total_pages = max(1, (len(rows) + QUESTIONS_PAGE_SIZE - 1) // QUESTIONS_PAGE_SIZE)
    if page > total_pages:
        await update.message.reply_text(f"En fazla {total_pages} sayfa var.")
        return

    start = (page - 1) * QUESTIONS_PAGE_SIZE
    chunk = rows[start : start + QUESTIONS_PAGE_SIZE]

    lines = [
        f"📋 <b>Kayıtlı sorular</b> — sayfa {page}/{total_pages} "
        f"(toplam {len(rows)})\n"
    ]
    for i, row in enumerate(chunk, start=start + 1):
        media = f" [{row.media_type}]" if row.media_type else ""
        lines.append(f"{i}. {escape_html(row.question_text)}{media}")

    if total_pages > 1:
        lines.append(f"\nSonraki: /sorular {page + 1}" if page < total_pages else "")

    await send_long_text(update, context, "\n".join(lines))


async def cmd_bul(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_private(update):
        return
    if not is_group_chat(update) or not is_allowed_group(update):
        return

    if not context.args:
        await update.message.reply_text("Kullanım: /bul <kelime>")
        return

    keyword = " ".join(context.args).strip()
    if len(keyword) < 2:
        await update.message.reply_text("En az 2 karakter girin.")
        return

    group_id = update.effective_chat.id
    rows = search_questions(group_id, normalize_text(keyword))
    if not rows:
        await update.message.reply_text(f'"{keyword}" içeren kayıt bulunamadı.')
        return

    lines = [f'🔍 "<b>{escape_html(keyword)}</b>" — {len(rows)} sonuç:\n']
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. {escape_html(row.question_text)}")

    await send_long_text(update, context, "\n".join(lines))


def _resolve_question_for_admin(group_id, arg: str):
    if arg.isdigit():
        return get_question_by_list_index(group_id, int(arg))

    rows = all_questions_for_group(group_id)
    candidates = [(r.id, r.normalized_question) for r in rows]
    match = find_best_match(arg, candidates)
    if match:
        qid = match[0]
        return next((r for r in rows if r.id == qid), None)
    return None


async def cmd_sil(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_private(update):
        return
    if not is_group_chat(update) or not is_allowed_group(update):
        return
    if not is_admin(update):
        await update.message.reply_text("Bu komut yalnızca yetkililer içindir.")
        return

    if not context.args:
        await update.message.reply_text(
            "Kullanım:\n"
            "• /sil 3 — listedeki 3. soruyu sil\n"
            "• /sil soru metni — metinle sil"
        )
        return

    group_id = update.effective_chat.id
    arg = " ".join(context.args).strip()

    if arg.isdigit():
        row = get_question_by_list_index(group_id, int(arg))
        if not row:
            await update.message.reply_text("Bu numarada soru yok. /sorular ile listeleyin.")
            return
        delete_by_id(group_id, row.id)
        invalidate(group_id)
        await update.message.reply_text(f"Silindi (#{arg}): {row.question_text}")
        return

    deleted = delete_by_question_text(group_id, arg)
    if deleted:
        invalidate(group_id)
        await update.message.reply_text(f"Silindi ({deleted} kayıt).")
        return

    row = _resolve_question_for_admin(group_id, arg)
    if row:
        delete_by_id(group_id, row.id)
        invalidate(group_id)
        await update.message.reply_text(f"Silindi (eşleşme): {row.question_text}")
        return

    await update.message.reply_text("Silinecek soru bulunamadı.")


async def cmd_guncelle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_private(update):
        return
    if not is_group_chat(update) or not is_allowed_group(update):
        return
    if not is_admin(update):
        await update.message.reply_text("Bu komut yalnızca yetkililer içindir.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Kullanım:\n"
            "• /guncelle 3 yeni cevap metni\n"
            "• /guncelle soru metni yeni cevap"
        )
        return

    group_id = update.effective_chat.id

    if context.args[0].isdigit():
        index = int(context.args[0])
        new_answer = " ".join(context.args[1:]).strip()
        row = get_question_by_list_index(group_id, index)
        if not row:
            await update.message.reply_text("Bu numarada soru yok.")
            return
        question_label = f"#{index}"
    else:
        full = " ".join(context.args).strip()
        rows = all_questions_for_group(group_id)
        matched_row = None
        matched_answer = None
        for row in rows:
            q = row.question_text
            if full.startswith(q):
                rest = full[len(q) :].strip()
                if rest:
                    matched_row = row
                    matched_answer = rest
                    break
        if not matched_row:
            question_guess = context.args[0]
            row = _resolve_question_for_admin(group_id, question_guess)
            if row:
                matched_row = row
                matched_answer = " ".join(context.args[1:]).strip()
        if not matched_row or not matched_answer:
            await update.message.reply_text("Güncellenecek soru veya yeni cevap bulunamadı.")
            return
        row = matched_row
        new_answer = matched_answer
        question_label = row.question_text

    if not new_answer:
        await update.message.reply_text("Yeni cevap boş olamaz.")
        return

    update_answer(group_id, row.id, new_answer)
    invalidate(group_id)
    await update.message.reply_html(
        f"✅ Güncellendi ({escape_html(question_label)})\n"
        f"<b>Yeni cevap:</b> {escape_html(new_answer)}"
    )
