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
# MESSAGE
# ============================================================

@client.on(events.NewMessage)
async def new_message(event):

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
