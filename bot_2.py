import os
import asyncio
from pathlib import Path

from telethon import TelegramClient, events


# ============================================================
# SOZLAMALAR
# ============================================================

API_ID = int(os.getenv("API_ID", "946606"))
API_HASH = os.getenv("API_HASH", "a183e9d1503a9c6514bd086dd03aeb8e")

# Bot2 uchun session papkasi
BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "bot2_1"

SESSION_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SESSION_NAME = SESSION_DIR / "bot2_1"


# ============================================================
# TEKSHIRISH
# ============================================================

if API_ID == 0:
    raise ValueError(
        "API_ID topilmadi. Render Environment Variables "
        "ichiga API_ID qo'shing."
    )

if not API_HASH:
    raise ValueError(
        "API_HASH topilmadi. Render Environment Variables "
        "ichiga API_HASH qo'shing."
    )


# ============================================================
# USERBOT
# ============================================================

client = TelegramClient(
    str(SESSION_NAME),
    API_ID,
    API_HASH
)


# ============================================================
# YANGI XABAR
# ============================================================

@client.on(events.NewMessage)
async def new_message(event):

    # Faqat shaxsiy chatlar
    if event.is_private:

        text = event.raw_text.strip()

        # Test komandasi
        if text.lower() == "ping":

            await event.reply(
                "Pong 🟢"
            )


# ============================================================
# USERBOT MAIN
# ============================================================

async def main():

    print("=" * 50)
    print("BOT2 — TELEGRAM USERBOT")
    print("=" * 50)

    print()

    print("Session:")
    print(SESSION_NAME)

    print()

    print(
        "Agar session mavjud bo'lmasa, "
        "Telegram login ma'lumotlarini so'raydi."
    )

    print(
        "Telefon raqam → Telegram kodi → 2FA parol"
    )

    print()

    # UserBotni ishga tushirish
    await client.start()

    # Akkaunt ma'lumotlari
    me = await client.get_me()

    print()
    print("✅ BOT2 USERBOT ISHLADI")
    print()

    print(
        f"Ism: {me.first_name or ''}"
    )

    print(
        f"Familiya: {me.last_name or ''}"
    )

    print(
        f"Username: @{me.username}"
        if me.username
        else "Username: yo'q"
    )

    print(
        f"ID: {me.id}"
    )

    print()
    print("📡 Xabarlar kuzatilmoqda...")
    print("🛑 To'xtatish: CTRL+C")
    print()

    # Doimiy ishlash
    await client.run_until_disconnected()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print()
        print("🛑 Bot2 UserBot to'xtatildi.")
