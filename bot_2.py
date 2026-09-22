import asyncio
import json
from pathlib import Path

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from telethon import TelegramClient


# =========================================================
# SOZLAMALAR
# =========================================================

BOT2_TOKEN = "8992607786:AAG-Ii8k1yAr-FB5DXPMsSVcITczQ0uEbq8"

API_ID = 946606
API_HASH = "a183e9d1503a9c6514bd086dd03aeb8e"

# Faqat siz ishlatishingiz uchun Telegram ID'ingiz
OWNER_ID = 1072547777


# =========================================================
# PAPKALAR
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

SESSION_DIR = BASE_DIR / "bot_2"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNTS_FILE = SESSION_DIR / "accounts.json"


# =========================================================
# GLOBAL
# =========================================================

clients = {}
accounts = {}
selected_session = None


# =========================================================
# ACCOUNTS.JSON
# =========================================================

def save_accounts():
    data = {}

    for name, info in accounts.items():
        data[name] = {
            "name": info.get("name", ""),
            "username": info.get("username", ""),
            "user_id": info.get("user_id", 0),
        }

    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_accounts():
    global accounts

    if not ACCOUNTS_FILE.exists():
        accounts = {}
        return

    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            accounts = json.load(f)
    except Exception:
        accounts = {}


# =========================================================
# OWNER TEKSHIRISH
# =========================================================

def is_owner(update: Update):
    user = update.effective_user

    if not user:
        return False

    return user.id == OWNER_ID


async def access_denied(update: Update):
    if update.message:
        await update.message.reply_text(
            "⛔ Bu botdan foydalanishga ruxsat yo‘q."
        )


# =========================================================
# START
# =========================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update):
        await access_denied(update)
        return

    await update.message.reply_text(
        "✅ Bot2 ishlayapti!\n\n"
        "Bu bot orqali Telegram UserBot sessionlarini ulashingiz mumkin.\n\n"
        "/help — komandalar"
    )


# =========================================================
# HELP
# =========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update):
        await access_denied(update)
        return

    text = (
        "📚 BOT2 KOMANDALAR\n\n"

        "🔐 UserBot:\n"
        "/login — .session ulash\n"
        "/accounts — ulangan accountlar\n"
        "/use — account tanlash\n"
        "/logout — accountni o‘chirish\n"
        "/status — holatini ko‘rish\n"
        "/id — Telegram ID\n"
        "/info — account ma’lumoti\n\n"

        "⚙️ Bot:\n"
        "/ping — tekshirish\n"
        "/gps — hozirgi joylashuvni yuborish\n"
        "/settings — Telegram sozlamalari\n"
        "/privacy — Privacy\n"
        "/notifications — Notifications\n"
        "/language — Language\n"
        "/data — Data\n"
    )

    await update.message.reply_text(text)


# =========================================================
# LOGIN
# =========================================================

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update):
        await access_denied(update)
        return

    context.user_data["waiting_session"] = True

    await update.message.reply_text(
        "🔐 SESSION ULASH\n\n"
        "Telegram .session faylini shu chatga yuboring.\n\n"
        "Masalan:\n"
        "account.session\n\n"
        "⚠️ Faqat o‘zingizga tegishli session faylini yuboring."
    )


# =========================================================
# SESSION NOMINI TAKRORLANMAS QILISH
# =========================================================

def unique_session_path(filename):

    filename = Path(filename).name

    if not filename.endswith(".session"):
        filename += ".session"

    path = SESSION_DIR / filename

    if not path.exists():
        return path

    stem = path.stem

    number = 1

    while True:
        new_path = SESSION_DIR / f"{stem}_{number}.session"

        if not new_path.exists():
            return new_path

        number += 1


# =========================================================
# SESSION QABUL QILISH
# =========================================================

