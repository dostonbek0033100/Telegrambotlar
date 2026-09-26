from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT3_TOKEN = '8958500982:AAERSc1_6vEuPb2xHZRQog_BaDuQjWC2pIw' # 3-bot tokenini kiriting
YOUR_TELEGRAM_ID = 1072547777          # O'zingizning ID raqamingiz

async def b3_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn = [[KeyboardButton('📍 Manzilni yuborish', request_location=True)]]
    markup = ReplyKeyboardMarkup(btn, resize_keyboard=True)
    await update.message.reply_text("Assalomu alaykum! Iltimos, pastdagi 'Manzilni yuborish' tugmasini bosing:", reply_markup=markup)

async def b3_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude
    
    yandex_link = f"https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map"
    google_link = f"https://www.google.com/maps?q={lat},{lon}"
    msg = f"Yangi mijoz manzili!\n\nYandex: {yandex_link}\nGoogle: {google_link}"
    
    await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=msg)
    await update.message.reply_text("Rahmat! Manzilingiz qabul qilindi, tez orada yetkazib beramiz.")

async def start():
    app3 = Application.builder().token(BOT3_TOKEN).build()
    app3.add_handler(CommandHandler("start", b3_start))
    app3.add_handler(MessageHandler(filters.LOCATION, b3_location))
    
    await app3.initialize()
    await app3.start()
    await app3.updater.start_polling(drop_pending_updates=True)
