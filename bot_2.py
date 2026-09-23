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

# ================= USERBOT FUNKSIYALARI (AKKAUNT ICHIDA) =================

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
    await event.edit("🟢 **24/7 Onlayn rejim yoqildi!**")

async def userbot_online_off(event):
    client = event.client
    if hasattr(client, 'online_task') and client.online_task:
        client.online_task.cancel()
        client.online_task = None
        try: await client(functions.account.UpdateStatusRequest(offline=True))
        except: pass
        await event.edit("🔴 **24/7 Onlayn rejim o'chirildi.**")

# 2. Familyaga soat qo'yish
async def keep_time_task(client):
    try:
        while True:
            if client.is_connected():
                now = datetime.utcnow() + timedelta(hours=5)
                current_time = now.strftime("%H:%M")
                try:
                    await client(UpdateProfileRequest(last_name=current_time))
                except Exception:
                    pass
            now = datetime.utcnow() + timedelta(hours=5)
            await asyncio.sleep(60 - now.second)
    except asyncio.CancelledError: pass
    except Exception: pass

async def userbot_time_on(event):
    client = event.client
    if hasattr(client, 'time_task') and client.time_task:
        return await event.edit("⏳ Soatli ism allaqachon yoqilgan.")
    client.time_task = asyncio.create_task(keep_time_task(client))
    await event.edit("⏳ **Soatli ism yoqildi!**\nFamilyangiz har minutda yangilanadi.")

async def userbot_time_off(event):
    client = event.client
    if hasattr(client, 'time_task') and client.time_task:
        client.time_task.cancel()
        client.time_task = None
        try: 
            await client(UpdateProfileRequest(last_name=""))
        except: pass
        await event.edit("🛑 **Soatli ism o'chirildi.**")

# 3. Avto-javob funksiyalari
async def userbot_auto_on(event):
    event.client.auto_reply = True
    await event.edit("🤖 **Avto-javob tizimi yoqildi!**")

async def userbot_auto_off(event):
    event.client.auto_reply = False
    await event.edit("💤 **Avto-javob tizimi o'chirildi.**")

async def userbot_add_auto(event):
    text = event.raw_text.split(" ", 1)
    if len(text) < 2 or "|" not in text[1]:
        return await event.edit("⚠️ Format xato:\n`/add_auto salom | Vaalaykum assalom`")

    keyword, reply = text[1].split("|", 1)
    keyword = keyword.strip().lower()
    reply = reply.strip()

    session_name = getattr(event.client, 'session_name', None)
    if session_name:
        await save_reply(session_name, keyword, reply)
        if keyword == "*":
            await event.edit("✅ Barcha xabarlar uchun umumiy javob BAZAGA saqlandi!")
        else:
            await event.edit(f"✅ **{keyword}** so'zi BAZAGA saqlandi!")

async def userbot_del_auto(event):
    text = event.raw_text.split(" ", 1)
    if len(text) < 2:
        return await event.edit("⚠️ Qaysi so'zni o'chirmoqchisiz?\nMasalan: `/del_auto salom`")

    keyword = text[1].strip().lower()
    session_name = getattr(event.client, 'session_name', None)
    
    if session_name:
        deleted = await delete_reply(session_name, keyword)
        if deleted:
            await event.edit(f"🗑 **{keyword}** so'zi BAZADAN o'chirildi.")
        else:
            await event.edit(f"❌ **{keyword}** so'zi topilmadi.")

async def userbot_list_auto(event):
    session_name = getattr(event.client, 'session_name', None)
    if not session_name: return

    replies = await get_replies(session_name)
    if not replies:
        return await event.edit("📭 Hozircha bazada hech qanday so'z yo'q.")

    text = "📋 **Sizning bazadagi avto-javoblaringiz:**\n\n"
    for k, v in replies.items():
        k_text = "Umumiy (*)" if k == "*" else k
        text += f"▫️ **{k_text}** ➡️ _{v}_\n"
    
    await event.edit(text)

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

# --- Barcha userbot komandalarini ro'yxatdan o'tkazish ---
def add_userbot_handlers(client: TelegramClient):
    client.add_event_handler(userbot_online_on, events.NewMessage(pattern=r"(?i)^/online_on", outgoing=True))
    client.add_event_handler(userbot_online_off, events.NewMessage(pattern=r"(?i)^/online_off", outgoing=True))
    
    client.add_event_handler(userbot_time_on, events.NewMessage(pattern=r"(?i)^/s_on", outgoing=True))
    client.add_event_handler(userbot_time_off, events.NewMessage(pattern=r"(?i)^/s_off", outgoing=True))
    
    client.add_event_handler(userbot_auto_on, events.NewMessage(pattern=r"(?i)^/auto_on", outgoing=True))
    client.add_event_handler(userbot_auto_off, events.NewMessage(pattern=r"(?i)^/auto_off", outgoing=True))
    client.add_event_handler(userbot_add_auto, events.NewMessage(pattern=r"(?i)^/add_auto", outgoing=True))
    client.add_event_handler(userbot_del_auto, events.NewMessage(pattern=r"(?i)^/del_auto", outgoing=True))
    client.add_event_handler(userbot_list_auto, events.NewMessage(pattern=r"(?i)^/list_auto", outgoing=True))
    
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
        "📝 <b>Bu komandalarni botga emas, to'g'ridan-to'g'ri profilingiz orqali istalgan chatga yozib ishlata olasiz!</b>",
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
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("ping", ping))
    
    app.add_handler(MessageHandler(filters.Document.ALL, session))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)
