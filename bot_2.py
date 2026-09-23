import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telethon import TelegramClient, events, functions
from telethon.tl.functions.account import UpdateProfileRequest
from motor.motor_asyncio import AsyncIOMotorClient

# ================= SOZLAMALAR =================
BOT2_TOKEN = "8992607786:AAHoL2E8joe9KrPJyhP5UQXziSuVSi16lrM"
API_ID = 946606
API_HASH = "a183e9d1503a9c6514bd086dd03aeb8e"
OWNER_ID = 1072547777

MONGO_URL = "mongodb+srv://jokkeralihackerov_db_user:UpsDycBqNlvgbhmb@cluster0.mrhsyx8.mongodb.net/?retryWrites=true&w=majority"

DIR = Path("bot_2")
DIR.mkdir(exist_ok=True)

db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["telegram_bot_db"]
replies_col = db["auto_replies"]

clients = {}

def ok(u: Update):
    return u.effective_user and u.effective_user.id == OWNER_ID

# ================= BAZA (MONGODB) BILAN ISHLASH =================
async def get_replies(session_name):
    data = await replies_col.find_one({"session": session_name})
    if data: 
        return data.get("replies", {})
    return {}

async def save_reply(session_name, keyword, reply_text):
    replies = await get_replies(session_name)
    replies[keyword] = reply_text
    await replies_col.update_one(
        {"session": session_name}, 
        {"$set": {"replies": replies}}, 
        upsert=True
    )

async def delete_reply(session_name, keyword):
    replies = await get_replies(session_name)
    if keyword in replies:
        del replies[keyword]
        await replies_col.update_one(
            {"session": session_name}, 
            {"$set": {"replies": replies}}, 
            upsert=True
        )
        return True
    return False

# ================= USERBOT FUNKSIYALARI =================

# 1. Onlayn ushlab turish
async def keep_online_task(client):
    try:
        while True:
            if client.is_connected():
                await client(functions.account.UpdateStatusRequest(offline=False))
                await client(functions.updates.GetStateRequest())
            await asyncio.sleep(60) 
    except asyncio.CancelledError: pass
    except Exception: pass

async def userbot_online_on(event):
    client = event.client
    if hasattr(client, 'online_task') and client.online_task:
        return await event.edit("🟢 24/7 Onlayn rejim allaqachon yoqilgan.")
    client.online_task = asyncio.create_task(keep_online_task(client))
    await event.edit("🟢 <b>24/7 Onlayn rejim yoqildi!</b>", parse_mode="html")

async def userbot_online_off(event):
    client = event.client
    if hasattr(client, 'online_task') and client.online_task:
        client.online_task.cancel()
        client.online_task = None
        try: await client(functions.account.UpdateStatusRequest(offline=True))
        except: pass
        await event.edit("🔴 <b>24/7 Onlayn rejim o'chirildi.</b>", parse_mode="html")

# 2. Avto-javob
async def userbot_auto_on(event):
    event.client.auto_reply = True
    await event.edit("🤖 <b>Avto-javob tizimi yoqildi!</b>", parse_mode="html")

async def userbot_auto_off(event):
    event.client.auto_reply = False
    await event.edit("💤 <b>Avto-javob tizimi o'chirildi.</b>", parse_mode="html")

async def auto_responder(event):
    client = event.client
    if not getattr(client, 'auto_reply', False): return
    if not event.is_private: return
        
    sender = await event.get_sender()
    if sender is None or sender.bot or sender.is_self: return

    text = event.raw_text.lower()
    session_name = getattr(client, 'session_name', None)
    if not session_name: return
    
    user_replies = await get_replies(session_name)
    
    for keyword, response in user_replies.items():
        if keyword != "*" and keyword in text:
            await event.reply(response)
            return
            
    if "*" in user_replies:
        await event.reply(user_replies["*"])

# 3. Familyaga soat qo'yish
async def keep_time_task(client):
    try:
        while True:
            if client.is_connected():
                # O'zbekiston vaqtini olish (UTC+5)
                now = datetime.utcnow() + timedelta(hours=5)
                current_time = now.strftime("%H:%M")
                try:
                    await client(UpdateProfileRequest(last_name=current_time))
                except Exception:
                    pass
            
            # Har daqiqaning boshida yangilanishi uchun soniyalarni hisoblab uxlash
            now = datetime.utcnow() + timedelta(hours=5)
            await asyncio.sleep(60 - now.second)
    except asyncio.CancelledError: pass
    except Exception: pass

async def userbot_time_on(event):
    client = event.client
    if hasattr(client, 'time_task') and client.time_task:
        return await event.edit("⏳ Soatli ism allaqachon yoqilgan.")
    client.time_task = asyncio.create_task(keep_time_task(client))
    await event.edit("⏳ <b>Soatli ism yoqildi!</b>\nFamilyangiz har minutda yangilanadi.", parse_mode="html")

