import os
import asyncio
import logging
import csv
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

logging.basicConfig(level=logging.INFO)

# Конфигурация
API_TOKEN = os.getenv('BOT_TOKEN')
RAW_ADMIN_ID = os.getenv('ADMIN_ID')
FILENAME = "coffee_results.csv" # Название файла с данными

try:
    ADMIN_ID = int(RAW_ADMIN_ID) if RAW_ADMIN_ID else 0
except:
    ADMIN_ID = 0

bot = Bot(token=API_TOKEN.strip() if API_TOKEN else "")
dp = Dispatcher()

# Функция записи в локальную таблицу
def save_to_csv(data_list):
    file_exists = os.path.isfile(FILENAME)
    with open(FILENAME, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        # Если файл новый, создаем шапку
        if not file_exists:
            writer.writerow(['Дата', 'Пользователь', 'Образец №', 'Оценка (1-10)', 'Понравилось', 'Не понравилось', 'Вариант названия'])
        writer.writerow(data_list)

class CoffeeReview(StatesGroup):
    choosing_number = State()
    rating = State()
    details = State()
    writing_positive = State()
    writing_negative = State()
    brand_naming = State()

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    kb = [[KeyboardButton(text="☕ Оценить кофе")], [KeyboardButton(text="💎 Предложить название бренда")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_numbers():
    kb = [[KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")], [KeyboardButton(text="4"), KeyboardButton(text="5")], [KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_ratings():
    r1 = [KeyboardButton(text=str(i)) for i in range(1, 6)]
    r2 = [KeyboardButton(text=str(i)) for i in range(6, 11)]
    return ReplyKeyboardMarkup(keyboard=[r1, r2, [KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)

def get_details_menu():
    kb = [[KeyboardButton(text="✅ Что понравилось")], [KeyboardButton(text="❌ Что не понравилось")], [KeyboardButton(text="🏁 Завершить и отправить")], [KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_back_button():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---
@dp.message(F.text == "🔙 Назад")
async def go_back(message: types.Message, state: FSMContext):
    s = await state.get_state()
    if s in [CoffeeReview.choosing_number, CoffeeReview.brand_naming, None]:
        await state.clear()
        await message.answer("Главное меню:", reply_markup=get_main_menu())
    elif s == CoffeeReview.rating:
        await state.set_state(CoffeeReview.choosing_number)
        await message.answer("Выбери номер образца:", reply_markup=get_numbers())
    elif s == CoffeeReview.details:
        await state.set_state(CoffeeReview.rating)
        await message.answer("Оцени от 1 до 10:", reply_markup=get_ratings())
    elif s in [CoffeeReview.writing_positive, CoffeeReview.writing_negative]:
        await state.set_state(CoffeeReview.details)
        await message.answer("Что еще добавить?", reply_markup=get_details_menu())

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Мы выбираем лучший кофе. Помоги нам!", reply_markup=get_main_menu())

@dp.message(F.text == "☕ Оценить кофе")
async def start_review(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await message.answer("Какой номер образца пробуешь?", reply_markup=get_numbers())

@dp.message(CoffeeReview.choosing_number, F.text.in_(["1", "2", "3", "4", "5"]))
async def num_chosen(message: types.Message, state: FSMContext):
    await state.update_data(c_num=message.text)
    await state.set_state(CoffeeReview.rating)
    await message.answer(f"Образец №{message.text}. Поставь оценку (1-10):", reply_markup=get_ratings())

@dp.message(CoffeeReview.rating, F.text.in_([str(i) for i in range(1, 11)]))
async def rating_chosen(message: types.Message, state: FSMContext):
    await state.update_data(c_rating=message.text)
    await state.set_state(CoffeeReview.details)
    await message.answer("Поделишься подробностями?", reply_markup=get_details_menu())

@dp.message(CoffeeReview.details, F.text == "✅ Что понравилось")
async def lead_pos(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.writing_positive)
    await message.answer("Напиши, что тебе понравилось:", reply_markup=get_back_button())

@dp.message(CoffeeReview.details, F.text == "❌ Что не понравилось")
async def lead_neg(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.writing_negative)
    await message.answer("Напиши, что не понравилось:", reply_markup=get_back_button())

@dp.message(CoffeeReview.writing_positive)
async def s_pos(message: types.Message, state: FSMContext):
    if message.text != "🔙 Назад":
        await state.update_data(pos=message.text)
        await state.set_state(CoffeeReview.details)
        await message.answer("Запомнил! Что-то еще?", reply_markup=get_details_menu())

@dp.message(CoffeeReview.writing_negative)
async def s_neg(message: types.Message, state: FSMContext):
    if message.text != "🔙 Назад":
        await state.update_data(neg=message.text)
        await state.set_state(CoffeeReview.details)
        await message.answer("Запомнил! Что-то еще?", reply_markup=get_details_menu())

@dp.message(CoffeeReview.details, F.text == "🏁 Завершить и отправить")
async def finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    u = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Сохраняем в файл
    save_to_csv([now, u, data.get('c_num'), data.get('c_rating'), data.get('pos', '-'), data.get('neg', '-'), '-'])
    
    rep = f"📥 ОТЗЫВ №{data.get('c_num')}\n⭐ Оценка: {data.get('c_rating')}/10\n👤 От: {u}"
    if ADMIN_ID:
        try: await bot.send_message(ADMIN_ID, rep)
        except: pass
    
    await state.clear()
    await message.answer("Спасибо! Данные сохранены.", reply_markup=get_main_menu())

@dp.message(F.text == "💎 Предложить название бренда")
async def brand_s(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.brand_naming)
    await message.answer("Как назовем бренд?", reply_markup=get_back_button())

@dp.message(CoffeeReview.brand_naming)
async def p_brand(message: types.Message, state: FSMContext):
    if message.text != "🔙 Назад":
        u = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Сохраняем только название
        save_to_csv([now, u, '-', '-', '-', '-', message.text])
        
        if ADMIN_ID:
            try: await bot.send_message(ADMIN_ID, f"💎 Вариант названия: {message.text}\nОт: {u}")
            except: pass
            
        await state.clear()
        await message.answer("Вариант записан!", reply_markup=get_main_menu())

# Запуск
async def start_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
