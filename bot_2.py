import asyncio
import os
from pathlib import Path

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telethon import TelegramClient


# ============================================================
# CONFIG
# ============================================================

BOT2_TOKEN = os.getenv("BOT2_TOKEN")
API_ID_RAW = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
OWNER_ID_RAW = os.getenv("OWNER_ID")


if not BOT2_TOKEN:
    raise RuntimeError("BOT2_TOKEN topilmadi.")

if not API_ID_RAW:
    raise RuntimeError("API_ID topilmadi.")

if not API_HASH:
    raise RuntimeError("API_HASH topilmadi.")

if not OWNER_ID_RAW:
    raise RuntimeError("OWNER_ID topilmadi.")


try:
    API_ID = int(API_ID_RAW)
except ValueError:
    raise RuntimeError("API_ID raqam bo'lishi kerak.")


try:
    OWNER_ID = int(OWNER_ID_RAW)
except ValueError:
    raise RuntimeError("OWNER_ID raqam bo'lishi kerak.")


# ============================================================
# SESSION PAPKA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "bot_2"

SESSION_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# GLOBAL
# ============================================================

clients = {}

selected = None


# ============================================================
# OWNER TEKSHIRISH
# ============================================================

def is_owner(update: Update) -> bool:
    user = update.effective_user

    if not user:
        return False

    return user.id == OWNER_ID


# ============================================================
# START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    await update.message.reply_text(
        "✅ Bot2 ishlayapti!\n\n"
        "/help"
    )


# ============================================================
# HELP
# ============================================================

async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    text = (
        "🤖 BOT2 BUYRUQLARI\n\n"

        "/login — .session ulash\n"
        "/accounts — accountlar\n"
        "/use NOMI — account tanlash\n"
        "/status — status\n"
        "/id — Telegram ID\n"
        "/info — account ma'lumoti\n"
        "/logout — accountni o'chirish\n"
        "/ping — test\n"
        "/gps — joylashuv yuborish\n"
    )

    await update.message.reply_text(text)


# ============================================================
# LOGIN
# ============================================================

