import os
import re
import json
import asyncio
from pathlib import Path

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from telethon import TelegramClient
from telethon.errors import RPCError


# ============================================================
# SOZLAMALAR
# ============================================================

API_ID = int(os.getenv("API_ID", "946606"))
API_HASH = os.getenv("API_HASH", "a183e9d1503a9c6514bd086dd03aeb8e")
BOT2_TOKEN = os.getenv("BOT2_TOKEN", "8992607786:AAG-Ii8k1yAr-FB5DXPMsSVcITczQ0uEbq8")

if API_ID == 0:
    raise ValueError("API_ID topilmadi")

if not API_HASH:
    raise ValueError("API_HASH topilmadi")

if not BOT2_TOKEN:
    raise ValueError("BOT2_TOKEN topilmadi")


# ============================================================
# PAPKALAR
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SESSION_DIR = BASE_DIR / "bot_2"

SESSION_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ACCOUNTS_FILE = SESSION_DIR / "accounts.json"


# ============================================================
# GLOBAL
# ============================================================

clients = {}

selected_accounts = {}

bot_app = None


# ============================================================
# ACCOUNTS.JSON
# ============================================================

def load_accounts():

    if not ACCOUNTS_FILE.exists():
        return {}

    try:
        with open(
            ACCOUNTS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:
        return {}


def save_accounts(accounts):

    with open(
        ACCOUNTS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            accounts,
            f,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# USER ID
# ============================================================

def get_user_id(update):

    if update.effective_user:
        return update.effective_user.id

    return None


# ============================================================
# /start
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 Bot2 ishlayapti.\n\n"
        "Telegram akkauntini ulash uchun:\n"
        "/login\n\n"
        "Mavjud komandalar:\n"
        "/login\n"
        "/logout\n"
        "/accounts\n"
        "/use\n"
        "/status\n"
        "/id\n"
        "/info\n"
        "/ping\n"
        "/gps\n"
        "/help"
    )


# ============================================================
# /help
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 BOT2 COMMANDS\n\n"

        "🔐 AKKAUNT\n"
        "/login — Session ulash\n"
        "/logout — Tanlangan sessionni uzish\n"
        "/accounts — Ulangan akkauntlar\n"
        "/use — Akkaunt tanlash\n"
        "/status — Holat\n\n"

        "👤 USERBOT\n"
        "/id — Telegram ID\n"
        "/info — Akkaunt ma'lumotlari\n"
        "/ping — Ping\n"
        "/gps — GPS haqida\n\n"

        "⚙️ TELEGRAM\n"
        "/settings\n"
        "/privacy\n"
        "/notifications\n"
        "/language\n"
        "/data"
    )


# ============================================================
# /login
# ============================================================

async def login_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["waiting_session"] = True

    await update.message.reply_text(
        "🔐 **Session ulash**\n\n"
        "Telethon `.session` faylingizni yuboring.\n\n"
        "Masalan:\n"
        "`bot2_1.session`\n\n"
        "Session fayl Telegram akkauntingizga kirish "
        "ma'lumotlarini o'z ichiga oladi. Uni faqat "
        "o'zingiz nazorat qiladigan botga yuboring.",
        parse_mode="Markdown"
    )


# ============================================================
# SESSION QABUL QILISH
# ============================================================

async def session_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get("waiting_session"):
        return

    document = update.message.document

    if not document:
        return

    filename = document.file_name or ""

    if not filename.lower().endswith(".session"):

        await update.message.reply_text(
            "❌ Faqat `.session` fayl yuboring."
        )

        return

    context.user_data["waiting_session"] = False

    user_id = get_user_id(update)

    await update.message.reply_text(
        "⏳ Session qabul qilindi.\n"
        "Akkaunt tekshirilmoqda..."
    )

    # --------------------------------------------------------
    # Xavfsiz fayl nomi
    # --------------------------------------------------------

    safe_name = re.sub(
        r"[^a-zA-Z0-9_.-]",
        "_",
        Path(filename).name
    )

    # .session ni saqlaymiz
    session_path = SESSION_DIR / safe_name

    # Bir xil nom bo'lsa yangi nom
    counter = 1

    while session_path.exists():

        stem = Path(safe_name).stem

        session_path = (
            SESSION_DIR /
            f"{stem}_{counter}.session"
        )

        counter += 1

    try:

        tg_file = await context.bot.get_file(
            document.file_id
        )

        await tg_file.download_to_drive(
            custom_path=str(session_path)
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Faylni yuklab bo'lmadi:\n{e}"
        )

        return

    # --------------------------------------------------------
    # Sessionni tekshirish
    # --------------------------------------------------------

    client = None

    try:

        client = TelegramClient(
            str(session_path.with_suffix("")),
            API_ID,
            API_HASH
        )

        await client.connect()

        if not await client.is_user_authorized():

            await client.disconnect()

            session_path.unlink(
                missing_ok=True
            )

            await update.message.reply_text(
                "❌ Bu session avtorizatsiyadan o'tmagan.\n\n"
                "Pydroid/Telethon orqali qayta login qilib "
                "session yarating."
            )

            return

        me = await client.get_me()

        # ----------------------------------------------------
        # Clientni saqlash
        # ----------------------------------------------------

        session_key = session_path.stem

        clients[session_key] = client

        accounts = load_accounts()

        accounts[session_key] = {
            "owner_id": user_id,
            "user_id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "session": str(session_path)
        }

        save_accounts(accounts)

        selected_accounts[user_id] = session_key

        username = (
            f"@{me.username}"
            if me.username
            else "Username yo'q"
        )

        await update.message.reply_text(
            "✅ **AKKAUNT ULANDI!**\n\n"
            f"👤 Ism: {me.first_name or 'Yo‘q'}\n"
            f"👤 Familiya: {me.last_name or 'Yo‘q'}\n"
            f"🔗 Username: {username}\n"
            f"🆔 ID: `{me.id}`\n\n"
            f"📁 Session: `{session_key}`\n\n"
            "Endi UserBot funksiyalaridan foydalanishingiz mumkin.",
            parse_mode="Markdown"
        )

    except Exception as e:

        if client:

            try:
                await client.disconnect()
            except:
                pass

        session_path.unlink(
            missing_ok=True
        )

        await update.message.reply_text(
            "❌ Sessionni tekshirishda xatolik:\n\n"
            f"{type(e).__name__}: {e}"
        )