async def userbot_time_off(event):
    client = event.client
    if hasattr(client, 'time_task') and client.time_task:
        client.time_task.cancel()
        client.time_task = None
        try: 
            await client(UpdateProfileRequest(last_name="")) # O'chirilganda familyani bo'shatadi
        except: pass
        await event.edit("🛑 <b>Soatli ism o'chirildi.</b>", parse_mode="html")
    else:
        await event.edit("⚠️ Soatli ism yoqilmagan edi.")

# --- Barcha userbot komandalarini ro'yxatdan o'tkazish ---
def add_userbot_handlers(client: TelegramClient):
    client.add_event_handler(userbot_online_on, events.NewMessage(pattern=r"(?i)^/online_on", outgoing=True))
    client.add_event_handler(userbot_online_off, events.NewMessage(pattern=r"(?i)^/online_off", outgoing=True))
    client.add_event_handler(userbot_auto_on, events.NewMessage(pattern=r"(?i)^/auto_on", outgoing=True))
    client.add_event_handler(userbot_auto_off, events.NewMessage(pattern=r"(?i)^/auto_off", outgoing=True))
    client.add_event_handler(userbot_time_on, events.NewMessage(pattern=r"(?i)^/s_on", outgoing=True))
    client.add_event_handler(userbot_time_off, events.NewMessage(pattern=r"(?i)^/s_off", outgoing=True))
    client.add_event_handler(auto_responder, events.NewMessage(incoming=True))


# ================= SESSIYA ORQALI LOGIN TIZIMI =================
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    context.user_data["login"] = True
    await update.message.reply_text("📁 Iltimos, <b>.session</b> faylini yuboring.", parse_mode="HTML")

async def session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update) or not context.user_data.get("login"): return

    f = update.message.document
    if not f.file_name.endswith(".session"):
        return await update.message.reply_text("❌ Faqat <b>.session</b> fayl qabul qilinadi!", parse_mode="HTML")

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
            return await msg.edit_text("❌ Session yaroqsiz yoki avtorizatsiyadan o'tmagan!")

        me = await client.get_me()
        client.auto_reply = False
        client.session_name = name
        
        add_userbot_handlers(client)
        asyncio.create_task(client.run_until_disconnected())

        clients[name] = client
        context.user_data["selected"] = name

        await msg.edit_text(f"✅ <b>Muvaffaqiyatli ulandi!</b>\n📁 Sessiya: <b>{name}</b>\n🆔 ID: <code>{me.id}</code>", parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {e}")


# ================= BOT KOMANDALARI =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text("✅ <b>Bot_2 ishlayapti!</b>\nBarcha buyruqlar: /help", parse_mode="HTML")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    await update.message.reply_text(
        "🛠 <b>Boshqaruv:</b>\n"
        "/login — Yangi .session fayl ulash\n"
        "/accounts, /use NOMI, /status, /logout\n"
        "🌐 /online_on, /online_off\n"
        "🤖 /auto_on, /auto_off\n"
        "⏳ /s_on, /s_off — Familyaga soat qo'yish\n\n"
        "📝 <b>Avto-javobni sozlash:</b>\n"
        "➕ <code>/add_auto salom | Vaalaykum assalom</code>\n"
        "➖ <code>/del_auto salom</code>\n"
        "📋 <code>/list_auto</code> — Barcha so'zlar",
        parse_mode="HTML"
    )

async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    if not clients: return await update.message.reply_text("📭 Akkauntlar yo'q.")
    text = "👤 <b>Akkauntlaringiz:</b>\n"
    for name in clients:
        sel = "✅" if context.user_data.get("selected") == name else "🔹"
        text += f"{sel} <code>{name}</code>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    if not context.args: return await update.message.reply_text("⚠️ /use NOMI")
    name = context.args[0]
    if name not in clients: return await update.message.reply_text("❌ Akkaunt topilmadi!")
    context.user_data["selected"] = name
    await update.message.reply_text(f"✅ <b>{name}</b> tanlandi!", parse_mode="HTML")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    c = clients.get(selected)
    await update.message.reply_text(f"📡 <b>{selected}</b>\n{'🟢 Ulangan' if c and c.is_connected() else '🔴 Ulanmagan'}", parse_mode="HTML")

# Botdan turib boshqariladigan komandalar
async def s_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    client = clients[selected]
    if hasattr(client, 'time_task') and client.time_task: return await update.message.reply_text("⚠️ Soatli ism allaqachon yoqilgan.")
    client.time_task = asyncio.create_task(keep_time_task(client))
    await update.message.reply_text(f"⏳ <b>{selected}</b> familyasiga soat qo'yildi!", parse_mode="HTML")

async def s_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    client = clients[selected]
    if hasattr(client, 'time_task') and client.time_task:
        client.time_task.cancel()
        client.time_task = None
        try: await client(UpdateProfileRequest(last_name=""))
        except: pass
        await update.message.reply_text("🛑 Soatli ism o'chirildi.")