async def login(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    context.user_data["waiting_session"] = True

    await update.message.reply_text(
        "📁 .session faylini yuboring."
    )


# ============================================================
# SESSION QABUL QILISH
# ============================================================

async def receive_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    if not context.user_data.get("waiting_session"):
        return

    document = update.message.document

    if not document:
        return

    filename = document.file_name or ""

    if not filename.lower().endswith(".session"):
        await update.message.reply_text(
            "❌ Faqat .session fayl yuboring."
        )
        return

    context.user_data["waiting_session"] = False

    name = Path(filename).stem.strip()

    if not name:
        await update.message.reply_text(
            "❌ Session nomi noto'g'ri."
        )
        return

    session_file = SESSION_DIR / f"{name}.session"

    # Eski client bo'lsa yopamiz
    old_client = clients.get(name)

    if old_client:
        try:
            await old_client.disconnect()
        except Exception:
            pass

        clients.pop(name, None)

    try:

        # Telegram faylini yuklab olish
        tg_file = await context.bot.get_file(
            document.file_id
        )

        await tg_file.download_to_drive(
            str(session_file)
        )

        # Telethon .session faylini ochish
        client = TelegramClient(
            str(session_file.with_suffix("")),
            API_ID,
            API_HASH,
        )

        await client.connect()

        # Login tekshirish
        authorized = await client.is_user_authorized()

        if not authorized:

            await client.disconnect()

            session_file.unlink(
                missing_ok=True
            )

            await update.message.reply_text(
                "❌ Session yaroqsiz.\n"
                "Telegram akkauntiga kirilmagan."
            )

            return

        # Account ma'lumoti
        me = await client.get_me()

        clients[name] = client

        await update.message.reply_text(
            "✅ ACCOUNT ULANDI!\n\n"

            f"📁 Session: {name}\n"
            f"👤 Ism: {me.first_name or 'Nomaʼlum'}\n"
            f"🆔 ID: {me.id}\n"
            f"📱 Telefon: {me.phone or 'yashirilgan'}\n\n"

            f"Accountni tanlash:\n"
            f"/use {name}"
        )

    except Exception as e:

        session_file.unlink(
            missing_ok=True
        )

        await update.message.reply_text(
            "❌ Session ulashda xato:\n\n"
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# ACCOUNTS
# ============================================================

async def accounts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    if not clients:

        await update.message.reply_text(
            "📭 Hozircha account yo'q."
        )

        return

    lines = []

    for name, client in clients.items():

        if client.is_connected():
            icon = "🟢"
        else:
            icon = "🔴"

        selected_icon = ""

        if name == selected:
            selected_icon = " ⭐"

        lines.append(
            f"{icon} {name}{selected_icon}"
        )

    await update.message.reply_text(
        "👤 ACCOUNTLAR\n\n"
        + "\n".join(lines)
    )


# ============================================================
# USE
# ============================================================

async def use(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    global selected

    if not is_owner(update):
        return

    if not context.args:

        await update.message.reply_text(
            "/use SESSION_NOMI"
        )

        return

    name = context.args[0]

    if name not in clients:

        await update.message.reply_text(
            "❌ Account topilmadi.\n\n"
            "/accounts"
        )

        return

    selected = name

    await update.message.reply_text(
        f"✅ Account tanlandi:\n\n"
        f"📁 {name}"
    )


# ============================================================
# STATUS
# ============================================================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    if not selected:

        await update.message.reply_text(
            "❌ Account tanlanmagan."
        )

        return

    client = clients.get(selected)

    if not client:

        await update.message.reply_text(
            "❌ Account topilmadi."
        )

        return

    if client.is_connected():

        status_text = "🟢 Ulangan"

    else:

        status_text = "🔴 Ulanmagan"

    await update.message.reply_text(
        f"📡 Account: {selected}\n"
        f"{status_text}"
    )


# ============================================================
# TELEGRAM ID
# ============================================================

async def tg_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    if not selected:

        await update.message.reply_text(
            "❌ Avval account tanlang."
        )

        return

    client = clients.get(selected)

    if not client:

        await update.message.reply_text(
            "❌ Account topilmadi."
        )

        return

    try:

        if not client.is_connected():
            await client.connect()

        me = await client.get_me()

        await update.message.reply_text(
            f"🆔 Telegram ID:\n\n"
            f"{me.id}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Xato:\n{e}"
        )


# ============================================================
# INFO
# ============================================================

async def info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    if not selected:

        await update.message.reply_text(
            "❌ Avval account tanlang."
        )

        return

    client = clients.get(selected)

    if not client:

        await update.message.reply_text(
            "❌ Account topilmadi."
        )

        return

    try:

        if not client.is_connected():
            await client.connect()

        me = await client.get_me()

        username = (
            f"@{me.username}"
            if me.username
            else "yo'q"
        )

        phone = (
            me.phone
            if me.phone
            else "yashirilgan"
        )

        await update.message.reply_text(
            "👤 ACCOUNT MA'LUMOTI\n\n"

            f"📁 Session: {selected}\n"
            f"👤 Ism: {me.first_name or 'yoq'}\n"
            f"👤 Familiya: {me.last_name or 'yoq'}\n"
            f"🔹 Username: {username}\n"
            f"🆔 ID: {me.id}\n"
            f"📱 Telefon: {phone}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Xato:\n{e}"
        )


# ============================================================
# LOGOUT
# ============================================================

async def logout(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    global selected

    if not is_owner(update):
        return

    if not selected:

        await update.message.reply_text(
            "❌ Account tanlanmagan."
        )

        return

    name = selected

    client = clients.get(name)

    if client:

        try:
            await client.disconnect()
        except Exception:
            pass

        clients.pop(name, None)

    session_file = (
        SESSION_DIR / f"{name}.session"
    )

    session_file.unlink(
        missing_ok=True
    )

    selected = None

    await update.message.reply_text(
        f"🗑 Account o'chirildi:\n\n"
        f"{name}"
    )


# ============================================================
# PING
# ============================================================

async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    await update.message.reply_text(
        "🏓 Pong 🟢"
    )


# ============================================================
# GPS
# ============================================================

async def gps(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    keyboard = [
        [
            KeyboardButton(
                "📍 Joylashuvni yuborish",
                request_location=True,
            )
        ]
    ]

    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "📍 Joylashuvni yuborish uchun "
        "tugmani bosing:",
        reply_markup=markup,
    )


# ============================================================
# LOCATION
# ============================================================

async def location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_owner(update):
        return

    location_data = update.message.location

    if not location_data:
        return

    latitude = location_data.latitude
    longitude = location_data.longitude

    maps_url = (
        "https://www.google.com/maps"
        f"?q={latitude},{longitude}"
    )

    await update.message.reply_text(
        "📍 JOYLASHUV\n\n"

        f"Latitude: {latitude}\n"
        f"Longitude: {longitude}\n\n"

        f"🗺 Google Maps:\n"
        f"{maps_url}"
    )


# ============================================================
# OLD SESSIONLARNI YUKLASH
# ============================================================

async def load_sessions():
    """
    Server qayta ishga tushganda
    mavjud .session fayllarini avtomatik
    qayta ulaydi.
    """

    for session_file in SESSION_DIR.glob(
        "*.session"
    ):

        name = session_file.stem

        if name in clients:
            continue

        client = TelegramClient(
            str(session_file.with_suffix("")),
            API_ID,
            API_HASH,
        )

        try:

            await client.connect()

            authorized = (
                await client.is_user_authorized()
            )

            if authorized:

                clients[name] = client

                print(
                    f"✅ Session yuklandi: {name}"
                )

            else:

                await client.disconnect()

                print(
                    f"⚠️ Session yaroqsiz: {name}"
                )

        except Exception as e:

            try:
                await client.disconnect()
            except Exception:
                pass

            print(
                f"❌ Session yuklanmadi: "
                f"{name} — {e}"
            )


# ============================================================
# SHUTDOWN
# ============================================================

async def shutdown_clients():

    for name, client in list(
        clients.items()
    ):

        try:

            await client.disconnect()

        except Exception as e:

            print(
                f"⚠️ {name} yopishda xato: {e}"
            )

    clients.clear()


# ============================================================
# MAIN
# ============================================================

async def main():

    application = (
        Application.builder()
        .token(BOT2_TOKEN)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_cmd,
        )
    )

    application.add_handler(
        CommandHandler(
            "login",
            login,
        )
    )

    application.add_handler(
        CommandHandler(
            "accounts",
            accounts,
        )
    )

    application.add_handler(
        CommandHandler(
            "use",
            use,
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status,
        )
    )

    application.add_handler(
        CommandHandler(
            "id",
            tg_id,
        )
    )

    application.add_handler(
        CommandHandler(
            "info",
            info,
        )
    )

    application.add_handler(
        CommandHandler(
            "logout",
            logout,
        )
    )

    application.add_handler(
        CommandHandler(
            "ping",
            ping,
        )
    )

    application.add_handler(
        CommandHandler(
            "gps",
            gps,
        )
    )

    # .session fayl
    application.add_handler(
        MessageHandler(
            filters.Document.ALL,
            receive_session,
        )
    )

    # GPS
    application.add_handler(
        MessageHandler(
            filters.LOCATION,
            location,
        )
    )

    # Old sessionlarni yuklash
    await load_sessions()

    # Botni ishga tushirish
    await application.initialize()
    await application.start()

    await application.updater.start_polling(
        drop_pending_updates=True
    )

    print(
        "================================"
    )

    print(
        "✅ BOT2 ISHLADI"
    )

    print(
        "================================"
    )

    try:

        await asyncio.Event().wait()

    finally:

        await application.updater.stop()

        await shutdown_clients()

        await application.stop()
        await application.shutdown()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
    
