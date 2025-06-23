from config import ADMIN_ID
from bot import bot
from aiogram import types

async def send_log_to_admin(text: str, user: types.User = None):
    user_info = ""
    if user:
        username = f"@{user.username}" if user.username else "(нет username)"
        full_name = f"{user.full_name}"
        user_info = f"👤 <b>{full_name}</b> {username}\n"
    await bot.send_message(ADMIN_ID, f"📋 <b>Лог действия:</b>\n{user_info}{text}")
