import asyncio
from pathlib import Path
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telethon import TelegramClient

BOT2_TOKEN = "8992607786:AAHign6aDhQHvoAZhERw6PP8pdtclKYAB8U"
API_ID = 946606
API_HASH = "a183e9d1503a9c6514bd086dd03aeb8e"
OWNER_ID = 1072547777

DIR = Path("bot_2")
DIR.mkdir(exist_ok=True)

# Aktiv akkauntlarni ushlab turish uchun dict
clients = {}

def ok(u: Update):
    return u.effective_user and u.effective_user.id == OWNER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text("✅ <b>Bot2 ishlayapti!</b>\nBarcha buyruqlar: /help", parse_mode="HTML")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text(
        "🛠 <b>Asosiy buyruqlar:</b>\n\n"
        "<code>/login</code> — Yangi session ulash\n"
        "<code>/accounts</code> — Ulangan akkauntlar ro'yxati\n"
        "<code>/use NOMI</code> — Akkauntni tanlash\n"
        "<code>/status</code> — Tanlangan akkaunt holati\n"
        "<code>/id</code> — Telegram ID'ni ko'rish\n"
        "<code>/info</code> — Akkaunt ma'lumotlari\n"
        "<code>/logout</code> — Akkauntni tizimdan o'chirish\n"
        "<code>/ping</code> — Bot ishlashini tekshirish\n"
        "<code>/gps</code> — GPS manzil jo'natish",
        parse_mode="HTML"
    )

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    context.user_data["login"] = True
    await update.message.reply_text("📁 Iltimos, <b>.session</b> faylini yuboring.", parse_mode="HTML")

