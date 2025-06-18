import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode
from config import TOKEN, ADMIN_ID
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

RENDER_DOMAIN = "telegram-bot-jfww.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://{RENDER_DOMAIN}{WEBHOOK_PATH}"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Команда /start
@dp.message(F.text == "/start")
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📦 Каталог",
            web_app=WebAppInfo(url="https://telegram-webapp-sand.vercel.app/")
        )],
        [InlineKeyboardButton(text="👨‍💼 Менеджер", callback_data="manager")],
        [InlineKeyboardButton(text="📢 Канал", url="https://t.me/zdclubshop")]
    ])
    await message.answer("Добро пожаловать! Выберите:", reply_markup=kb)

# Логи с полной информацией
async def send_log_to_admin(text: str, user: types.User = None):
    user_info = ""
    if user:
        username = f"@{user.username}" if user.username else "(нет username)"
        full_name = f"{user.full_name}"
        user_info = f"👤 <b>{full_name}</b> {username}\n"
    await bot.send_message(ADMIN_ID, f"📋 <b>Лог действия:</b>\n{user_info}{text}")


# Обработка кнопки "Менеджер"
@dp.callback_query(F.data == "manager")
async def show_manager(callback: types.CallbackQuery):
    text = (
        "📞 <b>Контакты менеджеров:</b>\n\n"
        "😉 Эмиль\n"
        "Telegram: @kuZo_18\n\n"
        "😎 Ильназ\n"
        "Telegram: @zery01"
    )
    await callback.message.answer(text)
    await callback.answer()
    await send_log_to_admin("запросил контакты", user=callback.from_user)

# Обработка пинга
async def handle_ping(request):
    return web.Response(text="pong")

# Основная функция запуска
async def main():
    await bot.set_webhook(WEBHOOK_URL)
    app = web.Application()
    app.router.add_get("/ping", handle_ping)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app

# Запуск приложения
if __name__ == "__main__":
    web.run_app(main(), host="0.0.0.0", port=10000)
