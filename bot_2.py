import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telethon import TelegramClient, events
from telethon.tl.types import InputGeoPoint, InputMediaGeoPoint

BOT2_TOKEN = "8992607786:AAHign6aDhQHvoAZhERw6PP8pdtclKYAB8U"
API_ID = 946606
API_HASH = "a183e9d1503a9c6514bd086dd03aeb8e"
OWNER_ID = 1072547777

DIR = Path("bot_2")
DIR.mkdir(exist_ok=True)

clients = {}

def ok(u: Update):
    return u.effective_user and u.effective_user.id == OWNER_ID

# ================= USERBOT (AKKAUNT) FUNKSIYALARI =================

async def userbot_gps_handler(event):
    # O'zingiz xohlagan joyning koordinatalarini shu yerga kiritasiz (Hozir Farg'ona kiritilgan)
    lat = 40.3842
    lon = 71.7843
    
    # Telegram xarita obyekti
    geo = InputMediaGeoPoint(InputGeoPoint(lat, lon))
    
    # Siz yozgan "/gps" xabarini o'chirib tashlaydi
    await event.delete()
    
    # O'rniga xaritani jo'natadi
    await event.respond(file=geo)

def add_userbot_handlers(client: TelegramClient):
    # outgoing=True -> faqat siz (akkaunt egasi) yozganda ishlaydi
    client.add_event_handler(userbot_gps_handler, events.NewMessage(pattern=r"(?i)^/gps", outgoing=True))

# ================= BOT KOMANDALARI =================

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text("✅ <b>Bot_2 ishlayapti!</b>\nBarcha buyruqlar: /help", parse_mode="HTML")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text(
        "🛠 <b>Asosiy buyruqlar:</b>\n"
        "/login — Yangi session ulash\n"
        "/accounts — Ulangan akkauntlar\n"
        "/use NOMI — Akkauntni tanlash\n"
        "/status — Akkaunt holati\n"
        "/id — Telegram ID\n"
        "/info — Akkaunt ma'lumoti\n"
        "/logout — Akkauntni o'chirish\n"
        "/ping — Ping tekshirish\n\n"
        "<i>Eslatma: /gps komandasini endi ulangan akkauntingiz orqali istalgan chatda ishlatsangiz bo'ladi.</i>",
        parse_mode="HTML"
    )

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    context.user_data["login"] = True
    await update.message.reply_text("📁 Iltimos, <b>.session</b> faylini yuboring.", parse_mode="HTML")

async def session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update) or not context.user_data.get("login"): return

    f = update.message.document
    if not f.file_name.endswith(".session"):
        await update.message.reply_text("❌ Faqat <b>.session</b> fayl qabul qilinadi!", parse_mode="HTML")
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
        
        # Userbot handlerlarini ulash va fon rejimida eshitishni boshlash
        add_userbot_handlers(client)
        asyncio.create_task(client.run_until_disconnected())
        
        clients[name] = client
        context.user_data["selected"] = name

        await msg.edit_text(f"✅ <b>Muvaffaqiyatli ulandi!</b>\n📁 Sessiya: <b>{name}</b>\n🆔 ID: <code>{me.id}</code>", parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {e}")

async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    if not clients:
        await update.message.reply_text("📭 Akkauntlar yo'q.")
        return

    text = "👤 <b>Akkauntlaringiz:</b>\n"
    for name in clients:
        sel = "✅" if context.user_data.get("selected") == name else "🔹"
        text += f"{sel} <code>{name}</code>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    if not context.args:
        await update.message.reply_text("⚠️ /use SESSION_NOMI")
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
        await update.message.reply_text("❌ Akkaunt tanlanmagan.")
        return

    c = clients.get(selected)
    await update.message.reply_text(f"📡 <b>{selected}</b>\n{'🟢 Ulangan' if c and c.is_connected() else '🔴 Ulanmagan'}", parse_mode="HTML")

async def tg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    
    me = await clients[selected].get_me()
    await update.message.reply_text(f"🆔 <code>{me.id}</code>", parse_mode="HTML")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")

    me = await clients[selected].get_me()
    await update.message.reply_text(f"👤 {me.first_name or ''}\n🔹 @{me.username or 'yo‘q'}\n🆔 <code>{me.id}</code>\n📱 +{me.phone or 'yashirilgan'}", parse_mode="HTML")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")

    await clients[selected].disconnect()
    del clients[selected]
    (DIR / f"{selected}.session").unlink(missing_ok=True)
    
    await update.message.reply_text(f"🗑 <b>{selected}</b> o'chirildi.", parse_mode="HTML")
    context.user_data["selected"] = None

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ok(update): await update.message.reply_text("🏓 Pong 🟢 Bot_2 faol!")

# ================= SESSIYALARNI TIKLASH =================
async def load_sessions(app: Application):
    for p in DIR.glob("*.session"):
        name = p.stem
        client = TelegramClient(str(p.with_suffix("")), API_ID, API_HASH)
        try:
            await client.connect()
            if await client.is_user_authorized():
                add_userbot_handlers(client)
                asyncio.create_task(client.run_until_disconnected())
                clients[name] = client
            else:
                await client.disconnect()
        except Exception: pass

# ================= MAIN.PY CHAQIRADIGAN FUNKSIYA =================
async def start():
    print("🚀 Bot_2 ishga tushirilmoqda...")
    app = Application.builder().token(BOT2_TOKEN).post_init(load_sessions).build()

    # Handlelarni qo'shamiz
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("accounts", accounts))
    app.add_handler(CommandHandler("use", use))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("id", tg_id))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.Document.ALL, session))

    # Botni ishga tushiramiz (drop_pending_updates Render uchun muhim)
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    print("✅ Bot_2 muvaffaqiyatli ishlayapti!")
    
    # main.py da gather uzilib qolmasligi uchun cheksiz loop
    while True:
        await asyncio.sleep(3600)
