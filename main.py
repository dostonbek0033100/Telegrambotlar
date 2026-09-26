import os
import asyncio
from aiohttp import web

import bot_1
import bot_2
import bot_3


async def health_check(request):
    return web.Response(
        text="Telegram botlar ishlayapti!"
    )

async def start_web_server():

    app = web.Application()

    app.router.add_get(
        "/",
        health_check
    )

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print(
        f"Web server {port}-portda ishlayapti"
    )


async def main():

    await asyncio.gather(

        # Render Web Server
        start_web_server(),

        # Bot 1 — ModerBot
        bot_1.start(),

        # Bot 2 — UserBot
        bot_2.start(),

        # Keyinchalik qo‘shamiz
        bot_3.start()
    )
if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:

        print(
            "\nTelegram botlar to‘xtatildi."
        )
