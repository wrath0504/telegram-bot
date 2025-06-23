from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from services.logs import send_log_to_admin

router = Router()

@router.message(F.text == "/start")
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📦 Каталог",
            web_app=WebAppInfo(url="https://telegram-webapp-sand.vercel.app/")
        )],
        [InlineKeyboardButton(text="👨‍💼 Менеджер", callback_data="manager")],
        [InlineKeyboardButton(text="📢 Канал", url="https://t.me/zdclubshop")]
    ])
    await message.answer("Добро пожаловать! Выберите:", reply_markup=kb)
    await send_log_to_admin("нажал старт", user=message.from_user)
