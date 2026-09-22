import os
import re
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.helpers import escape_markdown


# ==============================
# BOT TOKEN
# ==============================

BOT_TOKEN = os.getenv("BOT1_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT1_TOKEN environment variable topilmadi!"
    )


# ==============================
# ADMINLAR
# ==============================

ADMIN_IDS = {1072547777}


# ==============================
# SPAM SO'ZLAR
# ==============================

SPAM_WORDS = [
    "xxx",
    "adult",
    "18+",
    "profilimda video bor",
]


# ==============================
# SPAM TEKSHIRISH
# ==============================

def contains_spam(text):
    text_lower = text.lower()
    found = []

    for word in SPAM_WORDS:
        w = word.lower()

        if re.fullmatch(r"[a-z0-9 ]+", w):
            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(w)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, text_lower):
                found.append(word)

        else:
            if w in text_lower:
                found.append(word)

    return found


# ==============================
# YANGI A'ZONI TEKSHIRISH
# ==============================

def should_ban(user):
    username = (
        user.username or ""
    ).lower().strip()

    full_name = (
        "{} {}".format(
            user.first_name or "",
            user.last_name or ""
        )
    ).lower().strip()

    # @user_... bo'lsa
    if username.startswith("user_"):
        return True, "username user_ bilan boshlanadi"

    # username'da admin bo'lsa
    if "admin" in username:
        return True, (
            "username'da 'admin' bor: @"
            + username
        )

    # ismda admin bo'lsa
    if "admin" in full_name:
        return True, (
            "ismda 'admin' bor: "
            + (full_name or "belgilanmagan")
        )

    return False, ""


# ==============================
# ADMINLARGA XABAR
# ==============================

async def notify_admins(
    context,
    chat_title,
    user,
    reason
):
    if not user:
        return

    username_text = (
        "@{}".format(user.username)
        if user.username
        else "username yo'q"
    )

    text = (
        "🚫 *{}* dan {} banlandi\n"
        "📌 Sabab: {}\n"
        "👤 Ism: {}\n"
        "🆔 ID: {}"
    ).format(
        escape_markdown(
            chat_title or "noma'lum guruh"
        ),
        escape_markdown(username_text),
        escape_markdown(reason),
        escape_markdown(
            user.first_name or "belgilanmagan"
        ),
        user.id
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="Markdown"
            )

            print(
                f"📩 Admin {admin_id} ga xabar yuborildi"
            )

        except Exception as e:
            print(
                f"❌ Admin {admin_id} ga xabar yuborilmadi: {e}"
            )


# ==============================
# /START
# ==============================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    await update.message.reply_text(
        "🤖 ModerBot ishlayapti!\n\n"
        "🛡 @user_... username'lar bloklanadi.\n"
        "🛡 Ismida yoki username'ida "
        "'admin' bor akkauntlar bloklanadi.\n"
        "🛡 Spam so'zlar yozgan "
        "foydalanuvchilar bloklanadi."
    )


# ==============================
# SPAM XABARLARNI TEKSHIRISH
# ==============================

async def check_spam_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.message

    if not message:
        return

    if not message.chat:
        return

    if message.chat.type not in (
        "group",
        "supergroup"
    ):
        return

    if not message.from_user:
        return

    # Adminni tekshirmaymiz
    if message.from_user.id in ADMIN_IDS:
        return

    text = (
        message.text
        or message.caption
        or ""
    )

    if not text:
        return

    spam_found = contains_spam(text)

    if spam_found:
        reason = (
            "spam so'zlar: "
            + ", ".join(spam_found)
        )

        await handle_violation(
            update,
            context,
            reason
        )


# ==============================
# QOIDA BUZILGANDA
# ==============================

