import os
import re
import asyncio
import json
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ChatMemberHandler,
    MessageHandler, ContextTypes, filters,
)
from telegram.helpers import escape_markdown

BOT_TOKEN = os.getenv('BOT1_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('BOT1_TOKEN environment variable topilmadi!')

ADMIN_IDS = {1072547777}
SPAM_WORDS = ['xxx', 'adult', '18+', 'profilimda video bor']
STATE_FILE = Path(os.getenv('MODERBOT_STATE_FILE', 'moderbot_state.json'))


def load_enabled():
    try:
        return bool(json.loads(STATE_FILE.read_text(encoding='utf-8')).get('enabled', True))
    except (OSError, ValueError, TypeError):
        return True


def save_enabled(enabled):
    try:
        tmp = STATE_FILE.with_name(STATE_FILE.name + '.tmp')
        tmp.write_text(json.dumps({'enabled': enabled}), encoding='utf-8')
        tmp.replace(STATE_FILE)
        return True
    except OSError as exc:
        print(f'⚠️ Holatni saqlab bo‘lmadi: {exc}')
        return False


MODERATION_ENABLED = load_enabled()


def contains_spam(text):
    text_lower = text.lower()
    found = []
    for word in SPAM_WORDS:
        w = word.lower()
        if re.fullmatch(r'[a-z0-9 ]+', w):
            pattern = r'(?<![a-z0-9])' + re.escape(w) + r'(?![a-z0-9])'
            if re.search(pattern, text_lower):
                found.append(word)
        elif w in text_lower:
            found.append(word)
    return found


def should_ban(user):
    username = (user.username or '').lower().strip()
    full_name = f'{user.first_name or ""} {user.last_name or ""}'.lower().strip()
    if username.startswith('user_'):
        return True, 'username user_ bilan boshlanadi'
    if 'admin' in username:
        return True, "username'da 'admin' bor: @" + username
    if 'admin' in full_name:
        return True, "ismda 'admin' bor: " + (full_name or 'belgilanmagan')
    return False, ''


async def notify_admins(context, chat_title, user, reason):
    if not user:
        return
    username_text = f'@{user.username}' if user.username else "username yo'q"
    text = (
        '🚫 *{}* dan {} banlandi\n📌 Sabab: {}\n👤 Ism: {}\n🆔 ID: {}'
    ).format(
        escape_markdown(chat_title or "noma'lum guruh"),
        escape_markdown(username_text),
        escape_markdown(reason),
        escape_markdown(user.first_name or 'belgilanmagan'),
        user.id,
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=text, parse_mode='Markdown')
            print(f'📩 Admin {admin_id} ga xabar yuborildi')
        except Exception as exc:
            print(f'❌ Admin {admin_id} ga xabar yuborilmadi: {exc}')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "🤖 ModerBot ishlayapti!\n\n"
            "🛡 @user_... username'lar bloklanadi.\n"
            "🛡 Ismida yoki username'ida 'admin' bor akkauntlar bloklanadi.\n"
            "🛡 Spam so'zlar yozgan foydalanuvchilar bloklanadi.\n\n"
            "🔐 Admin buyruqlari: /toxta /davom /holat"
        )


async def admin_only(update):
    if not update.effective_user or update.effective_user.id not in ADMIN_IDS:
        if update.effective_message:
            await update.effective_message.reply_text('⛔ Bu buyruq faqat administrator uchun.')
        return False
    return True


async def toxta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODERATION_ENABLED
    if not await admin_only(update):
        return
    if not MODERATION_ENABLED:
        await update.effective_message.reply_text('⏸ Moderatsiya allaqachon to‘xtatilgan. /davom bilan yoq.')
        return
    MODERATION_ENABLED = False
    persisted = save_enabled(False)
    await update.effective_message.reply_text(
        '⏸ Moderatsiya vaqtincha to‘xtatildi.\n'
        'Spam tekshirish va avtomatik ban o‘chirilgan.\n'
        '▶️ Qayta yoqish: /davom' +
        ('' if persisted else '\n⚠️ Holat diskka saqlanmadi; restartdan keyin qayta yoqilishi mumkin.')
    )


async def davom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODERATION_ENABLED
    if not await admin_only(update):
        return
    if MODERATION_ENABLED:
        await update.effective_message.reply_text('✅ Moderatsiya allaqachon ishlayapti.')
        return
    MODERATION_ENABLED = True
    persisted = save_enabled(True)
    await update.effective_message.reply_text(
        '▶️ Moderatsiya qayta yoqildi.\n🛡 Spam tekshirish va avtomatik ban faol.' +
        ('' if persisted else '\n⚠️ Holat diskka saqlanmadi.')
    )


