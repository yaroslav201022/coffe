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

class CoffeeReview(StatesGroup):
    choosing_number = State()
    writing_feedback = State()
    brand_discussion = State()

def get_main_menu():
    kb = [[KeyboardButton(text="☕ Оценить кофе")], [KeyboardButton(text="💡 Обсудить бренд")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_numbers():
    kb = [[KeyboardButton(text=str(i)) for i in range(1, 4)], [KeyboardButton(text="4"), KeyboardButton(text="5")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=get_main_menu())

@dp.message(F.text == "☕ Оценить кофе")
async def start_review(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await message.answer("Выберите номер образца (1-5):", reply_markup=get_numbers())

@dp.message(CoffeeReview.choosing_number)
async def num_chosen(message: types.Message, state: FSMContext):
    if message.text in ["1", "2", "3", "4", "5"]:
        await state.update_data(c_num=message.text)
        await state.set_state(CoffeeReview.writing_feedback)
        await message.answer(f"Образец №{message.text}. Напишите отзыв:", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Выберите 1-5 на кнопках.")

@dp.message(CoffeeReview.writing_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    report = f"📥 ОТЗЫВ\nКофе: №{data.get('c_num')}\nОт: {user}\nТекст: {message.text}"
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, report)
    await state.clear()
    await message.answer("Спасибо!", reply_markup=get_main_menu())

@dp.message(F.text == "💡 Обсудить бренд")
async def brand_idea(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.brand_discussion)
    await message.answer("Ваши идеи по бренду:", reply_markup=ReplyKeyboardRemove())

@dp.message(CoffeeReview.brand_discussion)
async def process_brand(message: types.Message, state: FSMContext):
    user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    report = f"💡 БРЕНД\nОт: {user}\nТекст: {message.text}"
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, report)
    await state.clear()
    await message.answer("Принято!", reply_markup=get_main_menu())

async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
