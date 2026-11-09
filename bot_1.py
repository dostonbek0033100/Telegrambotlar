import os
import re
import asyncio
import json
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT1_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT1_TOKEN environment variable topilmadi!")

ADMIN_IDS = {1072547777}

# Shu so‘zlar bor xabarlar o‘chiriladi.
# Yangi reklama iboralarini shu ro‘yxatga qo‘shishing mumkin.
SPAM_WORDS = [
    "xxx",
    "adult",
    "18+",
    "profilimda video bor",
]

STATE_FILE = Path(
    os.getenv("MODERBOT_STATE_FILE", "moderbot_state.json")
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("moderbot")


def load_enabled():
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return True
        enabled = data.get("enabled", True)
        return enabled if isinstance(enabled, bool) else True
    except (OSError, ValueError, TypeError):
        return True


def save_enabled(enabled):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_name(STATE_FILE.name + ".tmp")
        tmp.write_text(
            json.dumps({"enabled": enabled}),
            encoding="utf-8",
        )
        tmp.replace(STATE_FILE)
        return True
    except OSError:
        logger.exception("Holatni saqlab bo‘lmadi")
        return False


MODERATION_ENABLED = load_enabled()


def contains_spam(text):
    text_lower = text.casefold()
    found = []

    for word in SPAM_WORDS:
        w = word.strip().casefold()
        if not w:
            continue

        if re.fullmatch(r"[a-z0-9 ]+", w):
            pattern = (
                r"(?<!\w)"
                + re.escape(w)
                + r"(?!\w)"
            )
            if re.search(pattern, text_lower):
                found.append(word)
        elif w in text_lower:
            found.append(word)

    return found


def should_ban(user):
    """Faqat yangi kirgan a’zolar uchun oldingi qoida."""
    username = (user.username or "").lower().strip()
    full_name = (
        f'{user.first_name or ""} {user.last_name or ""}'
    ).lower().strip()

    if username.startswith("user_"):
        return True, "username user_ bilan boshlanadi"

    if "admin" in username:
        return True, "username'da 'admin' bor: @" + username

    if "admin" in full_name:
        return True, "ismda 'admin' bor: " + full_name

    return False, ""


async def notify_admins(context, chat_title, user, reason):
    if not user:
        return

    username = (
        f"@{user.username}"
        if user.username
        else "username yo‘q"
    )

    text = (
        f"🚫 {chat_title or 'Noma’lum guruh'} dan a’zo banlandi\n"
        f"📌 Sabab: {reason}\n"
        f"👤 Ism: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
            )
        except Exception:
            logger.exception(
                "Admin %s ga xabar yuborilmadi",
                admin_id,
            )


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    if not message:
        return

    await message.reply_text(
        "🤖 ModerBot ishlayapti!\n\n"
        "🧹 Ro‘yxatdagi spam/reklama so‘zlari bor "
        "xabarlar o‘chiriladi.\n"
        "✅ Reklama yozgan foydalanuvchi bloklanmaydi.\n"
        "📝 Tahrirlangan xabarlar ham tekshiriladi.\n\n"
        "🛡 Yangi a’zolar uchun:\n"
        "• Username user_ bilan boshlansa — ban.\n"
        "• Ismida yoki username’ida admin bo‘lsa — ban.\n\n"
        "🔐 Admin buyruqlari:\n"
        "/toxta — moderatsiyani to‘xtatish\n"
        "/davom — moderatsiyani yoqish\n"
        "/holat — holatni ko‘rish\n\n"
        "🧹 Shaxsiy chatda bot xabariga javoban "
        "/reklama — o‘sha xabarni o‘chirish"
    )


async def admin_only(update: Update):
    user = update.effective_user
    if user and user.id in ADMIN_IDS:
        return True

    if update.effective_message:
        await update.effective_message.reply_text(
            "⛔ Bu buyruq faqat administrator uchun."
        )
    return False


async def toxta_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    global MODERATION_ENABLED

    if not await admin_only(update):
        return

    message = update.effective_message
    if not message:
        return

    if not MODERATION_ENABLED:
        await message.reply_text(
            "⏸ Moderatsiya allaqachon to‘xtatilgan.\n"
            "▶️ Yoqish: /davom"
        )
        return

    MODERATION_ENABLED = False
    persisted = save_enabled(False)

    text = (
        "⏸ Moderatsiya to‘xtatildi.\n"
        "Reklamalarni o‘chirish va yangi a’zolarni "
        "avtomatik bloklash o‘chirilgan.\n"
        "▶️ Qayta yoqish: /davom"
    )
    if not persisted:
        text += (
            "\n⚠️ Holat saqlanmadi. Restartdan keyin "
            "oldingi holat tiklanishi mumkin."
        )

    await message.reply_text(text)


async def davom_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    global MODERATION_ENABLED

    if not await admin_only(update):
        return

    message = update.effective_message
    if not message:
        return

    if MODERATION_ENABLED:
        await message.reply_text(
            "✅ Moderatsiya allaqachon ishlayapti."
        )
        return

    MODERATION_ENABLED = True
    persisted = save_enabled(True)

    text = (
        "▶️ Moderatsiya qayta yoqildi.\n"
        "🧹 Reklama xabarlari o‘chiriladi.\n"
        "✅ Reklama yozgan odam bloklanmaydi.\n"
        "🛡 Yangi a’zolarni tekshirish faol."
    )
    if not persisted:
        text += "\n⚠️ Holat diskka saqlanmadi."

    await message.reply_text(text)


async def holat_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    message = update.effective_message
    if not message:
        return

    status = (
        "🟢 Moderatsiya FAOL"
        if MODERATION_ENABLED
        else "⏸ Moderatsiya TO‘XTATILGAN"
    )

    await message.reply_text(
        f"{status}\n\n"
        f"📋 Spam so‘zlar: {len(SPAM_WORDS)} ta\n"
        "🧹 Reklama uchun: faqat xabar o‘chiriladi.\n"
        "🛡 Yangi a’zolar uchun ism/username "
        "bo‘yicha ban qoidasi mavjud."
    )


async def reklama_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Shaxsiy chatdagi bot xabarini reply orqali o‘chirish."""
    message = update.effective_message
    chat = update.effective_chat

    if not message or not chat:
        return

    if chat.type != "private":
        await message.reply_text(
            "🧹 /reklama ModerBot bilan shaxsiy chatda ishlaydi.\n"
            "Guruhdagi spam xabarlar avtomatik tekshiriladi."
        )
        return

    target = message.reply_to_message
    if target is None:
        await message.reply_text(
            "O‘chirmoqchi bo‘lgan bot xabariga "
            "«Javob berish / Reply» ni bosib, "
            "/reklama deb yubor."
        )
        return

    sender = target.from_user
    if not sender or sender.id != context.bot.id:
        await message.reply_text(
            "⚠️ Bu xabarni ModerBot yubormagan."
        )
        return

    try:
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=target.message_id,
        )
    except Exception:
        logger.exception("Shaxsiy chatdagi xabar o‘chirilmadi")
        await message.reply_text(
            "❌ Xabarni o‘chirib bo‘lmadi. "
            "Xabar eskirgan, allaqachon o‘chirilgan yoki "
            "Telegram chekloviga tushgan bo‘lishi mumkin."
        )
        return

    await message.reply_text("✅ Xabar o‘chirildi.")


async def check_spam_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Reklamani faqat o‘chiradi. Foydalanuvchini ban qilmaydi."""
    if not MODERATION_ENABLED:
        return

    # Oddiy va tahrirlangan xabarlarni oladi.
    message = update.effective_message
    if not message or message.chat.type not in (
        "group",
        "supergroup",
    ):
        return

    # Belgilangan bot administratorlari tekshirilmaydi.
    if (
        message.from_user
        and message.from_user.id in ADMIN_IDS
    ):
        return

    # Anonim guruh administratori yuborgan xabarni o‘tkazib yuboradi.
    if (
        message.sender_chat
        and message.sender_chat.id == message.chat.id
    ):
        return

    text = message.text or message.caption or ""
    if not text:
        return

    spam_found = contains_spam(text)
    if not spam_found:
        return

    try:
        await context.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        logger.info(
            "Reklama o‘chirildi: chat=%s, msg=%s, sabab=%s",
            message.chat.id,
            message.message_id,
            ", ".join(spam_found),
        )
    except Exception:
        logger.exception(
            "Reklama o‘chirilmadi: chat=%s, msg=%s",
            message.chat.id,
            message.message_id,
        )

    # Bu yerda ban_chat_member chaqirilmaydi.


def is_current_member(member):
    if member.status in ("member", "administrator", "creator"):
        return True
    return (
        member.status == "restricted"
        and bool(getattr(member, "is_member", False))
    )


async def check_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Yangi kirgan a’zolar uchun avvalgi ban qoidasi."""
    if not MODERATION_ENABLED:
        return

    member_update = update.chat_member
    if not member_update:
        return

    if member_update.chat.type not in ("group", "supergroup"):
        return

    old_member = member_update.old_chat_member
    new_member = member_update.new_chat_member

    # Faqat guruhga yangi kirish holatini tekshirish.
    if is_current_member(old_member):
        return
    if not is_current_member(new_member):
        return
    if new_member.status in ("administrator", "creator"):
        return

    user = new_member.user
    if user.id in ADMIN_IDS or user.id == context.bot.id:
        return

    ban, reason = should_ban(user)
    if not ban or not MODERATION_ENABLED:
        return

    chat = member_update.chat

    try:
        await context.bot.ban_chat_member(
            chat_id=chat.id,
            user_id=user.id,
        )
        logger.info(
            "Yangi a’zo banlandi: chat=%s, user=%s, sabab=%s",
            chat.id,
            user.id,
            reason,
        )
    except Exception:
        logger.exception(
            "Yangi a’zoni ban qilib bo‘lmadi: user=%s",
            user.id,
        )
        return

    await notify_admins(
        context,
        chat.title,
        user,
        reason,
    )

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"⛔ Siz {chat.title or 'guruh'} "
                f"guruhidan ban qilindingiz.\n"
                f"📌 Sabab: {reason}\n"
                "❓ Muammo bo‘lsa admin bilan bog‘laning."
            ),
        )
    except Exception:
        # Foydalanuvchi botni boshlamagan bo‘lishi mumkin.
        pass


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    error = context.error
    if error:
        logger.error(
            "Yangilanishni qayta ishlashda xatolik",
            exc_info=(type(error), error, error.__traceback__),
        )


def build_application():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start_command)
    )
    application.add_handler(
        CommandHandler("toxta", toxta_command)
    )
    application.add_handler(
        CommandHandler("davom", davom_command)
    )
    application.add_handler(
        CommandHandler("holat", holat_command)
    )
    application.add_handler(
        CommandHandler("reklama", reklama_command)
    )
    application.add_handler(
        ChatMemberHandler(
            check_new_member,
            ChatMemberHandler.CHAT_MEMBER,
        )
    )

    # Alohida guruh: buyruq ko‘rinishidagi spam ham tekshiriladi.
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & (filters.TEXT | filters.CAPTION),
            check_spam_message,
        ),
        group=1,
    )

    application.add_error_handler(error_handler)
    return application


async def start():
    """Boshqa Python dasturidan await start() bilan ishga tushirish."""
    application = build_application()

    async with application:
        try:
            await application.start()
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
            )
            logger.info("ModerBot ishga tushdi")
            await asyncio.Event().wait()
        finally:
            if application.updater.running:
                await application.updater.stop()
            if application.running:
                await application.stop()


if __name__ == "__main__":
    app = build_application()
    logger.info(
        "ModerBot ishga tushmoqda. Moderatsiya: %s",
        "faol" if MODERATION_ENABLED else "to‘xtatilgan",
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)