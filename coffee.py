import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Чтение переменных окружения (настраиваются в панели BotHost)
API_TOKEN = os.getenv('8258796089:AAF14YXPMnYLJm1htV5D_byBP1BDbJpXeXk')
try:
    ADMIN_ID = int(os.getenv('160624362', 0))
except (TypeError, ValueError):
    ADMIN_ID = 0

# Проверка наличия настроек
if not API_TOKEN:
    exit("Критическая ошибка: Переменная BOT_TOKEN не найдена в окружении!")
if not ADMIN_ID:
    exit("Критическая ошибка: Переменная ADMIN_ID не настроена или имеет неверный формат!")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния для опроса (Машина состояний)
class CoffeeReview(StatesGroup):
    choosing_number = State()
    writing_feedback = State()
    brand_discussion = State()

# Клавиатуры
def main_menu():
    buttons = [
        [KeyboardButton(text="☕ Оценить кофе")],
        [KeyboardButton(text="💡 Обсудить бренд")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def coffee_numbers():
    buttons = [
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="4"), KeyboardButton(text="5")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Обработка команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Помоги нам выбрать лучший кофе. Выбери действие:", 
        reply_markup=main_menu()
    )

# --- ЛОГИКА ДЕГУСТАЦИИ ---
@dp.message(F.text == "☕ Оценить кофе")
async def choose_coffee(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await message.answer("Выбери номер образца кофе (1-5):", reply_markup=coffee_numbers())

@dp.message(CoffeeReview.choosing_number)
async def process_number(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 5:
        await state.update_data(coffee_id=message.text)
        await state.set_state(CoffeeReview.writing_feedback)
        await message.answer(
            f"Образец №{message.text} принят. \n\nНапиши отзыв: что понравилось, а что нет?", 
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("Пожалуйста, используй кнопки 1-5 для выбора номера.")

@dp.message(CoffeeReview.writing_feedback)
async def save_feedback(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    coffee_id = user_data['coffee_id']
    
    # Отчет для тебя/папы
    report = (f"📥 **НОВЫЙ ОТЗЫВ ПО КОФЕ**\n"
              f"--------------------------\n"
              f"● **Образец:** №{coffee_id}\n"
              f"● **От:** @{message.from_user.username or 'Без ника'}\n"
              f"● **Имя:** {message.from_user.full_name}\n"
              f"● **Текст:** {message.text}")
    
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await state.clear()
    await message.answer("Спасибо! Мы учтем твое мнение.", reply_markup=main_menu())

# --- ЛОГИКА БРЕНДА ---
@dp.message(F.text == "💡 Обсудить бренд")
async def brand_start(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.brand_discussion)
    await message.answer(
        "Напиши свои идеи по названию бренда или комментарии к текущему варианту:", 
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(CoffeeReview.brand_discussion)
async def brand_save(message: types.Message, state: FSMContext):
    report = (f"💡 **ИДЕЯ ПО БРЕНДУ**\n"
              f"--------------------------\n"
              f"● **От:** @{message.from_user.username or 'Без ника'}\n"
              f"● **Текст:** {message.text}")
    
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await state.clear()
    await message.answer("Круто, спасибо за идею!", reply_markup=main_menu())

# Запуск бота
async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