async def session_file_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
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

    if document.file_size and document.file_size > 10 * 1024 * 1024:
        await update.message.reply_text(
            "❌ Session fayli juda katta."
        )
        return

    await update.message.reply_text(
        "⏳ Session yuklanmoqda..."
    )

    try:

        session_path = unique_session_path(filename)

        telegram_file = await context.bot.get_file(
            document.file_id
        )

        await telegram_file.download_to_drive(
            custom_path=str(session_path)
        )

        session_name = session_path.stem

        await update.message.reply_text(
            "🔍 Session tekshirilmoqda..."
        )

        client = TelegramClient(
            str(session_path.with_suffix("")),
            API_ID,
            API_HASH
        )

        await client.connect()

        authorized = await client.is_user_authorized()

        if not authorized:

            await client.disconnect()

            try:
                session_path.unlink()
            except Exception:
                pass

            await update.message.reply_text(
                "❌ Session Telegram akkauntiga login qilinmagan.\n\n"
                "Boshqa .session fayl yuboring."
            )

            return

        me = await client.get_me()

        clients[session_name] = client

        accounts[session_name] = {
            "name": me.first_name or "",
            "username": me.username or "",
            "user_id": me.id,
        }

        save_accounts()

        username_text = (
            f"@{me.username}"
            if me.username
            else "Username yo‘q"
        )

        await update.message.reply_text(
            "✅ SESSION MUVAFFAQIYATLI ULANDI!\n\n"
            f"📁 Session: {session_name}\n"
            f"👤 Ism: {me.first_name or ''}\n"
            f"🔹 Username: {username_text}\n"
            f"🆔 ID: {me.id}\n\n"
            "Endi /use orqali accountni tanlashingiz mumkin."
        )

    except Exception as e:

        try:
            if "client" in locals():
                await client.disconnect()
        except Exception:
            pass

        await update.message.reply_text(
            "❌ Sessionni ulashda xatolik:\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================================================
# ACCOUNTS
# =========================================================

async def accounts_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    if not accounts:
        await update.message.reply_text(
            "📭 Hozircha session ulanmagan."
        )
        return

    text = "👤 ULANGAN ACCOUNTLAR:\n\n"

    for number, (name, info) in enumerate(
        accounts.items(),
        start=1
    ):

        username = info.get("username", "")

        username_text = (
            f"@{username}"
            if username
            else "Username yo‘q"
        )

        selected = ""

        if name == selected_session:
            selected = " ⭐"

        text += (
            f"{number}. {name}{selected}\n"
            f"   👤 {info.get('name', '')}\n"
            f"   🔹 {username_text}\n"
            f"   🆔 {info.get('user_id', '')}\n\n"
        )

    await update.message.reply_text(text)


# =========================================================
# USE
# =========================================================

async def use_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global selected_session

    if not is_owner(update):
        await access_denied(update)
        return

    if not accounts:
        await update.message.reply_text(
            "📭 Avval /login orqali session ulang."
        )
        return

    if not context.args:

        text = (
            "👉 Account tanlang:\n\n"
            "Mavjud sessionlar:\n\n"
        )

        for name in accounts:
            text += f"• {name}\n"

        text += (
            "\nMisol:\n"
            "/use account"
        )

        await update.message.reply_text(text)

        return

    name = context.args[0]

    if name not in accounts:
        await update.message.reply_text(
            "❌ Bunday session topilmadi.\n\n"
            "📋 /accounts"
        )
        return

    if name not in clients:

        session_path = SESSION_DIR / f"{name}.session"

        if not session_path.exists():
            await update.message.reply_text(
                "❌ Session fayli topilmadi."
            )
            return

        try:

            client = TelegramClient(
                str(session_path.with_suffix("")),
                API_ID,
                API_HASH
            )

            await client.connect()

            if not await client.is_user_authorized():
                await client.disconnect()

                await update.message.reply_text(
                    "❌ Session autorizatsiyadan o‘tmagan."
                )

                return

            clients[name] = client

        except Exception as e:

            await update.message.reply_text(
                f"❌ Ulanishda xato:\n{e}"
            )

            return

    selected_session = name

    await update.message.reply_text(
        f"✅ Account tanlandi:\n\n"
        f"📁 {name}\n"
        f"👤 {accounts[name].get('name', '')}\n"
        f"🆔 {accounts[name].get('user_id', '')}"
    )


# =========================================================
# STATUS
# =========================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    if not selected_session:
        await update.message.reply_text(
            "❌ Hali account tanlanmagan.\n\n"
            "/use SESSION_NOMI"
        )
        return

    client = clients.get(selected_session)

    if not client:
        await update.message.reply_text(
            "🔴 Client ulanmagan."
        )
        return

    try:

        connected = client.is_connected()

        if connected:
            status = "🟢 Ulangan"
        else:
            status = "🔴 Ulanmagan"

        await update.message.reply_text(
            f"📡 STATUS\n\n"
            f"📁 Session: {selected_session}\n"
            f"Holat: {status}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Xato:\n{e}"
        )


# =========================================================
# ID
# =========================================================

async def id_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    if not selected_session:
        await update.message.reply_text(
            "❌ Account tanlanmagan."
        )
        return

    client = clients.get(selected_session)

    if not client:
        await update.message.reply_text(
            "❌ Client ulanmagan."
        )
        return

    try:

        me = await client.get_me()

        await update.message.reply_text(
            f"🆔 Telegram ID: {me.id}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Xato:\n{e}"
        )


# =========================================================
# INFO
# =========================================================

async def info_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    if not selected_session:
        await update.message.reply_text(
            "❌ Account tanlanmagan."
        )
        return

    client = clients.get(selected_session)

    if not client:
        await update.message.reply_text(
            "❌ Client ulanmagan."
        )
        return

    try:

        me = await client.get_me()

        username = (
            f"@{me.username}"
            if me.username
            else "Username yo‘q"
        )

        await update.message.reply_text(
            "👤 ACCOUNT INFO\n\n"
            f"Ism: {me.first_name or ''}\n"
            f"Familiya: {me.last_name or ''}\n"
            f"Username: {username}\n"
            f"ID: {me.id}\n"
            f"Phone: {me.phone or 'yashirilgan'}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Xato:\n{e}"
        )


# =========================================================
# LOGOUT
# =========================================================

async def logout_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global selected_session

    if not is_owner(update):
        await access_denied(update)
        return

    if not context.args:

        if selected_session:

            await update.message.reply_text(
                "⚠️ Tanlangan accountni o‘chirish uchun:\n\n"
                "/logout CONFIRM"
            )

        else:

            await update.message.reply_text(
                "❌ Account tanlanmagan."
            )

        return

    if context.args[0].upper() != "CONFIRM":
        await update.message.reply_text(
            "❌ Tasdiqlash uchun:\n"
            "/logout CONFIRM"
        )
        return

    if not selected_session:
        await update.message.reply_text(
            "❌ Account tanlanmagan."
        )
        return

    name = selected_session

    client = clients.get(name)

    try:
        if client:
            await client.disconnect()
    except Exception:
        pass

    clients.pop(name, None)

    session_path = SESSION_DIR / f"{name}.session"

    try:
        if session_path.exists():
            session_path.unlink()
    except Exception as e:

        await update.message.reply_text(
            f"⚠️ Session faylini o‘chirishda xato:\n{e}"
        )

    accounts.pop(name, None)

    save_accounts()

    selected_session = None

    await update.message.reply_text(
        f"🗑 Account o‘chirildi:\n{name}"
    )


# =========================================================
# PING
# =========================================================

async def ping_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    await update.message.reply_text(
        "🏓 Pong 🟢\n"
        "Bot2 ishlayapti."
    )


# =========================================================
# GPS
# =========================================================

async def gps_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    keyboard = [
        [
            KeyboardButton(
                "📍 Hozirgi joylashuvimni yuborish",
                request_location=True
            )
        ]
    ]

    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "📍 Hozirgi GPS joylashuvingizni olish uchun "
        "pastdagi tugmani bosing.\n\n"
        "Telegram telefoningizdagi GPS joylashuvni botga yuboradi.",
        reply_markup=markup
    )


