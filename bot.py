"""
Rencong Showroom KL — Telegram Lead Capture Bot
================================================
Qualify prospek → Auto-save ke Google Sheets
"""

import logging
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN   = "8961374336:AAEskXQelunCbhuMp0PkT6G_468pjPSGDig"
SHEET_ID    = "1NWB4qwpDR6PTmS49vVX4eEha2XlYLzmE8ujFwQ4V-e0"
SHEET_NAME  = "📋 Leads Database"
CREDS_FILE  = "credentials.json"

# Telegram ID owner — untuk notif lead baru
# Dapatkan ID kau dengan chat @userinfobot di Telegram
OWNER_IDS = [
    6320227217,  # Fajar — Rencong Showroom KL
]

# Conversation states
(
    NAMA, HP, EMAIL, PEKERJAAN,
    PENDAPATAN, BUDGET, JENIS, KEPERLUAN, CONFIRM
) = range(9)

# ── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)


# ── GOOGLE SHEETS ─────────────────────────────────────────────────────────────
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)


async def notify_owner(bot, data: dict):
    """Hantar notif ke owner bila lead baru masuk."""
    msg = (
        f"🔔 *LEAD BARU MASUK!*\n"
        f"{'─' * 26}\n"
        f"👤 *Nama:* {data.get('nama', '—')}\n"
        f"📱 *No HP:* {data.get('hp', '—')}\n"
        f"💼 *Pekerjaan:* {data.get('pekerjaan', '—')}\n"
        f"💳 *Budget:* {data.get('budget', '—')}\n"
        f"🚗 *Jenis:* {data.get('jenis', '—')}\n"
        f"🎯 *Keperluan:* {data.get('keperluan', '—')}\n"
        f"{'─' * 26}\n"
        f"⚡ _Hubungi dalam masa 24 jam!_"
    )
    for owner_id in OWNER_IDS:
        try:
            await bot.send_message(chat_id=owner_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            log.error(f"Notif owner failed: {e}")


def save_lead(data: dict):
    sheet = get_sheet()
    now   = datetime.now().strftime("%d/%m/%Y  %H:%M")
    row   = [
        now,
        data.get("nama", "—"),
        data.get("hp", "—"),
        data.get("email", "—"),
        data.get("pekerjaan", "—"),
        data.get("pendapatan", "—"),
        data.get("budget", "—"),
        data.get("jenis", "—"),
        "—",                          # Kereta Diminati — diisi dari web
        data.get("keperluan", "—"),
        "🟡  Warm Lead",              # Default status
        "Hubungi Hari Ini",           # Default tindakan
        f"Lead dari Telegram Bot. Kereta: {data.get('jenis','—')}",
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")
    log.info(f"Lead saved: {data.get('nama')} | {data.get('hp')}")


# ── KEYBOARDS ─────────────────────────────────────────────────────────────────
def kb_pendapatan():
    return ReplyKeyboardMarkup([
        ["< RM 2,000", "RM 2,000 – 3,000"],
        ["RM 3,000 – 4,000", "RM 4,000 – 5,000"],
        ["RM 5,000+"],
    ], resize_keyboard=True, one_time_keyboard=True)

def kb_budget():
    return ReplyKeyboardMarkup([
        ["< RM 400/bln", "RM 400 – 600/bln"],
        ["RM 600 – 800/bln", "RM 800 – 1,000/bln"],
        ["RM 1,000+/bln"],
    ], resize_keyboard=True, one_time_keyboard=True)

def kb_jenis():
    return ReplyKeyboardMarkup([
        ["🚗 Sedan", "🚙 SUV / MPV"],
        ["🛻 Pickup / 4WD", "Tak pasti lagi"],
    ], resize_keyboard=True, one_time_keyboard=True)

def kb_confirm():
    return ReplyKeyboardMarkup([
        ["✅ Ya, hantar maklumat saya"],
        ["✏️ Tidak, saya nak betulkan"],
    ], resize_keyboard=True, one_time_keyboard=True)

def kb_remove():
    return ReplyKeyboardRemove()


# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    name = update.effective_user.first_name or "Sahabat"

    await update.message.reply_text(
        f"Assalamualaikum, {name}! 👋\n\n"
        f"Selamat datang ke *Rencong Showroom KL* 🚗\n"
        f"Kami pakar dalam kereta *sambung bayar* terbaik di KL.\n\n"
        f"Untuk bantu anda cari kereta yang sesuai, saya perlukan beberapa maklumat ringkas.\n"
        f"Tak sampai 2 minit! ⏱️\n\n"
        f"Boleh saya tahu *nama penuh* anda?",
        parse_mode="Markdown",
        reply_markup=kb_remove()
    )
    return NAMA


# ── CONVERSATION STEPS ────────────────────────────────────────────────────────
async def step_nama(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["nama"] = update.message.text.strip()
    await update.message.reply_text(
        f"Terima kasih, *{ctx.user_data['nama']}*! 😊\n\n"
        f"Boleh saya dapatkan *nombor telefon* anda?\n"
        f"_(Contoh: 012-3456789)_",
        parse_mode="Markdown"
    )
    return HP


async def step_hp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["hp"] = update.message.text.strip()
    await update.message.reply_text(
        f"Baik! Seterusnya, boleh bagi *alamat emel* anda?\n"
        f"_(Taip *skip* jika tiada)_",
        parse_mode="Markdown"
    )
    return EMAIL


async def step_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    ctx.user_data["email"] = "—" if val.lower() == "skip" else val
    await update.message.reply_text(
        f"Okay! Apa *pekerjaan* anda sekarang?\n"
        f"_(Contoh: Kakitangan kerajaan, Bekerja sendiri, Pelajar...)_",
        parse_mode="Markdown"
    )
    return PEKERJAAN


async def step_pekerjaan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pekerjaan"] = update.message.text.strip()
    await update.message.reply_text(
        f"Boleh saya tahu *anggaran pendapatan bulanan* anda?\n"
        f"_(Pilih dari butang di bawah)_",
        parse_mode="Markdown",
        reply_markup=kb_pendapatan()
    )
    return PENDAPATAN


async def step_pendapatan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pendapatan"] = update.message.text.strip()
    await update.message.reply_text(
        f"Berapa *ansuran bulanan* yang selesa untuk anda?\n",
        parse_mode="Markdown",
        reply_markup=kb_budget()
    )
    return BUDGET


async def step_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["budget"] = update.message.text.strip()
    await update.message.reply_text(
        f"Apa jenis kereta yang anda cari? 🚗",
        parse_mode="Markdown",
        reply_markup=kb_jenis()
    )
    return JENIS


async def step_jenis(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["jenis"] = update.message.text.strip()
    await update.message.reply_text(
        f"Soalan terakhir! 🎉\n\n"
        f"Untuk *tujuan apa* anda perlukan kereta ini?\n"
        f"_(Contoh: Pergi kerja, Keluarga, Hantar anak sekolah...)_",
        parse_mode="Markdown",
        reply_markup=kb_remove()
    )
    return KEPERLUAN


async def step_keperluan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["keperluan"] = update.message.text.strip()
    d = ctx.user_data

    summary = (
        f"📋 *Ringkasan Maklumat Anda*\n"
        f"{'─' * 30}\n"
        f"👤 *Nama:* {d.get('nama')}\n"
        f"📱 *No HP:* {d.get('hp')}\n"
        f"📧 *Email:* {d.get('email')}\n"
        f"💼 *Pekerjaan:* {d.get('pekerjaan')}\n"
        f"💰 *Pendapatan:* {d.get('pendapatan')}\n"
        f"💳 *Budget Ansuran:* {d.get('budget')}\n"
        f"🚗 *Jenis Kereta:* {d.get('jenis')}\n"
        f"🎯 *Keperluan:* {d.get('keperluan')}\n"
        f"{'─' * 30}\n\n"
        f"Adakah maklumat di atas *betul*?"
    )

    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=kb_confirm()
    )
    return CONFIRM


async def step_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ans = update.message.text.strip()

    if "Ya" in ans:
        try:
            save_lead(ctx.user_data)
            await notify_owner(ctx.bot, ctx.user_data)
            await update.message.reply_text(
                f"✅ *Terima kasih, {ctx.user_data.get('nama')}!*\n\n"
                f"Maklumat anda telah kami terima. "
                f"Pasukan kami akan menghubungi anda *dalam masa 24 jam* untuk cadangkan kereta terbaik mengikut bajet anda.\n\n"
                f"Sementara itu, anda boleh layari stok kami di:\n"
                f"🌐 [rencongshowroom.vercel.app](https://rencongshowroom.vercel.app)\n\n"
                f"Sebarang pertanyaan, taip /start untuk mulakan semula. 🚗",
                parse_mode="Markdown",
                reply_markup=kb_remove()
            )
        except Exception as e:
            log.error(f"Sheet error: {e}")
            await update.message.reply_text(
                f"✅ Maklumat diterima! Kami akan hubungi anda dalam masa 24 jam.\n\n"
                f"_(Nota sistem: Sila hubungi admin jika tiada respon)_",
                parse_mode="Markdown",
                reply_markup=kb_remove()
            )
        return ConversationHandler.END

    else:
        ctx.user_data.clear()
        await update.message.reply_text(
            f"Okay, kita mulakan semula! Boleh saya tahu *nama penuh* anda?",
            parse_mode="Markdown",
            reply_markup=kb_remove()
        )
        return NAMA


# ── /cancel ───────────────────────────────────────────────────────────────────
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Sesi dibatalkan. Taip /start bila anda bersedia. 👋",
        reply_markup=kb_remove()
    )
    return ConversationHandler.END


# ── FALLBACK ──────────────────────────────────────────────────────────────────
async def fallback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Taip /start untuk mulakan semula. 🚗"
    )


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAMA:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nama)],
            HP:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_hp)],
            EMAIL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_email)],
            PEKERJAAN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pekerjaan)],
            PENDAPATAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pendapatan)],
            BUDGET:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_budget)],
            JENIS:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_jenis)],
            KEPERLUAN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_keperluan)],
            CONFIRM:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    log.info("🚗 Rencong Showroom Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
