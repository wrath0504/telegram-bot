import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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

# Хранилище корзин пользователей
user_cart = {}

# Универсальная клавиатура внизу
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Каталог"), KeyboardButton(text="Корзина"), KeyboardButton(text="Контакты")]
], resize_keyboard=True)

# Состояния FSM для оформления заказа
class Order(StatesGroup):
    name = State()
    phone = State()
    address = State()
    payment = State()

# Утилита: отправка лога админу
async def send_log_to_admin(text: str):
    try:
        await bot.send_message(ADMIN_ID, f"📋 <b>Лог действия:</b>\n{text}")
    except Exception as e:
        print(f"[Ошибка логирования]: {e}")

# Утилита: отмена заказа
@dp.message(F.text.lower() == "отменить заказ")
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Заказ отменён. Вы вернулись в корзину.", reply_markup=main_menu)
    await show_cart_command(message)

# Команда /start
@dp.message(F.text == "/start")
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📦 Каталог",
            web_app=WebAppInfo(url="https://telegram-webapp-sand.vercel.app/")
        )],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])
    await message.answer("Добро пожаловать! Выберите:", reply_markup=kb)

# Команда /contacts
@dp.message(F.text == "/contacts")
async def show_contacts(message: Message):
    text = (
        "📞 <b>Контакты менеджеров:</b>\n\n"
        "👤 Ирина\n"
        "Telegram: @manager_irina\n\n"
        "👤 Артём\n"
        "Telegram: @manager_artem"
    )
    await message.answer(text)
    await send_log_to_admin(f"👤 {message.from_user.full_name} запросил контакты.")

# Команда /catalog
@dp.message(F.text == "/catalog")
async def show_catalog(message: Message):
    try:
        with open("catalog.json", "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception as e:
        await message.answer("❌ Не удалось загрузить каталог.")
        print(f"[Ошибка каталога]: {e}")
        return

    for product in catalog:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{product['id']}")],
            [InlineKeyboardButton(text="📥 Оформить заказ", callback_data="quick_order")],
            [InlineKeyboardButton(text="❌ Убрать из корзины", callback_data=f"remove_{product['id']}")]
        ])
        caption = f"<b>{product['name']}</b>\n\n{product['description']}\n\n💵 Цена: {product['price']} руб."
        try:
            await message.answer_photo(photo=product['photo_url'], caption=caption, reply_markup=kb)
        except Exception as e:
            await message.answer(f"{caption}", reply_markup=kb)
            print(f"[Ошибка фото]: {e}")

# Команда /cart
@dp.message(F.text == "/cart")
async def show_cart_command(message: Message):
    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])

    if not cart:
        await message.answer("🛒 Ваша корзина пуста.", reply_markup=main_menu)
        return

    try:
        with open("catalog.json", "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception:
        await message.answer("❌ Ошибка загрузки каталога.", reply_markup=main_menu)
        return

    items = []
    total = 0
    for product_id in cart:
        product = next((p for p in catalog if p["id"] == product_id), None)
        if product:
            items.append(f"• {product['name']} — {product['price']} руб.")
            total += product["price"]

    text = "\n".join(items)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Оформить заказ", callback_data="quick_order")],
        [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")]
    ])
    await message.answer(f"🧾 <b>Ваша корзина:</b>\n\n{text}\n\n<b>Итого: {total} руб.</b>", reply_markup=kb)

# Очистка корзины
@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_cart[user_id] = []
    await callback.message.answer("🧹 Корзина очищена.", reply_markup=main_menu)
    await callback.answer()
    await send_log_to_admin(f"👤 {callback.from_user.full_name} очистил корзину.")

# Добавление товара
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])
    user_cart.setdefault(user_id, []).append(product_id)
    await callback.answer("Добавлено в корзину 🛒")
    await send_log_to_admin(f"👤 {callback.from_user.full_name} добавил товар ID {product_id} в корзину.")

# Удаление товара
@dp.callback_query(F.data.startswith("remove_"))
async def remove_from_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])
    if user_id in user_cart and product_id in user_cart[user_id]:
        user_cart[user_id].remove(product_id)
        await callback.answer("❌ Удалено из корзины")
        await send_log_to_admin(f"👤 {callback.from_user.full_name} удалил товар ID {product_id} из корзины.")
    else:
        await callback.answer("Товар не найден в корзине")

# Быстрое оформление заказа
@dp.callback_query(F.data == "quick_order")
async def quick_order(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not user_cart.get(user_id):
        await callback.answer("Ваша корзина пуста!")
        return
    await send_log_to_admin(f"👤 {callback.from_user.full_name} начал оформление заказа.")
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Отменить заказ")],
        [KeyboardButton(text="/catalog"), KeyboardButton(text="/cart"), KeyboardButton(text="/contacts")]
    ], resize_keyboard=True)
    await callback.message.answer("Введите ваше <b>имя</b> для оформления заказа:", reply_markup=cancel_kb)
    await state.set_state(Order.name)

# Сбор данных заказа
@dp.message(Order.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш <b>телефон</b>:")

    # Кнопка отмены остаётся активной

    await state.set_state(Order.phone)

@dp.message(Order.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите <b>адрес доставки</b>:")
    await state.set_state(Order.address)

@dp.message(Order.address)
async def get_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Наличные", callback_data="pay_cash")],
        [InlineKeyboardButton(text="💳 Перевод", callback_data="pay_transfer")]
    ])
    await message.answer("Выберите способ оплаты:", reply_markup=kb)
    await state.set_state(Order.payment)

@dp.callback_query(Order.payment)
async def payment_chosen(callback: types.CallbackQuery, state: FSMContext):
    payment_method = "Наличные" if callback.data == "pay_cash" else "Перевод"
    data = await state.get_data()
    user_id = callback.from_user.id
    cart_items = user_cart.get(user_id, [])

    try:
        with open("catalog.json", "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception:
        await callback.message.answer("❌ Ошибка загрузки каталога.")
        return

    summary = []
    total = 0
    for product_id in cart_items:
        product = next((p for p in catalog if p["id"] == product_id), None)
        if product:
            summary.append(f"• {product['name']} — {product['price']} руб.")
            total += product["price"]

    text = "\n".join(summary)
    username = f"@{callback.from_user.username}" if callback.from_user.username else "(нет username)"
    order_text = (
        f"📦 <b>Новый заказ!</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🔗 Telegram: {username}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"💰 Оплата: {payment_method}\n\n"
        f"🛒 Заказ:\n{text}\n\n"
        f"<b>Итого: {total} руб.</b>"
    )

    await bot.send_message(ADMIN_ID, order_text)
    await callback.message.answer("Спасибо за заказ! Мы скоро свяжемся с вами. ✅", reply_markup=main_menu)
    del user_cart[user_id]
    await state.clear()

# Запуск бота
async def main():
    # Установка Webhook
    await bot.set_webhook(WEBHOOK_URL)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    import uvicorn
    web.run_app(main(), host="0.0.0.0", port=10000)