# =========================================================
# LOCATION QABUL QILISH
# =========================================================

async def location_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    location = update.message.location

    if not location:
        return

    latitude = location.latitude
    longitude = location.longitude

    maps_link = (
        f"https://www.google.com/maps?q="
        f"{latitude},{longitude}"
    )

    await update.message.reply_text(
        "📍 JOYLASHUV QABUL QILINDI!\n\n"
        f"🌐 Latitude: {latitude}\n"
        f"🌐 Longitude: {longitude}\n\n"
        f"🗺 Google Maps:\n{maps_link}"
    )


# =========================================================
# SETTINGS
# =========================================================

async def settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "⚙️ Telegram Settings",
                url="tg://settings/"
            )
        ]
    ]

    await update.message.reply_text(
        "⚙️ Telegram sozlamalari:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# PRIVACY
# =========================================================

async def privacy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🔒 Privacy",
                url="tg://settings/privacy"
            )
        ]
    ]

    await update.message.reply_text(
        "🔒 Privacy sozlamalari:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

async def notifications_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🔔 Notifications",
                url="tg://settings/notifications"
            )
        ]
    ]

    await update.message.reply_text(
        "🔔 Notifications:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# LANGUAGE
# =========================================================

async def language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(update):
        await access_denied(update)
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Language"e.reply_text(
            "📭 Sizda ulangan akkaunt yo'q.\n\n"
            "/login"
        )

        return

    await update.message.reply_text(
        text
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

    own = []

    for key, data in accounts.items():

        if data.get("owner_id") == user_id:

            own.append(
                (key, data)
            )

    if not own:

        await update.message.reply_text(
            "❌ Avval session ulang:\n"
            "/login"
        )

        return

    if not context.args:

        text = (
            "🔄 AKKAUNT TANLASH\n\n"
            "Mavjud akkauntlar:\n\n"
        )

        for key, data in own:

            text += (
                f"🔑 {key}\n"
                f"👤 {data.get('first_name', '')}\n\n"
            )

        text += (
            "Tanlash:\n"
            "/use SESSION_NOMI"
        )

        await update.message.reply_text(
            text
        )

        return

    key = context.args[0]

    if key not in accounts:

        await update.message.reply_text(
            "❌ Bunday session topilmadi."
        )

        return

    if accounts[key].get(
        "owner_id"
    ) != user_id:

        await update.message.reply_text(
            "❌ Bu session sizniki emas."
        )

        return

    if key not in clients:

        await update.message.reply_text(
            "❌ Session faol emas."
        )

        return

    selected_accounts[user_id] = key

    await update.message.reply_text(
        "✅ Akkaunt tanlandi.\n\n"
        f"👤 {accounts[key].get('first_name', '')}\n"
        f"🆔 {accounts[key].get('user_id')}"
    )


# ============================================================
# /status
# ============================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(
        update
    )

    if not client:
        return

    me = await client.get_me()

    await update.message.reply_text(
        "🟢 USERBOT ISHLAYAPTI\n\n"
        f"👤 {me.first_name or ''}\n"
        f"🆔 {me.id}\n"
        f"🔗 @{me.username or 'yoq'}"
    )


