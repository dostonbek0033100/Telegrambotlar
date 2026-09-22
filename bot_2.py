import os
from pathlib import Path

from telethon import TelegramClient, events


# ============================================================
# API
# ============================================================

API_ID = int(os.getenv("API_ID", "946606"))
API_HASH = os.getenv("API_HASH", "a183e9d1503a9c6514bd086dd03aeb8e")

if API_ID == 0:
    raise ValueError("API_ID topilmadi")

if not API_HASH:
    raise ValueError("API_HASH topilmadi")


# ============================================================
# SESSION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SESSION_DIR = BASE_DIR / "bot_2"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

SESSION_NAME = SESSION_DIR / "bot2_1"


# ============================================================
# TELEGRAM CLIENT
# ============================================================

client = TelegramClient(
    str(SESSION_NAME),
    API_ID,
    API_HASH
)


# ============================================================
# /ping
# ============================================================

@client.on(events.NewMessage)
async def ping_handler(event):

    if event.raw_text.strip().lower() == "/ping":
        await event.reply("Pong 🟢")


# ============================================================
# /id
# ============================================================

@client.on(events.NewMessage)
async def id_handler(event):

    if event.raw_text.strip().lower() == "/id":

        sender = await event.get_sender()

        if not sender:
            return

        await event.reply(
            f"🆔 Telegram ID: `{sender.id}`"
        )


# ============================================================
# /info
# ============================================================

@client.on(events.NewMessage)
async def info_handler(event):

    if event.raw_text.strip().lower() == "/info":

        sender = await event.get_sender()

        if not sender:
            return

        first_name = sender.first_name or "Yo'q"
        last_name = sender.last_name or "Yo'q"
        username = (
            f"@{sender.username}"
            if sender.username
            else "Yo'q"
        )

        await event.reply(
            "👤 **Telegram ma'lumotlari**\n\n"
            f"🆔 ID: `{sender.id}`\n"
            f"👤 Ism: `{first_name}`\n"
            f"👤 Familiya: `{last_name}`\n"
            f"🔗 Username: `{username}`"
        )


# ============================================================
# /gps
# ============================================================

@client.on(events.NewMessage)
async def gps_handler(event):

    if event.raw_text.strip().lower() == "/gps":

        await event.reply(
            "📍 **GPS**\n\n"
            "Render server telefoningizning GPS sensoriga "
            "to'g'ridan-to'g'ri kira olmaydi.\n\n"
            "Haqiqiy telefon joylashuvini yuborish uchun "
            "Android qurilmadan Telegram orqali Location "
            "yuborilishi kerak.\n\n"
            "🗺 Google Maps:\n"
            "https://maps.google.com/"
        )


# ============================================================
# TG:// COMMANDS
# ============================================================

@client.on(events.NewMessage)
async def tg_handler(event):

    text = event.raw_text.strip().lower()

    if text == "/settings":
        await event.reply(
            "⚙️ Telegram sozlamalari:\n\n"
            "tg://settings/"
        )

    elif text == "/privacy":
        await event.reply(
            "🔐 Privacy sozlamalari:\n\n"
            "tg://settings/privacy"
        )

    elif text == "/notifications":
        await event.reply(
            "🔔 Notification sozlamalari:\n\n"
            "tg://settings/notifications"
        )

    elif text == "/language":
        await event.reply(
            "🌐 Language sozlamalari:\n\n"
            "tg://settings/language"
        )

    elif text == "/data":
        await event.reply(
            "📡 Data and Storage sozlamalari:\n\n"
            "tg://settings/data-and-storage"
        )


# ============================================================
# /help
# ============================================================

@client.on(events.NewMessage)
async def help_handler(event):

    if event.raw_text.strip().lower() == "/help":

        await event.reply(
            "🤖 **USERBOT COMMANDS**\n\n"
            "📡 `/ping` — Bot ishlayotganini tekshirish\n"
            "🆔 `/id` — Telegram ID\n"
            "👤 `/info` — Akkaunt ma'lumotlari\n"
            "📍 `/gps` — GPS haqida ma'lumot\n\n"
            "⚙️ **Telegram sozlamalari**\n"
            "`/settings` — Telegram Settings\n"
            "`/privacy` — Privacy\n"
            "`/notifications` — Notifications\n"
            "`/language` — Language\n"
            "`/data` — Data and Storage"
        )


# ============================================================
# SIMPLE PING
# ============================================================

@client.on(events.NewMessage)
async def simple_ping_handler(event):

    if event.is_private:

        text = event.raw_text.strip()

        if text.lower() == "ping":
            await event.reply("Pong 🟢")


# ============================================================
# START
# ============================================================

async def start():

    print("=" * 50)
    print("BOT2 — TELEGRAM USERBOT")
    print("=" * 50)

    print()
    print(f"Session: {SESSION_NAME}")
    print()

    print("UserBot ishga tushmoqda...")

    await client.start()

    me = await client.get_me()

    print()
    print("✅ BOT2 USERBOT ISHLADI")
    print()

    print(f"Ism: {me.first_name or ''}")
    print(f"Familiya: {me.last_name or ''}")

    if me.username:
        print(f"Username: @{me.username}")
    else:
        print("Username: yo'q")

    print(f"ID: {me.id}")

    print()
    print("📡 Xabarlar kuzatilmoqda...")
    print()

    await client.run_until_disconnected()


# ============================================================
# DIRECT START
# ============================================================

if __name__ == "__main__":

    try:
        import asyncio
        asyncio.run(start())

    except KeyboardInterrupt:
        print("🛑 Bot2 to'xtatildi.")