async def online_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    client = clients[selected]
    if hasattr(client, 'online_task') and client.online_task: return await update.message.reply_text("⚠️ Allaqachon onlayn.")
    client.online_task = asyncio.create_task(keep_online_task(client))
    await update.message.reply_text(f"🟢 <b>{selected}</b> doimiy onlayn bo'ladi!", parse_mode="HTML")

async def online_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    client = clients[selected]
    if hasattr(client, 'online_task') and client.online_task:
        client.online_task.cancel()
        client.online_task = None
        try: await client(functions.account.UpdateStatusRequest(offline=True))
        except: pass
        await update.message.reply_text("🔴 Onlayn rejimidan chiqarildi.")

async def auto_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    clients[selected].auto_reply = True
    await update.message.reply_text(f"🤖 <b>{selected}</b> uchun avto-javob yoqildi!", parse_mode="HTML")

async def auto_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    clients[selected].auto_reply = False
    await update.message.reply_text(f"💤 <b>{selected}</b> uchun avto-javob o'chirildi.", parse_mode="HTML")

# --- BAZA ORQALI SO'ZLARNI QO'SHISH VA O'CHIRISH ---
async def add_auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected: return await update.message.reply_text("❌ Akkaunt tanlanmagan. Avval /use qiling.")

    text = update.message.text.split(" ", 1)
    if len(text) < 2 or "|" not in text[1]:
        return await update.message.reply_text("⚠️ Format xato: <code>/add_auto salom | Vaalaykum assalom</code>", parse_mode="HTML")

    keyword, reply = text[1].split("|", 1)
    keyword = keyword.strip().lower()
    reply = reply.strip()

    await save_reply(selected, keyword, reply)
    
    if keyword == "*":
        await update.message.reply_text(f"✅ Barcha xabarlar uchun umumiy javob BAZAGA saqlandi!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"✅ <b>'{keyword}'</b> so'zi BAZAGA saqlandi!", parse_mode="HTML")

async def del_auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")

    if not context.args: return await update.message.reply_text("⚠️ Qaysi so'zni o'chirmoqchisiz? /del_auto salom")

    keyword = " ".join(context.args).lower()
    
    deleted = await delete_reply(selected, keyword)
    if deleted:
        await update.message.reply_text(f"🗑 <b>'{keyword}'</b> so'zi BAZADAN o'chirildi.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ '{keyword}' so'zi topilmadi.", parse_mode="HTML")

async def list_auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")

    replies = await get_replies(selected)
    if not replies: return await update.message.reply_text("📭 Hozircha bazada hech qanday so'z yo'q.")

    text = "📋 <b>Sizning bazadagi avto-javoblaringiz:</b>\n\n"
    for k, v in replies.items():
        k_text = "Hamma xabarlar uchun umumiy" if k == "*" else k
        text += f"▫️ <b>{k_text}</b> ➡️ <i>{v}</i>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    client = clients[selected]
    if hasattr(client, 'online_task') and client.online_task: client.online_task.cancel()
    if hasattr(client, 'time_task') and client.time_task: client.time_task.cancel()
    await client.disconnect()
    del clients[selected]
    (DIR / f"{selected}.session").unlink(missing_ok=True)
    await update.message.reply_text(f"🗑 <b>{selected}</b> o'chirildi.", parse_mode="HTML")
    context.user_data["selected"] = None

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ok(update): await update.message.reply_text("🏓 Pong 🟢 Bot_2 faol!")

async def load_sessions(app: Application):
    for p in DIR.glob("*.session"):
        name = p.stem
        client = TelegramClient(str(p.with_suffix("")), API_ID, API_HASH)
        try:
            await client.connect()
            if await client.is_user_authorized():
                client.auto_reply = False
                client.session_name = name
                add_userbot_handlers(client)
                asyncio.create_task(client.run_until_disconnected())
                clients[name] = client
            else:
                await client.disconnect()
        except Exception: pass

async def start():
    app = Application.builder().token(BOT2_TOKEN).post_init(load_sessions).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("accounts", accounts))
    app.add_handler(CommandHandler("use", use))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("online_on", online_on_cmd))
    app.add_handler(CommandHandler("online_off", online_off_cmd))
    app.add_handler(CommandHandler("auto_on", auto_on_cmd))
    app.add_handler(CommandHandler("auto_off", auto_off_cmd))
    
    app.add_handler(CommandHandler("s_on", s_on_cmd))
    app.add_handler(CommandHandler("s_off", s_off_cmd))
    
    app.add_handler(CommandHandler("add_auto", add_auto_cmd))
    app.add_handler(CommandHandler("del_auto", del_auto_cmd))
    app.add_handler(CommandHandler("list_auto", list_auto_cmd))
    
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("ping", ping))
    
    app.add_handler(MessageHandler(filters.Document.ALL, session))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)
