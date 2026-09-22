import asyncio
from pathlib import Path
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telethon import TelegramClient

BOT2_TOKEN = "8992607786:AAG-Ii8k1yAr-FB5DXPMsSVcITczQ0uEbq8"
API_ID = 946606
API_HASH = "a183e9d1503a9c6514bd086dd03aeb8e"
OWNER_ID = 1072547777

DIR = Path("bot_2")
DIR.mkdir(exist_ok=True)

clients = {}
selected = None


def ok(u):
    return u.effective_user and u.effective_user.id == OWNER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text("✅ Bot2 ishlayapti!\n/help")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text(
        "/login — session ulash\n"
        "/accounts — accountlar\n"
        "/use NOMI — tanlash\n"
        "/status — status\n"
        "/id — ID\n"
        "/info — ma'lumot\n"
        "/logout — o'chirish\n"
        "/ping — test\n"
        "/gps — GPS"
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    context.user_data["login"] = True
    await update.message.reply_text("📁 .session faylini yuboring")


async def session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update) or not context.user_data.get("login"):
        return

    f = update.message.document

    if not f.file_name.endswith(".session"):
        await update.message.reply_text("❌ Faqat .session fayl")
        return

    context.user_data["login"] = False
    name = Path(f.file_name).stem
    path = DIR / f"{name}.session"

    tgfile = await context.bot.get_file(f.file_id)
    await tgfile.download_to_drive(str(path))

    client = TelegramClient(str(path.with_suffix("")), API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            path.unlink(missing_ok=True)
            await update.message.reply_text("❌ Session yaroqsiz")
            return

        me = await client.get_me()
        clients[name] = client

        await update.message.reply_text(
            f"✅ Ulandi!\n"
            f"📁 {name}\n"
            f"👤 {me.first_name or ''}\n"
            f"🆔 {me.id}\n\n"
            f"/use {name}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {e}")


async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    if not clients:
        await update.message.reply_text("📭 Account yo'q")
        return

    await update.message.reply_text(
        "👤 Accountlar:\n\n" +
        "\n".join(f"• {x}" for x in clients)
    )


async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global selected

    if not ok(update): return

    if not context.args:
        await update.message.reply_text("/use SESSION_NOMI")
        return

    name = context.args[0]

    if name not in clients:
        await update.message.reply_text("❌ Topilmadi")
        return

    selected = name
    await update.message.reply_text(f"✅ Tanlandi: {name}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    if not selected:
        await update.message.reply_text("❌ Account tanlanmagan")
        return

    c = clients[selected]

    await update.message.reply_text(
        f"📡 {selected}\n"
        f"{'🟢 Ulangan' if c.is_connected() else '🔴 Ulanmagan'}"
    )


async def tg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    if not selected:
        await update.message.reply_text("❌ Account tanlanmagan")
        return

    me = await clients[selected].get_me()
    await update.message.reply_text(f"🆔 {me.id}")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    if not selected:
        await update.message.reply_text("❌ Account tanlanmagan")
        return

    me = await clients[selected].get_me()

    await update.message.reply_text(
        f"👤 {me.first_name or ''}\n"
        f"🔹 @{me.username or 'yo‘q'}\n"
        f"🆔 {me.id}\n"
        f"📱 {me.phone or 'yashirilgan'}"
    )


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global selected

    if not ok(update): return

    if not selected:
        await update.message.reply_text("❌ Account tanlanmagan")
        return

    name = selected
    await clients[name].disconnect()
    del clients[name]

    (DIR / f"{name}.session").unlink(missing_ok=True)

    selected = None

    await update.message.reply_text(f"🗑 {name} o'chirildi")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ok(update):
        await update.message.reply_text("🏓 Pong 🟢")


async def gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    kb = [[KeyboardButton(
        "📍 Joylashuvni yuborish",
        request_location=True
    )]]

    await update.message.reply_text(
        "GPS yuborish uchun tugmani bosing:",
        reply_markup=ReplyKeyboardMarkup(
            kb,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    x = update.message.location
    link = f"https://www.google.com/maps?q={x.latitude},{x.longitude}"

    await update.message.reply_text(
        f"📍 {x.latitude}, {x.longitude}\n\n"
        f"🗺 {link}"
    )


async def main():
    app = Application.builder().token(BOT2_TOKEN).build()

    cmds = {
        "start": start,
        "help": help_cmd,
        "login": login,
        "accounts": accounts,
        "use": use,
        "status": status,
        "id": tg_id,
        "info": info,
        "logout": logout,
        "ping": ping,
        "gps": gps,
    }

    for name, func in cmds.items():
        app.add_handler(CommandHandler(name, func))

    app.add_handler(MessageHandler(filters.Document.ALL, session))
    app.add_handler(MessageHandler(filters.LOCATION, location))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("✅ BOT2 ISHLADI")

    await asyncio.Event().wait()


asyncio.run(main())
