import os
import asyncio
from aiohttp import web

import bot_1
#import bot_2
#import bot_3


async def health_check(request):
    return web.Response(text="Telegram botlar ishlayapti!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)

    port = int(os.environ.get("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Web server {port}-portda ishlayapti")


async def main():
    await asyncio.gather(
        start_web_server(),
        bot_1.start(),
        #bot_2.start(),
        #bot_3.start()
    )


if __name__ == "__main__":
    asyncio.run(main())
