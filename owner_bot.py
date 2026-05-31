"""
Rencong Showroom KL — Owner AI Assistant Bot
=============================================
Bot khas untuk owner semak leads, stok & dapat notif.
Hanya Telegram ID owner yang boleh akses.
"""

import logging
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Ganti dengan token bot BARU dari @BotFather untuk owner bot
OWNER_BOT_TOKEN = "8941315560:AAHcbkUmWGaUmL3Ezux2s0bcTX1jc4oeFug"

# Telegram user ID owner — dapatkan dengan chat @userinfobot
# Boleh tambah lebih dari satu ID jika ada staff
OWNER_IDS = [
    6320227217,  # Fajar — Rencong Showroom KL
]

SHEET_ID       = "1NWB4qwpDR6PTmS49vVX4eEha2XlYLzmE8ujFwQ4V-e0"
SHEET_LEADS    = "📋 Leads Database"
CREDS_FILE     = "credentials.json"

# Stok kereta dummy (dalam sistem real, ini dari sheet stok)
STOK_KERETA = [
    {"model": "Perodua Myvi 1.5 H",     "tahun": 2020, "km": "42,000", "ansuran": "RM 520", "deposit": "RM 2,500", "status": "✅ Tersedia"},
    {"model": "Honda HR-V 1.8 V",        "tahun": 2019, "km": "68,000", "ansuran": "RM 860", "deposit": "RM 4,000", "status": "✅ Tersedia"},
    {"model": "Toyota Vios 1.5 G",       "tahun": 2021, "km": "31,000", "ansuran": "RM 610", "deposit": "RM 3,000", "status": "⏳ Deposit Diambil"},
    {"model": "Proton X50 Standard",     "tahun": 2021, "km": "55,000", "ansuran": "RM 790", "deposit": "RM 3,500", "status": "✅ Tersedia"},
    {"model": "Perodua Bezza 1.3 AV",    "tahun": 2022, "km": "28,000", "ansuran": "RM 430", "deposit": "RM 2,000", "status": "✅ Tersedia"},
    {"model": "Honda BR-V 1.5 V",        "tahun": 2018, "km": "88,000", "ansuran": "RM 680", "deposit": "RM 3,000", "status": "✅ Tersedia"},
    {"model": "Proton Saga 1.3 Premium", "tahun": 2022, "km": "22,000", "ansuran": "RM 370", "deposit": "RM 1,500", "status": "✅ Tersedia"},
    {"model": "Perodua Aruz 1.5 AV",     "tahun": 2020, "km": "61,000", "ansuran": "RM 740", "deposit": "RM 3,500", "status": "✅ Tersedia"},
]

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)


# ── SECURITY CHECK ────────────────────────────────────────────────────────────
def is_owner(update: Update) -> bool:
    return update.effective_user.id in OWNER_IDS


async def block_unauthorized(update: Update):
    await update.message.reply_text(
        "⛔ Akses ditolak. Bot ini hanya untuk owner Rencong Showroom KL."
    )


# ── GOOGLE SHEETS ─────────────────────────────────────────────────────────────
def get_leads_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).worksheet(SHEET_LEADS)


def fetch_leads():
    sheet = get_leads_sheet()
    rows  = sheet.get_all_records(head=4)  # Header ada di row 4
    return rows


# ── KEYBOARDS ─────────────────────────────────────────────────────────────────
def main_menu():
    return ReplyKeyboardMarkup([
        ["📊 Ringkasan Leads", "📋 Leads Terkini"],
        ["🚗 Semak Stok", "🔴 Hot Leads"],
        ["✏️ Update Status Lead", "❓ Bantuan"],
    ], resize_keyboard=True)


# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Selamat datang, *{name}*!\n\n"
        f"Ini adalah *AI Assistant* khas untuk anda.\n"
        f"Pilih fungsi dari menu di bawah, atau taip soalan terus.\n\n"
        f"_Contoh: \"berapa lead hari ni?\" atau \"stok apa yang ada?\"_",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ── RINGKASAN LEADS ───────────────────────────────────────────────────────────
