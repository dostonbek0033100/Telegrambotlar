import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telethon import TelegramClient, events, functions
from telethon.tl.functions.account import UpdateProfileRequest
import google.generativeai as genai

# ================= SOZLAMALAR =================
BOT2_TOKEN = "8992607786:AAHoL2E8joe9KrPJyhP5UQXziSuVSi16lrM"
API_ID = 946606
API_HASH = "a183e9d1503a9c6514bd086dd03aeb8e"
OWNER_ID = 1072547777

# AI SOZLAMALARI
GEMINI_API_KEY = "AQ.Ab8RN6Jacg2QdiLuh78_vsrNRuY00lgxj6H_iiFgH99jfL5Ziw"
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

DIR = Path("bot_2")
DIR.mkdir(exist_ok=True)
clients = {}

def ok(u: Update):
    return u.effective_user and u.effective_user.id == OWNER_ID

# ================= USERBOT FUNKSIYALARI =================

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

async def keep_time_task(client):
    try:
        while True:
            if client.is_connected():
                now = datetime.utcnow() + timedelta(hours=5)
                current_time = now.strftime("%H:%M")
                try: await client(UpdateProfileRequest(last_name=current_time))
                except Exception: pass
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
        try: await client(UpdateProfileRequest(last_name=""))
        except: pass
        await event.edit("🛑 **Soatli ism o'chirildi.**")


# --- AQLLI AI AVTO-JAVOB ---
async def userbot_auto_on(event):
    event.client.auto_reply = True
    await event.edit("🤖 **Aqlli AI Avto-javob yoqildi!**\nEndi xabarlarga AI javob beradi.")

async def userbot_auto_off(event):
    event.client.auto_reply = False
    await event.edit("💤 **Aqlli AI Avto-javob o'chirildi.**")

async def auto_responder(event):
    client = event.client
    if not getattr(client, 'auto_reply', False): return
    if not event.is_private: return
        
    sender = await event.get_sender()
    if sender is None or sender.bot or sender.is_self: return

    text = event.raw_text
    if not text: return

    try:
        # AI ga qanday javob berishini uqtiramiz (Prompt)
        prompt = (
            "Sen Dostonbekning shaxsiy Telegram yordamchisisan. "
            f"Unga hozirgina quyidagi xabar keldi: '{text}'. "
            "Ushbu xabarga o'zbek tilida, do'stona, qisqa va aniq javob yoz. "
            "Dostonbek hozir bandligini yoki keyinroq batafsil javob berishini xushmuomalalik bilan bildir. "
            "Javobingni boshqa izohlarsiz, to'g'ridan-to'g'ri yoz."
        )
        
        # Generative AI'dan javob olish (Asinxron ishlashi uchun)
        response = await ai_model.generate_content_async(prompt)
        ai_reply = response.text.strip()
        
        await event.reply(f"{ai_reply}\n\n*(AI yordamchi 🤖)*")
    except Exception as e:
        # Xatolik bo'lsa (masalan API limit tugasa) standart javob qaytaradi
        await event.reply("Xozir javob qaytaraman\n\n*(avto javob qaytargich 🤖)*")

# 4. Anti-reklama (Botlarni guruhda o'chirish)
async def userbot_antiad_on(event):
    event.client.anti_ad = True
    await event.edit("🛡 **Botlarga qarshi Anti-reklama yoqildi!**")

async def userbot_antiad_off(event):
    event.client.anti_ad = False
    await event.edit("🛑 **Anti-reklama o'chirildi.**")

async def anti_ad_handler(event):
    client = event.client
    if not getattr(client, 'anti_ad', False): return
    if not event.is_group: return
        
    sender = await event.get_sender()
    if sender and getattr(sender, 'bot', False) and not sender.is_self:
        try: await event.delete()
        except Exception: pass

def add_userbot_handlers(client: TelegramClient):
    client.add_event_handler(userbot_online_on, events.NewMessage(pattern=r"(?i)^/online_on", outgoing=True))
    client.add_event_handler(userbot_online_off, events.NewMessage(pattern=r"(?i)^/online_off", outgoing=True))
    client.add_event_handler(userbot_time_on, events.NewMessage(pattern=r"(?i)^/s_on", outgoing=True))
    client.add_event_handler(userbot_time_off, events.NewMessage(pattern=r"(?i)^/s_off", outgoing=True))
    client.add_event_handler(userbot_auto_on, events.NewMessage(pattern=r"(?i)^/auto_on", outgoing=True))
    client.add_event_handler(userbot_auto_off, events.NewMessage(pattern=r"(?i)^/auto_off", outgoing=True))
    client.add_event_handler(userbot_antiad_on, events.NewMessage(pattern=r"(?i)^/antiad_on", outgoing=True))
    client.add_event_handler(userbot_antiad_off, events.NewMessage(pattern=r"(?i)^/antiad_off", outgoing=True))
    
    client.add_event_handler(auto_responder, events.NewMessage(incoming=True))
    client.add_event_handler(anti_ad_handler, events.NewMessage(incoming=True))


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
        client.anti_ad = False
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
        "🛠 <b>Boshqaruv (Bot yoki profilingizdan):</b>\n"
        "📁 /login — Yangi .session fayl ulash\n"
        "📊 /accounts, /use NOMI, /status, /logout\n\n"
        "🌐 /online_on, /online_off — 24/7 Onlayn\n"
        "🤖 /auto_on, /auto_off — Aqlli AI Avto-javob\n"
        "⏳ /s_on, /s_off — Familyaga soat\n"
        "🛡 /antiad_on, /antiad_off — Guruhda botlarni o'chirish\n",
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
    await update.message.reply_text(f"🤖 <b>{selected}</b> uchun Aqlli AI Avto-javob yoqildi!", parse_mode="HTML")

async def auto_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    clients[selected].auto_reply = False
    await update.message.reply_text(f"💤 <b>{selected}</b> uchun AI Avto-javob o'chirildi.", parse_mode="HTML")

async def antiad_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    clients[selected].anti_ad = True
    await update.message.reply_text(f"🛡 <b>{selected}</b> uchun Anti-reklama yoqildi!", parse_mode="HTML")

async def antiad_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ok(update): return
    selected = context.user_data.get("selected")
    if not selected or selected not in clients: return await update.message.reply_text("❌ Akkaunt tanlanmagan.")
    clients[selected].anti_ad = False
    await update.message.reply_text(f"🛑 <b>{selected}</b> uchun Anti-reklama to'xtatildi.", parse_mode="HTML")

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
                client.anti_ad = False
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
    app.add_handler(CommandHandler("antiad_on", antiad_on_cmd))
    app.add_handler(CommandHandler("antiad_off", antiad_off_cmd))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("ping", ping))
    
    app.add_handler(MessageHandler(filters.Document.ALL, session))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)
