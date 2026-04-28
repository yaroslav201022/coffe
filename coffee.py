import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv('BOT_TOKEN')
RAW_ADMIN_ID = os.getenv('ADMIN_ID')

try:
    ADMIN_ID = int(RAW_ADMIN_ID) if RAW_ADMIN_ID else 0
except:
    ADMIN_ID = 0

bot = Bot(token=API_TOKEN.strip() if API_TOKEN else "")
dp = Dispatcher()

# Состояния
class CoffeeReview(StatesGroup):
    choosing_number = State()
    rating = State()
    details = State()
    writing_positive = State()
    writing_negative = State()
    brand_naming = State() # Состояние для предложения названия

# Клавиатуры
def get_main_menu():
    kb = [
        [KeyboardButton(text="☕ Оценить кофе")],
        [KeyboardButton(text="💎 Предложить название бренда")] # Обновили название
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_numbers():
    kb = [
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="4"), KeyboardButton(text="5")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_ratings():
    row1 = [KeyboardButton(text=str(i)) for i in range(1, 6)]
    row2 = [KeyboardButton(text=str(i)) for i in range(6, 11)]
    kb = [row1, row2, [KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_details_menu():
    kb = [
        [KeyboardButton(text="✅ Что понравилось")],
        [KeyboardButton(text="❌ Что не понравилось")],
        [KeyboardButton(text="🏁 Завершить и отправить")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_back_button():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)

# Универсальный обработчик кнопки Назад
@dp.message(F.text == "🔙 Назад")
async def go_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state in [CoffeeReview.choosing_number, CoffeeReview.brand_naming, None]:
        await state.clear()
        await message.answer("Главное меню:", reply_markup=get_main_menu())
    
    elif current_state == CoffeeReview.rating:
        await state.set_state(CoffeeReview.choosing_number)
        await message.answer("Выбери номер образца (1-5):", reply_markup=get_numbers())
    
    elif current_state == CoffeeReview.details:
        await state.set_state(CoffeeReview.rating)
        await message.answer("Оцени кофе от 1 до 10:", reply_markup=get_ratings())
    
    elif current_state in [CoffeeReview.writing_positive, CoffeeReview.writing_negative]:
        await state.set_state(CoffeeReview.details)
        await message.answer("Выбери, что хочешь добавить в отзыв:", reply_markup=get_details_menu())

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Мы запускаем новый бренд кофе. Помоги нам стать лучше!", reply_markup=get_main_menu())

# --- ЛОГИКА ОЦЕНКИ КОФЕ ---
@dp.message(F.text == "☕ Оценить кофе")
async def start_review(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await message.answer("Какой номер образца ты сейчас пробуешь?", reply_markup=get_numbers())

@dp.message(CoffeeReview.choosing_number, F.text.in_(["1", "2", "3", "4", "5"]))
async def num_chosen(message: types.Message, state: FSMContext):
    await state.update_data(c_num=message.text)
    await state.set_state(CoffeeReview.rating)
    await message.answer(f"Образец №{message.text}. Оцени вкус от 1 до 10:", reply_markup=get_ratings())

@dp.message(CoffeeReview.rating, F.text.in_([str(i) for i in range(1, 11)]))
async def rating_chosen(message: types.
Message, state: FSMContext):
    await state.update_data(c_rating=message.text)
    await state.set_state(CoffeeReview.details)
    await message.answer("Теперь добавь свои впечатления:", reply_markup=get_details_menu())

@dp.message(CoffeeReview.details, F.text == "✅ Что понравилось")
async def lead_positive(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.writing_positive)
    await message.answer("Опиши сильные стороны этого вкуса:", reply_markup=get_back_button())

@dp.message(CoffeeReview.details, F.text == "❌ Что не понравилось")
async def lead_negative(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.writing_negative)
    await message.answer("Что в этом кофе стоит улучшить?", reply_markup=get_back_button())

@dp.message(CoffeeReview.writing_positive)
async def save_pos(message: types.Message, state: FSMContext):
    await state.update_data(pos=message.text)
    await state.set_state(CoffeeReview.details)
    await message.answer("Сохранено. Хочешь добавить что-то еще?", reply_markup=get_details_menu())

@dp.message(CoffeeReview.writing_negative)
async def save_neg(message: types.Message, state: FSMContext):
    await state.update_data(neg=message.text)
    await state.set_state(CoffeeReview.details)
    await message.answer("Сохранено. Хочешь добавить что-то еще?", reply_markup=get_details_menu())

@dp.message(CoffeeReview.details, F.text == "🏁 Завершить и отправить")
async def finish_review(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    
    report = (f"📥 **НОВЫЙ ОТЗЫВ**\n"
              f"☕ Кофе: №{data.get('c_num')}\n"
              f"⭐ Оценка: {data.get('c_rating')}/10\n"
              f"👍 Понравилось: {data.get('pos', '—')}\n"
              f"👎 Не понравилось: {data.get('neg', '—')}\n"
              f"👤 От: {user}")
    
    if ADMIN_ID:
        try: await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
        except: pass
    
    await state.clear()
    await message.answer("Твой отзыв отправлен папе! Спасибо за помощь.", reply_markup=get_main_menu())

# --- ЛОГИКА ПРЕДЛОЖЕНИЯ НАЗВАНИЯ ---
@dp.message(F.text == "💎 Предложить название бренда")
async def brand_start(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.brand_naming)
    await message.answer("Напиши свой вариант названия для нашего бренда кофе:", reply_markup=get_back_button())

@dp.message(CoffeeReview.brand_naming)
async def process_brand(message: types.Message, state: FSMContext):
    user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    report = (f"💎 **НОВОЕ НАЗВАНИЕ**\n"
              f"📝 Вариант: {message.text}\n"
              f"👤 От: {user}")
    
    if ADMIN_ID:
        try: await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
        except: pass
    
    await state.clear()
    await message.answer("Отличное название! Мы его обязательно рассмотрим.", reply_markup=get_main_menu())

async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