# ============================================================
# /id
# ============================================================

async def id_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(
        update
    )

    if not client:
        return

    me = await client.get_me()

    await update.message.reply_text(
        f"🆔 Telegram ID:\n{me.id}"
    )


# ============================================================
# /info
# ============================================================

async def info_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(
        update
    )

    if not client:
        return

    me = await client.get_me()

    username = (
        f"@{me.username}"
        if me.username
        else "Yo'q"
    )

    await update.message.reply_text(
        "👤 USERBOT AKKAUNTI\n\n"

        f"🆔 ID: {me.id}\n"
        f"👤 Ism: {me.first_name or 'Yo‘q'}\n"
        f"👤 Familiya: {me.last_name or 'Yo‘q'}\n"
        f"🔗 Username: {username}\n"
        f"🤖 Bot: {me.bot}"
    )


# ============================================================
# /ping
# ============================================================

async def ping_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    client = await get_selected_client(
        update
    )

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
        "📍 GPS\n\n"

        "Render server telefon GPS sensoriga "
        "to'g'ridan-to'g'ri kira olmaydi.\n\n"

        "Google Maps:\n"
        "https://maps.google.com/"
    )


# ============================================================
# TG:// SETTINGS
# ============================================================

async def settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "⚙️ Telegram Settings:\n\n"
        "tg://settings/"
    )


async def privacy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔐 Privacy:\n\n"
        "tg://settings/privacy"
    )


async def notifications_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔔 Notifications:\n\n"
        "tg://settings/notifications"
    )


async def language_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🌐 Language:\n\n"
        "tg://settings/language"
    )


async def data_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📡 Data and Storage:\n\n"
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

    session_key = selected_accounts.get(
        user_id
    )

    if not session_key:

        await update.message.reply_text(
            "❌ Tanlangan akkaunt yo'q."
        )

        return

    client = clients.get(
        session_key
    )

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
        "✅ Akkaunt uzildi."
    )


# ============================================================
# ESKI SESSIONLARNI YUKLASH
# ============================================================

async def load_sessions():

    accounts = load_accounts()

    for session_path in SESSION_DIR.glob(
        "*.session"
    ):

        key = session_path.stem

        if key in clients:
            continue

        try:

            client = TelegramClient(
                str(
                    session_path.with_suffix("")
                ),
                API_ID,
                API_HASH
            )

            await client.connect()

            if not await client.is_user_authorized():

                await client.disconnect()

                print(
                    f"❌ Session ishlamaydi: {key}"
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
                    "session": str(
                        session_path
                    )
                }

            print(
                f"✅ Session yuklandi: "
                f"{me.first_name} "
                f"@{me.username or 'yoq'}"
            )

        except Exception as e:

            print(
                f"❌ Session xatosi "
                f"{key}: {e}"
            )

    save_accounts(accounts)


# ============================================================
# START
# ============================================================

async def start():

    print("=" * 60)
    print("BOT2 — SESSION CONNECTOR + USERBOT")
    print("=" * 60)

    await load_sessions()

    application = (
        Application.builder()
        .token(BOT2_TOKEN)
        .build()
    )

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "login",
            login_command
        )
    )

    application.add_handler(
        CommandHandler(
            "accounts",
            accounts_command
        )
    )

    application.add_handler(
        CommandHandler(
            "use",
            use_command
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status_command
        )
    )

    application.add_handler(
        CommandHandler(
            "id",
            id_command
        )
    )

    application.add_handler(
        CommandHandler(
            "info",
            info_command
        )
    )

    application.add_handler(
        CommandHandler(
            "ping",
            ping_command
        )
    )

    application.add_handler(
        CommandHandler(
            "gps",
            gps_command
        )
    )

    application.add_handler(
        Comman

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

