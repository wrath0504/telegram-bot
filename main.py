import asyncio
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import WEBHOOK_URL, WEBHOOK_PATH
from bot import bot, dp
from handlers import start_handler, manager_handler

dp.include_router(start_handler.router)
dp.include_router(manager_handler.router)

async def handle_ping(request):
    return web.Response(text="pong")

async def main():
    await bot.set_webhook(WEBHOOK_URL)
    app = web.Application()
    app.router.add_get("/ping", handle_ping)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    web.run_app(main(), host="0.0.0.0", port=10000)