async def ringkasan_leads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    await update.message.reply_text("⏳ Mengambil data dari Sheets...")

    try:
        leads = fetch_leads()
        total = len(leads)
        hot   = sum(1 for l in leads if "Hot"           in str(l.get("Status Lead", "")))
        warm  = sum(1 for l in leads if "Warm"          in str(l.get("Status Lead", "")))
        cold  = sum(1 for l in leads if "Cold"          in str(l.get("Status Lead", "")))
        closed= sum(1 for l in leads if "Closed"        in str(l.get("Status Lead", "")))
        tidak = sum(1 for l in leads if "Tidak Berminat" in str(l.get("Status Lead", "")))

        msg = (
            f"📊 *RINGKASAN LEADS*\n"
            f"{'─' * 28}\n"
            f"📌 *Jumlah Keseluruhan:* {total} leads\n\n"
            f"🔴 Hot Lead:         *{hot}*\n"
            f"🟡 Warm Lead:        *{warm}*\n"
            f"🟢 Cold Lead:        *{cold}*\n"
            f"✅ Closed:           *{closed}*\n"
            f"❌ Tidak Berminat:   *{tidak}*\n"
            f"{'─' * 28}\n"
            f"🕐 Dikemaskini: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu())

    except Exception as e:
        log.error(f"Sheets error: {e}")
        await update.message.reply_text(
            "⚠️ Gagal sambung ke Google Sheets. Cuba semula.",
            reply_markup=main_menu()
        )


# ── LEADS TERKINI ─────────────────────────────────────────────────────────────
async def leads_terkini(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    await update.message.reply_text("⏳ Mengambil 5 leads terkini...")

    try:
        leads = fetch_leads()
        # Ambil 5 terkini (bawah sekali = terbaru)
        recent = leads[-5:] if len(leads) >= 5 else leads
        recent.reverse()

        if not recent:
            await update.message.reply_text(
                "📭 Tiada leads lagi. Kongsikan link bot kepada pelanggan!",
                reply_markup=main_menu()
            )
            return

        msg = f"📋 *5 LEADS TERKINI*\n{'─' * 28}\n\n"
        for i, l in enumerate(recent, 1):
            status = l.get("Status Lead", "—")
            emoji  = "🔴" if "Hot" in status else "🟡" if "Warm" in status else "🟢" if "Cold" in status else "✅" if "Closed" in status else "❌"
            msg += (
                f"*{i}. {l.get('Nama Penuh', '—')}*\n"
                f"   📱 {l.get('No HP', '—')}\n"
                f"   💳 {l.get('Budget Ansuran', '—')}\n"
                f"   🚗 {l.get('Jenis Kereta', '—')}\n"
                f"   {emoji} {status}\n"
                f"   🕐 {l.get('Tarikh & Masa', '—')}\n\n"
            )

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu())

    except Exception as e:
        log.error(f"Sheets error: {e}")
        await update.message.reply_text("⚠️ Gagal sambung ke Google Sheets.", reply_markup=main_menu())


# ── HOT LEADS ─────────────────────────────────────────────────────────────────
async def hot_leads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    await update.message.reply_text("⏳ Mencari Hot Leads...")

    try:
        leads  = fetch_leads()
        hots   = [l for l in leads if "Hot" in str(l.get("Status Lead", ""))]

        if not hots:
            await update.message.reply_text(
                "✅ Tiada Hot Lead buat masa ini. Semua dalam kawalan!",
                reply_markup=main_menu()
            )
            return

        msg = f"🔴 *HOT LEADS — PERLU TINDAKAN SEGERA*\n{'─' * 28}\n\n"
        for i, l in enumerate(hots, 1):
            msg += (
                f"*{i}. {l.get('Nama Penuh', '—')}*\n"
                f"   📱 {l.get('No HP', '—')}\n"
                f"   💼 {l.get('Pekerjaan', '—')}\n"
                f"   💳 {l.get('Budget Ansuran', '—')}\n"
                f"   🚗 {l.get('Jenis Kereta', '—')}\n"
                f"   🎯 {l.get('Keperluan', '—')}\n"
                f"   ⚡ *Tindakan:* {l.get('Tindakan', '—')}\n\n"
            )

        msg += f"_Jumlah: {len(hots)} Hot Lead_"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu())

    except Exception as e:
        log.error(f"Sheets error: {e}")
        await update.message.reply_text("⚠️ Gagal sambung ke Google Sheets.", reply_markup=main_menu())