# ============================================================
# TANLANGAN CLIENT
# ============================================================

async def get_selected_client(update):

    user_id = get_user_id(update)

    if not user_id:
        return None

    session_key = selected_accounts.get(user_id)

    if not session_key:

        await update.message.reply_text(
            "❌ Avval akkaunt ulang:\n"
            "/login"
        )

        return None

    client = clients.get(session_key)

    if not client:

        await update.message.reply_text(
            "❌ Session hozir faol emas.\n"
            "Sessionni qayta ulang:\n"
            "/login"
        )

        return None

    if not client.is_connected():

        await client.connect()

    return client


# ============================================================
# /accounts
# ============================================================

async def accounts_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    accounts = load_accounts()

    if not accounts:

        await update.message.reply_text(
            "📭 Hozircha hech qanday akkaunt ulanmagan.\n\n"
            "/login"
        )

        return

    user_id = get_user_id(update)

    text = "👥 **ULANGAN AKKAUNTLAR**\n\n"

    number = 1

    for key, data in accounts.items():

        if data.get("owner_id") != user_id:
            continue

        first_name = data.get(
            "first_name",
            ""
        )

        username = data.get(
            "username"
        )

        username_text = (
            f"@{username}"
            if username
            else "Username yo'q"
        )

        selected = (
            " 🟢"
            if selected_accounts.get(user_id) == key
            else ""
        )

        text += (
            f"{number}. {first_name} "
            f"({username_text}){selected}\n"
            f"   🆔 `{data.get('user_id')}`\n"
            f"   🔑 `{key}`\n\n"
        )

        number += 1

    if number == 1:

        await update.message.reply_text(
            "📭 Sizga tegishli session topilmadi."
        )

        return

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# ============================================================
# /use
# ============================================================

async def use_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    accounts = load_accounts()

    user_id = get_user_id(update)

    own_accounts = []

    for key, data in accounts.items():

        if data.get("owner_id") == user_id:

            own_accounts.append(
                (key, data)
            )

    if not own_accounts:

        await update.message.reply_text(
            "❌ Avval session ulang:\n"
            "/login"
        )

        return

    if not context.args:

        text = (
            "🔄 **Akkaunt tanlash**\n\n"
            "Quyidagicha yozing:\n"
            "`/use SESSION_NOMI`\n\n"
            "Mavjud sessionlar:\n\n"
        )

        for key, data in own_accounts:

            text += (
                f"🔑 `{key}` — "
                f"{data.get('first_name', '')}\n"
            )

        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )

        return

    key = context.args[0]

    if key not in accounts:

        await update.message.reply_text(
            "❌ Bunday session topilmadi."
        )

        return

    if accounts[key].get("owner_id") != user_id:

        await update.message.reply_text(
            "❌ Bu session sizga tegishli emas."
        )

        return

    if key not in clients:

        await update.message.reply_text(
            "❌ Session faol emas."
        )

        return

    selected_accounts[user_id] = key

    data = accounts[key]

    await update.message.reply_text(
        "✅ Akkaunt tanlandi.\n\n"
        f"👤 {data.get('first_name', '')}\n"
        f"🆔 `{data.get('user_id')}`",
        parse_mode="Markdown"
    )


