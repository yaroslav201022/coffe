import os
import asyncio
import logging
import csv
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile

logging.basicConfig(level=logging.INFO)

# Настройки
API_TOKEN = os.getenv('BOT_TOKEN')
RAW_ADMIN_ID = os.getenv('ADMIN_ID')
FILENAME = "coffee_results.csv"

try:
    ADMIN_ID = int(RAW_ADMIN_ID) if RAW_ADMIN_ID else 0
except:
    ADMIN_ID = 0

bot = Bot(token=API_TOKEN.strip() if API_TOKEN else "")
dp = Dispatcher()

class CoffeeReview(StatesGroup):
    choosing_number = State()
    rating = State()
    details = State()
    writing_pos = State()
    writing_neg = State()
    brand_naming = State()

# --- ФУНКЦИИ ---
def save_to_csv(data_list):
    file_exists = os.path.isfile(FILENAME)
    with open(FILENAME, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        if not file_exists:
            writer.writerow(['Дата', 'Пользователь', 'Образец №', 'Оценка', 'Понравилось', 'Не понравилось', 'Название'])
        writer.writerow(data_list)

# --- ИНЛАЙН-КЛАВИАТУРЫ ---
def kb_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Оценить кофе", callback_data="start_eval")],
        [InlineKeyboardButton(text="💎 Придумайте свое название", callback_data="start_name")]
    ])

def kb_numbers():
    btns = [[InlineKeyboardButton(text=str(i), callback_data=f"num_{i}") for i in range(1, 6)]]
    btns.append([InlineKeyboardButton(text="🔙 Назад", callback_data="to_main")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def kb_ratings():
    row1 = [InlineKeyboardButton(text=str(i), callback_data=f"rat_{i}") for i in range(1, 6)]
    row2 = [InlineKeyboardButton(text=str(i), callback_data=f"rat_{i}") for i in range(6, 11)]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2, [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_nums")]])

def kb_details():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Что понравилось", callback_data="write_pos")],
        [InlineKeyboardButton(text="❌ Что не понравилось", callback_data="write_neg")],
        [InlineKeyboardButton(text="🏁 Завершить", callback_data="finish_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_rat")]
    ])

def kb_back(to_where):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=to_where)]])

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=kb_main())

@dp.message(Command("get_data"))
async def send_data(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if os.path.exists(FILENAME):
            await message.answer_document(FSInputFile(FILENAME), caption="Все результаты на текущий момент.")
        else:
            await message.answer("Файл еще не создан.")

# Логика "Оценить кофе"
@dp.callback_query(F.data == "start_eval")
async def select_num(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await call.message.edit_text("Выберите номер образца (1-5):", reply_markup=kb_numbers())

@dp.callback_query(F.data.startswith("num_"))
async def select_rat(call: types.CallbackQuery, state: FSMContext):
    num = call.data.split("_")[1]
    await state.update_data(c_num=num)
    await state.set_state(CoffeeReview.rating)
    await call.message.edit_text(f"Образец №{num}.\nОцените вкус кофе по шкале от 1 до 10:", reply_markup=kb_ratings())

@dp.callback_query(F.data.startswith("rat_"))
async def select_details(call: types.CallbackQuery, state: FSMContext):
    rat = call.data.split("_")[1]
    await state.update_data(c_rating=rat)
    await state.set_state(CoffeeReview.details)
    await call.message.edit_text("Добавьте подробности:", reply_markup=kb_details())

@dp.callback_query(F.data == "write_pos")
async def ask_pos(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CoffeeReview.writing_pos)
    await call.message.edit_text("Напишите, что вам ПОНРАВИЛОСЬ в этом кофе:", reply_markup=kb_back("back_to_details"))

@dp.callback_query(F.data == "write_neg")
async def ask_neg(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CoffeeReview.writing_neg)
    await call.message.edit_text("Напишите, что вам НЕ понравилось:", reply_markup=kb_back("back_to_details"))

@dp.message(CoffeeReview.writing_pos)
async def get_pos(message: types.Message, state: FSMContext):
    await state.update_data(pos=message.text)
    await state.set_state(CoffeeReview.details)
    await message.answer("Записано. Что-то еще?", reply_markup=kb_details())

@dp.message(CoffeeReview.writing_neg)
async def get_neg(message: types.Message, state: FSMContext):
    await state.update_data(neg=message.text)
    await state.set_state(CoffeeReview.details)
    await message.answer("Записано. Что-то еще?", reply_markup=kb_details())

@dp.callback_query(F.data == "finish_all")
async def finish_survey(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    u = f"@{call.from_user.username}" if call.from_user.username else call.from_user.full_name
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    save_to_csv([now, u, data.get('c_num'), data.get('c_rating'), data.get('pos', '-'), data.get('neg', '-'), '-'])
    
    if ADMIN_ID:
        try: await bot.send_message(ADMIN_ID, f"📥 ОТЗЫВ №{data.get('c_num')}\n⭐ Оценка: {data.get('c_rating')}/10\n👤 От: {u}")
        except: pass
        
    await state.clear()
    await call.message.edit_text("Спасибо! Ваш отзыв сохранен.", reply_markup=kb_main())

# Логика названия
@dp.callback_query(F.data == "start_name")
async def start_naming(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CoffeeReview.brand_naming)
    await call.message.edit_text("Напишите ваш вариант названия для бренда:", reply_markup=kb_back("to_main"))

@dp.message(CoffeeReview.brand_naming)
async def save_brand_name(message: types.Message, state: FSMContext):
    u = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    save_to_csv([now, u, '-', '-', '-', '-', message.text])
    
    if ADMIN_ID:
        try: await bot.send_message(ADMIN_ID, f"💎 Название: {message.text}\nОт: {u}")
        except: pass
        
    await state.clear()
    await message.answer("Вариант сохранен!", reply_markup=kb_main())

# Навигация Назад
@dp.callback_query(F.data == "to_main")
async def back_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Главное меню:", reply_markup=kb_main())

@dp.callback_query(F.data == "back_to_nums")
async def back_nums(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await call.message.edit_text("Выберите номер образца (1-5):", reply_markup=kb_numbers())

@dp.callback_query(F.data == "back_to_rat")
async def back_rat(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(CoffeeReview.rating)
    await call.message.edit_text(f"Образец №{data.get('c_num')}.\nОцените вкус кофе по шкале от 1 до 10:", reply_markup=kb_ratings())

@dp.callback_query(F.data == "back_to_details")
async def back_details(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CoffeeReview.details)
    await call.message.edit_text("Добавьте подробности:", reply_markup=kb_details())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
