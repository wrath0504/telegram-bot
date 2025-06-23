from aiogram import types, Router, F
from services.logs import send_log_to_admin

router = Router()

@router.callback_query(F.data == "manager")
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