# ============================================================
# /status
# ============================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(update)

    if not client:
        return

    me = await client.get_me()

    await update.message.reply_text(
        "🟢 **USERBOT ISHLAYAPTI**\n\n"
        f"👤 {me.first_name or ''}\n"
        f"🆔 `{me.id}`\n"
        f"🔗 @{me.username if me.username else 'yo‘q'}",
        parse_mode="Markdown"
    )


# ============================================================
# /id
# ============================================================

async def id_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(update)

    if not client:
        return

    me = await client.get_me()

    await update.message.reply_text(
        f"🆔 Telegram ID:\n`{me.id}`",
        parse_mode="Markdown"
    )


# ============================================================
# /info
# ============================================================

async def info_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(update)

    if not client:
        return

    me = await client.get_me()

    username = (
        f"@{me.username}"
        if me.username
        else "Yo'q"
    )

    await update.message.reply_text(
        "👤 **USERBOT AKKAUNTI**\n\n"
        f"🆔 ID: `{me.id}`\n"
        f"👤 Ism: `{me.first_name or 'Yo‘q'}`\n"
        f"👤 Familiya: `{me.last_name or 'Yo‘q'}`\n"
        f"🔗 Username: `{username}`\n"
        f"📱 Bot: `{me.bot}`",
        parse_mode="Markdown"
    )


# ============================================================
# /ping
# ============================================================

async def ping_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(update)

    if not client:
        return

    await update.message.reply_text(
        "Pong 🟢"
    )


# ============================================================
# /gps
# ============================================================

async def gps_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📍 **GPS**\n\n"
        "UserBot ishlayotgan Render server telefonning "
        "GPS sensoriga kira olmaydi.\n\n"
        "Haqiqiy telefon GPS joylashuvini olish uchun "
        "telefon tomonidan Location yuborilishi kerak.\n\n"
        "🗺 Google Maps:\n"
        "https://maps.google.com/"
    )


# ============================================================
# TG:// COMMANDS
# ============================================================

async def settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "⚙️ Telegram Settings:\n"
        "tg://settings/"
    )


async def privacy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔐 Privacy:\n"
        "tg://settings/privacy"
    )


async def notifications_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔔 Notifications:\n"
        "tg://settings/notifications"
    )


async def language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🌐 Language:\n"
        "tg://settings/language"
    )


async def data_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📡 Data and Storage:\n"
        "tg://settings/data-and-storage"
    )


# ============================================================
# /logout
# ============================================================

async def logout_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = get_user_id(update)

    session_key = selected_accounts.get(user_id)

    if not session_key:

        await update.message.reply_text(
            "❌ Tanlangan akkaunt yo'q."
        )

        return

    client = clients.get(session_key)

    if client:

        try:
            await client.disconnect()
        except:
            pass

        clients.pop(
            session_key,
            None
        )

    accounts = load_accounts()

    data = accounts.pop(
        session_key,
        None
    )

    save_accounts(accounts)

    selected_accounts.pop(
        user_id,
        None
    )

    if data:

        session_path = Path(
            data.get(
                "session",
                ""
            )
        )

        session_path.unlink(
            missing_ok=True
        )

    await update.message.reply_text(
        "✅ Tanlangan akkaunt uzildi va "
        "session fayli o'chirildi."
    )


# ============================================================
# SESSIONLARNI STARTDA YUKLASH
# ============================================================

async def load_sessions():

    accounts = load_accounts()

    for session_path in SESSION_DIR.glob("*.session"):

        key = session_path.stem

        if key in clients:
            continue

        try:

            client = TelegramClient(
                str(session_path.with_suffix("")),
                API_ID,
                API_HASH
            )

            await client.connect()

            if not await client.is_user_authorized():

                await client.disconnect()

                print(
                    f"❌ Session avtorizatsiyasiz: {key}"
                )

                continue

            me = await client.get_me()

            clients[key] = client

            if key not in accounts:

                accounts[key] = {
                    "owner_id": None,
                    "user_id": me.id,
                    "username": me.username,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "session": str(session_path)
                }

            print(
                f"✅ Session yuklandi: "
                f"{me.first_name} "
                f"(@{me.username or 'yoq'})"
            )

        except Exception as e:

            print(
                f"❌ Session yuklanmadi "
                f"{key}: {e}"
            )

    save_accounts(accounts)


# ============================================================
# WEB HEALTH CHECK
# ============================================================

async def health(request):

    return web.Response(
        text="Bot2 ishlayapti 🟢"
    )


async def start_web():

    app = web.Application()

    app.router.add_get(
        "/",
        health
    )

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print(
        f"Bot2 Web Server: {port}"
    )


# ============================================================
# TELEGRAM BOTNI ISHGA TUSHIRISH
# ============================================================

async def start():

    global bot_app

    print("=" * 60)
    print("BOT2 — USERBOT CONNECTOR")
    print("=" * 60)

    # --------------------------------------------------------
    # Eski sessionlarni yuklash
    # --------------------------------------------------------

    await load_sessions()

