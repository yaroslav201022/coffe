import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Данные из твоих скриншотов
API_TOKEN = '8258796089:AAF14YXPMnYLJm1htV5D_byBP1BDbJpXeXk'
ADMIN_ID = 160624362 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния для опроса
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

# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Мы проводим дегустацию кофе. Пожалуйста, выбери пункт меню ниже:", 
        reply_markup=main_menu()
    )

# --- ЛОГИКА ОЦЕНКИ КОФЕ ---
@dp.message(F.text == "☕ Оценить кофе")
async def choose_coffee(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await message.answer("Выбери номер образца кофе, который ты попробовал:", reply_markup=coffee_numbers())

@dp.message(CoffeeReview.choosing_number)
async def process_number(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 5:
        await state.update_data(coffee_id=message.text)
        await state.set_state(CoffeeReview.writing_feedback)
        await message.answer(
            f"Ты выбрал образец №{message.text}.\n\nНапиши, чем он тебе понравился или не понравился?", 
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("Пожалуйста, нажми на одну из кнопок с номером (1-5).")

@dp.message(CoffeeReview.writing_feedback)
async def save_feedback(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    coffee_id = user_data['coffee_id']
    
    # Формируем отчет для тебя/папы
    report = (f"📥 **НОВЫЙ ОТЗЫВ ПО КОФЕ**\n"
              f"--------------------------\n"
              f"● Образец: №{coffee_id}\n"
              f"● От: @{message.from_user.username or message.from_user.full_name}\n"
              f"● Мнение: {message.text}")
    
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await state.clear()
    await message.answer("Спасибо! Твой отзыв очень важен для нас.", reply_markup=main_menu())

# --- ЛОГИКА БРЕНДА ---
@dp.message(F.text == "💡 Обсудить бренд")
async def brand_start(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.brand_discussion)
    await message.answer(
        "Как тебе название нашего бренда? Напиши свои идеи, варианты или замечания одним сообщением:", 
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(CoffeeReview.brand_discussion)
async def brand_save(message: types.Message, state: FSMContext):
    report = (f"💡 **ИДЕЯ ПО БРЕНДУ**\n"
              f"--------------------------\n"
              f"● От: @{message.from_user.username or message.from_user.full_name}\n"
              f"● Текст: {message.text}")
    
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await state.clear()
    await message.answer("Принято! Спасибо за идею.", reply_markup=main_menu())

async def main():
    print("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if name == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")