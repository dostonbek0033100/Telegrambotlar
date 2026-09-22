import os
import asyncio
from pathlib import Path

from telethon import TelegramClient, events


# ============================================================
# API SETTINGS
# ============================================================

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")


# ============================================================
# CHECK API
# ============================================================

if API_ID == 0:
    raise ValueError(
        "API_ID topilmadi. Render Environment Variables ichiga API_ID qo'shing."
    )

if not API_HASH:
    raise ValueError(
        "API_HASH topilmadi. Render Environment Variables ichiga API_HASH qo'shing."
    )


# ============================================================
# SESSION PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SESSION_DIR = BASE_DIR / "bot2_1"
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
# NEW MESSAGE
# ============================================================

@client.on(events.NewMessage)
async def new_message(event):

    # Faqat shaxsiy chat
    if event.is_private:

        text = event.raw_text.strip()

        # Test komandasi
        if text.lower() == "ping":

            await event.reply("Pong 🟢")


# ============================================================
# USERBOT START
# ============================================================

async def start():

    print("=" * 50)
    print("BOT2 — TELEGRAM USERBOT")
    print("=" * 50)

    print()
    print(f"Session: {SESSION_NAME}")
    print()

    print("UserBot ishga tushmoqda...")

    # Telegramga ulanish
    await client.start()

    # User ma'lumotlarini olish
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

    # UserBotni doimiy ishlatish
    await client.run_until_disconnected()


# ============================================================
# DIRECT START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(start())

    except KeyboardInterrupt:

        print()
        print("🛑 Bot2 UserBot to'xtatildi.")
