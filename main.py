import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def handle(request):
    return web.Response(text="Bot ishlayapti!")


async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)

    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Web server {port} portda ishlayapti")


async def start_bot():
    print("Telegram bot ishga tushdi!")
    await dp.start_polling(bot)


async def main():
    await asyncio.gather(
        start_web(),
        start_bot()
    )


if __name__ == "__main__":
    asyncio.run(main())