async def handle_violation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    reason
):
    if not update.message:
        return

    user = update.message.from_user
    chat = update.message.chat
    message_id = update.message.message_id

    if not user:
        return

    username_text = (
        "@{}".format(user.username)
        if user.username
        else "username yo'q"
    )

    # Adminni ban qilmaymiz
    if user.id in ADMIN_IDS:
        print(
            f"⚠️ Admin tekshirildi: {reason}"
        )
        return

    # ==========================
    # 1. XABARNI O'CHIRISH
    # ==========================

    try:
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=message_id
        )

        print(
            f"🗑 Xabar o'chirildi: {message_id}"
        )

    except Exception as e:
        print(
            f"❌ Xabarni o'chirishda xatolik: {e}"
        )

    # ==========================
    # 2. BAN
    # ==========================

    try:
        await context.bot.ban_chat_member(
            chat_id=chat.id,
            user_id=user.id
        )

        print("====================================")
        print("🚫 BAN QILINDI")
        print(f"👤 Ism: {user.first_name}")
        print(f"🔗 Username: {username_text}")
        print(f"🆔 ID: {user.id}")
        print(f"📌 Sabab: {reason}")
        print("====================================")

    except Exception as e:
        print(
            f"❌ Ban qilishda xatolik: {e}"
        )

        print(
            "⚠️ Bot guruhda ADMIN emas yoki "
            "'Ban users' huquqi yo'q!"
        )

        return

    # ==========================
    # 3. ADMINGA XABAR
    # ==========================

    await notify_admins(
        context,
        chat.title,
        user,
        reason
    )

    # ==========================
    # 4. USERGA SHAXSIY XABAR
    # ==========================

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "⛔ Siz {} guruhidan ban qilindingiz.\n"
                "📌 Sabab: {}\n"
                "❓ Muammo bo'lsa admin bilan bog'laning."
            ).format(
                chat.title or "guruh",
                reason
            )
        )

    except Exception:
        pass


# ==============================
# YANGI A'ZONI TEKSHIRISH
# ==============================

async def check_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat_member = update.chat_member

    if not chat_member:
        return

    old_status = (
        chat_member.old_chat_member.status
    )

    new_status = (
        chat_member.new_chat_member.status
    )

    if new_status not in (
        "member",
        "restricted"
    ):
        return

    if old_status not in (
        "left",
        "kicked",
        "banned"
    ):
        return

    user = (
        chat_member.new_chat_member.user
    )

    ban, reason = should_ban(user)

    if not ban:
        return

    username_text = (
        "@{}".format(user.username)
        if user.username
        else "username yo'q"
    )

    # ==========================
    # BAN
    # ==========================

    try:
        await context.bot.ban_chat_member(
            chat_id=chat_member.chat.id,
            user_id=user.id
        )

        print("====================================")
        print("🚫 YANGI A'ZO BAN QILINDI")
        print(f"👤 Ism: {user.first_name}")
        print(f"🔗 Username: {username_text}")
        print(f"🆔 ID: {user.id}")
        print(f"📌 Sabab: {reason}")
        print("====================================")

    except Exception as e:
        print(
            f"❌ Ban qilishda xatolik: {e}"
        )

        print(
            "⚠️ Bot ADMIN emas yoki "
            "'Ban users' huquqiga ega emas!"
        )

        return

    # ==========================
    # ADMINGA XABAR
    # ==========================

    await notify_admins(
        context,
        chat_member.chat.title,
        user,
        reason
    )

    # ==========================
    # USERGA XABAR
    # ==========================

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "⛔ Siz {} guruhidan ban qilindingiz.\n"
                "📌 Sabab: {}\n"
                "❓ Muammo bo'lsa admin bilan bog'laning."
            ).format(
                chat_member.chat.title or "guruh",
                reason
            )
        )

    except Exception:
        pass


# ==============================
# BOTNI ISHGA TUSHIRISH
# ==============================

async def start():
    print("====================================")
    print("🤖 ModerBot-1 ishga tushmoqda...")
    print("====================================")

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # /start
    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    # Yangi a'zolar
    application.add_handler(
        ChatMemberHandler(
            check_new_member,
            ChatMemberHandler.CHAT_MEMBER
        )
    )

    # Spam xabarlar
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_spam_message
        )
    )

    print("✅ ModerBot-1 tayyor!")
    print("🛡 @user_... bloklanadi")
    print("🛡 'admin' ism/username bloklanadi")
    print(
        f"🛡 {len(SPAM_WORDS)} ta spam so'z tekshiriladi"
    )
    print(f"👤 Admin ID: {ADMIN_IDS}")
    print("📡 Telegram polling boshlandi...")

    await application.initialize()
    await application.start()

    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES
    )

    # Botni doimiy ishlatish
    await asyncio.Event().wait()
