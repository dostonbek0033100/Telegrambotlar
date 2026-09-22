import asyncio
from aiogram import Bot, Dispatcher

TOKEN = "8643594879:AAHn4frN-NejUEp_1mP3QtF7GVHO_Sj2Xds"

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