# ── SEMAK STOK ────────────────────────────────────────────────────────────────
async def semak_stok(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    tersedia = [k for k in STOK_KERETA if "Tersedia" in k["status"]]
    deposit  = [k for k in STOK_KERETA if "Deposit"  in k["status"]]

    msg = (
        f"🚗 *STOK KERETA SEMASA*\n"
        f"{'─' * 28}\n"
        f"✅ Tersedia: *{len(tersedia)}* unit\n"
        f"⏳ Deposit Diambil: *{len(deposit)}* unit\n"
        f"{'─' * 28}\n\n"
    )

    for k in STOK_KERETA:
        emoji = "✅" if "Tersedia" in k["status"] else "⏳"
        msg += (
            f"{emoji} *{k['model']}*\n"
            f"   📅 {k['tahun']}  •  🛣 {k['km']} km\n"
            f"   💳 {k['ansuran']}/bln  •  Deposit: {k['deposit']}\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu())


# ── UPDATE STATUS ─────────────────────────────────────────────────────────────
async def update_status_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    await update.message.reply_text(
        f"✏️ *Update Status Lead*\n\n"
        f"Taip dalam format ini:\n"
        f"`update [No HP] [status baru]`\n\n"
        f"*Contoh:*\n"
        f"`update 012-3456789 hot`\n"
        f"`update 019-8765432 closed`\n\n"
        f"*Status yang boleh:*\n"
        f"• `hot` — 🔴 Hot Lead\n"
        f"• `warm` — 🟡 Warm Lead\n"
        f"• `cold` — 🟢 Cold Lead\n"
        f"• `closed` — ✅ Closed\n"
        f"• `tidak` — ❌ Tidak Berminat",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    ctx.user_data["awaiting_update"] = True


async def process_update_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE, text: str):
    parts = text.strip().split()
    if len(parts) < 3:
        await update.message.reply_text(
            "⚠️ Format salah. Contoh: `update 012-3456789 hot`",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return

    hp_cari  = parts[1]
    status_kw = parts[2].lower()

    status_map = {
        "hot":    "🔴  Hot Lead",
        "warm":   "🟡  Warm Lead",
        "cold":   "🟢  Cold Lead",
        "closed": "✅  Closed",
        "tidak":  "❌  Tidak Berminat",
    }

    if status_kw not in status_map:
        await update.message.reply_text(
            "⚠️ Status tidak dikenali. Guna: hot / warm / cold / closed / tidak",
            reply_markup=main_menu()
        )
        return

    status_baru = status_map[status_kw]

    try:
        sheet = get_leads_sheet()
        data  = sheet.get_all_values()

        # Cari row dengan No HP yang match (col 3 = index 2)
        found = False
        for i, row in enumerate(data):
            if len(row) > 2 and hp_cari.replace("-", "").replace(" ", "") in row[2].replace("-", "").replace(" ", ""):
                # Update kolum K (index 10) = Status Lead
                sheet.update_cell(i + 1, 11, status_baru)
                nama = row[1] if len(row) > 1 else "—"
                await update.message.reply_text(
                    f"✅ *Status berjaya dikemaskini!*\n\n"
                    f"👤 *Nama:* {nama}\n"
                    f"📱 *No HP:* {row[2]}\n"
                    f"📌 *Status Baru:* {status_baru}",
                    parse_mode="Markdown",
                    reply_markup=main_menu()
                )
                found = True
                break

        if not found:
            await update.message.reply_text(
                f"⚠️ No HP `{hp_cari}` tidak dijumpai dalam database.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )

    except Exception as e:
        log.error(f"Update error: {e}")
        await update.message.reply_text("⚠️ Gagal update. Cuba semula.", reply_markup=main_menu())

    ctx.user_data.pop("awaiting_update", None)


# ── BANTUAN ───────────────────────────────────────────────────────────────────
async def bantuan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    await update.message.reply_text(
        f"❓ *PANDUAN AI ASSISTANT*\n"
        f"{'─' * 28}\n\n"
        f"*Menu Utama:*\n"
        f"📊 Ringkasan Leads — jumlah & breakdown status\n"
        f"📋 Leads Terkini — 5 leads paling baru\n"
        f"🚗 Semak Stok — senarai kereta & availability\n"
        f"🔴 Hot Leads — leads yang perlu dihubungi segera\n"
        f"✏️ Update Status Lead — tukar status lead\n\n"
        f"*Soalan Bebas (taip terus):*\n"
        f"• _\"berapa lead hari ni?\"_\n"
        f"• _\"ada stok SUV tak?\"_\n"
        f"• _\"senarai hot leads\"_\n"
        f"• _\"update 012-xxx closed\"_\n\n"
        f"*Command:*\n"
        f"/start — Mulakan semula\n"
        f"/cancel — Batalkan operasi semasa",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ── NATURAL LANGUAGE HANDLER ──────────────────────────────────────────────────
async def natural_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await block_unauthorized(update)
        return

    text = update.message.text.strip().lower()

    # Check if awaiting update command
    if ctx.user_data.get("awaiting_update") or text.startswith("update "):
        await process_update_status(update, ctx, update.message.text.strip())
        return

    # Route by keyword
    if any(w in text for w in ["ringkasan", "summary", "jumlah", "berapa lead", "statistik", "stat"]):
        await ringkasan_leads(update, ctx)

    elif any(w in text for w in ["terkini", "baru", "latest", "recent", "masuk"]):
        await leads_terkini(update, ctx)

    elif any(w in text for w in ["hot", "urgent", "segera", "panas"]):
        await hot_leads(update, ctx)

    elif any(w in text for w in ["stok", "kereta", "stock", "available", "ada apa", "unit"]):
        await semak_stok(update, ctx)

    elif any(w in text for w in ["bantuan", "help", "cara", "panduan", "guna"]):
        await bantuan(update, ctx)

    else:
        await update.message.reply_text(
            f"🤖 Saya faham soalan anda. Pilih dari menu di bawah atau cuba:\n\n"
            f"• _\"ringkasan leads\"_\n"
            f"• _\"leads terkini\"_\n"
            f"• _\"semak stok\"_\n"
            f"• _\"hot leads\"_\n"
            f"• _\"update 012-xxx hot\"_",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )


# ── NOTIF LEAD BARU (dipanggil dari customer bot) ────────────────────────────
# Untuk notif automatik, tambah function ni dalam bot.py (customer bot):
#
# async def notify_owner(bot, lead_data: dict):
#     for owner_id in OWNER_IDS:
#         await bot.send_message(
#             chat_id=owner_id,
#             text=f"🔔 *LEAD BARU MASUK!*\n\n"
#                  f"👤 {lead_data['nama']}\n"
#                  f"📱 {lead_data['hp']}\n"
#                  f"💳 {lead_data['budget']}\n"
#                  f"🚗 {lead_data['jenis']}",
#             parse_mode="Markdown"
#         )


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(OWNER_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(MessageHandler(filters.Regex("^📊 Ringkasan Leads$"),  ringkasan_leads))
    app.add_handler(MessageHandler(filters.Regex("^📋 Leads Terkini$"),    leads_terkini))
    app.add_handler(MessageHandler(filters.Regex("^🚗 Semak Stok$"),       semak_stok))
    app.add_handler(MessageHandler(filters.Regex("^🔴 Hot Leads$"),        hot_leads))
    app.add_handler(MessageHandler(filters.Regex("^✏️ Update Status Lead$"), update_status_prompt))
    app.add_handler(MessageHandler(filters.Regex("^❓ Bantuan$"),           bantuan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,        natural_handler))

    log.info("🏪 Rencong Owner Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