async def session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update) or not context.user_data.get("login"):
        return

    f = update.message.document

    if not f.file_name.endswith(".session"):
        await update.message.reply_text("❌ Faqat <b>.session</b> formatidagi fayl qabul qilinadi!", parse_mode="HTML")
        return

    context.user_data["login"] = False
    name = Path(f.file_name).stem
    path = DIR / f"{name}.session"

    tgfile = await context.bot.get_file(f.file_id)
    await tgfile.download_to_drive(str(path))

    msg = await update.message.reply_text("⏳ Ulanmoqda, kuting...")

    client = TelegramClient(str(path.with_suffix("")), API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            path.unlink(missing_ok=True)
            await msg.edit_text("❌ Session yaroqsiz yoki avtorizatsiyadan o'tmagan!")
            return

        me = await client.get_me()
        clients[name] = client
        context.user_data["selected"] = name  # Yuklangan akkauntni avtomatik tanlab qo'yamiz

        await msg.edit_text(
            f"✅ <b>Muvaffaqiyatli ulandi!</b>\n\n"
            f"📁 Sessiya: <b>{name}</b>\n"
            f"👤 Ism: {me.first_name or 'Yo‘q'}\n"
            f"🆔 ID: <code>{me.id}</code>\n\n"
            f"<i>Ushbu account avtomatik tanlandi.</i>",
            parse_mode="HTML"
        )

    except Exception as e:
        await msg.edit_text(f"❌ Xatolik yuz berdi: {e}")

async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    if not clients:
        await update.message.reply_text("📭 Hozircha akkauntlar yo'q.")
        return

    text = "👤 <b>Sizning akkauntlaringiz:</b>\n\n"
    for name in clients:
        # Tanlangan akkauntga ✅ belgisi qo'yiladi
        sel = "✅" if context.user_data.get("selected") == name else "🔹"
        text += f"{sel} <code>{name}</code>\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    if not context.args:
        await update.message.reply_text("⚠️ <b>Foydalanish:</b> <code>/use SESSION_NOMI</code>", parse_mode="HTML")
        return

    name = context.args[0]

    if name not in clients:
        await update.message.reply_text("❌ Bunday akkaunt topilmadi!")
        return

    context.user_data["selected"] = name
    await update.message.reply_text(f"✅ <b>{name}</b> akkaunti tanlandi!", parse_mode="HTML")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    selected = context.user_data.get("selected")
    if not selected:
        await update.message.reply_text("❌ Akkaunt tanlanmagan. Iltimos, <code>/use</code> orqali tanlang.", parse_mode="HTML")
        return

    c = clients.get(selected)
    
    await update.message.reply_text(
        f"📡 <b>{selected}</b> holati:\n"
        f"{'🟢 Ulangan (Onlayn)' if c and c.is_connected() else '🔴 Ulanmagan (Oflayn)'}",
        parse_mode="HTML"
    )

async def tg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    selected = context.user_data.get("selected")
    if not selected or selected not in clients:
        await update.message.reply_text("❌ Akkaunt tanlanmagan.")
        return

    me = await clients[selected].get_me()
    await update.message.reply_text(f"🆔 Akkaunt ID'si: <code>{me.id}</code>", parse_mode="HTML")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    selected = context.user_data.get("selected")
    if not selected or selected not in clients:
        await update.message.reply_text("❌ Akkaunt tanlanmagan.")
        return

    me = await clients[selected].get_me()
    await update.message.reply_text(
        f"👤 Ism: {me.first_name or ''}\n"
        f"🔹 User: @{me.username or 'yo‘q'}\n"
        f"🆔 ID: <code>{me.id}</code>\n"
        f"📱 Raqam: +{me.phone or 'yashirilgan'}",
        parse_mode="HTML"
    )

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    selected = context.user_data.get("selected")
    if not selected or selected not in clients:
        await update.message.reply_text("❌ Akkaunt tanlanmagan.")
        return

    name = selected
    await clients[name].disconnect()
    del clients[name]

    (DIR / f"{name}.session").unlink(missing_ok=True)
    context.user_data["selected"] = None

    await update.message.reply_text(f"🗑 <b>{name}</b> akkaunti tizimdan o'chirildi.", parse_mode="HTML")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ok(update):
        await update.message.reply_text("🏓 Pong 🟢 Bot faol holatda!")

async def gps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    kb = [[KeyboardButton("📍 Joylashuvni yuborish", request_location=True)]]
    await update.message.reply_text(
        "GPS manzilni yuborish uchun pastdagi tugmani bosing:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return

    x = update.message.location
    link = f"https://www.google.com/maps?q={x.latitude},{x.longitude}"

    await update.message.reply_text(
        f"📍 <b>Koordinatalar:</b>\n{x.latitude}, {x.longitude}\n\n"
        f"🗺 <a href='{link}'>Google Maps orqali ko'rish</a>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

# Bot ishga tushayotganda oldin kiritilgan .session fayllarini orqaga qaytarib ishga tushirish uchun
async def load_sessions(app: Application):
    print("⏳ Sessiyalar tekshirilmoqda...")
    for p in DIR.glob("*.session"):
        name = p.stem
        client = TelegramClient(str(p.with_suffix("")), API_ID, API_HASH)
        try:
            await client.connect()
            if await client.is_user_authorized():
                clients[name] = client
                print(f"✅ Yuklandi: {name}")
            else:
                await client.disconnect()
                print(f"❌ Yaroqsiz (o'chirildi): {name}")
        except Exception as e:
            print(f"❌ Xatolik ({name}): {e}")
    print("🚀 BOT TO'LIQ ISHGA TUSHDI")


def main():
    # post_init yordamida bot ishga tushishidan oldin sessiyalarni yuklaymiz
    app = Application.builder().token(BOT2_TOKEN).post_init(load_sessions).build()

    cmds = {
        "start": start,
        "help": help_cmd,
        "login": login,
        "accounts": accounts,
        "use": use,
        "status": status,
        "id": tg_id,
        "info": info,
        "logout": logout,
        "ping": ping,
        "gps": gps,
    }

    for name, func in cmds.items():
        app.add_handler(CommandHandler(name, func))

    # Xabarlar ushlagichlari
    app.add_handler(MessageHandler(filters.Document.ALL, session))
    app.add_handler(MessageHandler(filters.LOCATION, location))

    # Standart asinxron ishga tushirish (xatoliksiz va xavfsiz mexanizm)
    app.run_polling()


if __name__ == "__main__":
    main()
    