async def holat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    await update.effective_message.reply_text(
        '🟢 Moderatsiya FAOL' if MODERATION_ENABLED else '⏸ Moderatsiya TO‘XTATILGAN'
    )


async def check_spam_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not MODERATION_ENABLED:
        return
    message = update.message
    if not message or not message.chat or message.chat.type not in ('group', 'supergroup'):
        return
    if not message.from_user or message.from_user.id in ADMIN_IDS:
        return
    text = message.text or message.caption or ''
    if not text:
        return
    spam_found = contains_spam(text)
    if spam_found:
        await handle_violation(update, context, 'spam so‘zlar: ' + ', '.join(spam_found))


async def handle_violation(update: Update, context: ContextTypes.DEFAULT_TYPE, reason):
    if not MODERATION_ENABLED or not update.message:
        return
    user = update.message.from_user
    chat = update.message.chat
    message_id = update.message.message_id
    if not user or user.id in ADMIN_IDS:
        return
    username_text = f'@{user.username}' if user.username else "username yo'q"
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message_id)
        print(f'🗑 Xabar o‘chirildi: {message_id}')
    except Exception as exc:
        print(f'❌ Xabarni o‘chirishda xatolik: {exc}')
    if not MODERATION_ENABLED:
        return
    try:
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=user.id)
        print('====================================')
        print('🚫 BAN QILINDI')
        print(f'👤 Ism: {user.first_name}')
        print(f'🔗 Username: {username_text}')
        print(f'🆔 ID: {user.id}')
        print(f'📌 Sabab: {reason}')
        print('====================================')
    except Exception as exc:
        print(f'❌ Ban qilishda xatolik: {exc}')
        print("⚠️ Bot ADMIN emas yoki 'Ban users' huquqi yo‘q!")
        return
    await notify_admins(context, chat.title, user, reason)
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f'⛔ Siz {chat.title or "guruh"} guruhidan ban qilindingiz.\n📌 Sabab: {reason}\n❓ Muammo bo‘lsa admin bilan bog‘laning.',
        )
    except Exception:
        pass


async def check_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not MODERATION_ENABLED:
        return
    chat_member = update.chat_member
    if not chat_member:
        return
    old_status = chat_member.old_chat_member.status
    new_status = chat_member.new_chat_member.status
    if new_status not in ('member', 'restricted'):
        return
    if old_status not in ('left', 'kicked', 'banned'):
        return
    user = chat_member.new_chat_member.user
    if user.id in ADMIN_IDS:
        return
    ban, reason = should_ban(user)
    if not ban or not MODERATION_ENABLED:
        return
    username_text = f'@{user.username}' if user.username else "username yo'q"
    try:
        await context.bot.ban_chat_member(chat_id=chat_member.chat.id, user_id=user.id)
        print('====================================')
        print("🚫 YANGI A'ZO BAN QILINDI")
        print(f'👤 Ism: {user.first_name}')
        print(f'🔗 Username: {username_text}')
        print(f'🆔 ID: {user.id}')
        print(f'📌 Sabab: {reason}')
        print('====================================')
    except Exception as exc:
        print(f'❌ Ban qilishda xatolik: {exc}')
        print("⚠️ Bot ADMIN emas yoki 'Ban users' huquqiga ega emas!")
        return
    await notify_admins(context, chat_member.chat.title, user, reason)
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f'⛔ Siz {chat_member.chat.title or "guruh"} guruhidan ban qilindingiz.\n📌 Sabab: {reason}\n❓ Muammo bo‘lsa admin bilan bog‘laning.',
        )
    except Exception:
        pass


async def start():
    print('====================================')
    print('🤖 ModerBot-1 ishga tushmoqda...')
    print('====================================')
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('toxta', toxta_command))
    application.add_handler(CommandHandler('davom', davom_command))
    application.add_handler(CommandHandler('holat', holat_command))
    application.add_handler(ChatMemberHandler(check_new_member, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.CAPTION, check_spam_message))
    print('✅ ModerBot-1 tayyor!')
    print(f'🛡 {len(SPAM_WORDS)} ta spam so‘z tekshiriladi')
    print(f'👤 Admin ID: {ADMIN_IDS}')
    print('📡 Telegram polling boshlandi...')
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(start())
