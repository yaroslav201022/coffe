import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# 1. Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Получение данных из переменных окружения
API_TOKEN = os.getenv('BOT_TOKEN')
RAW_ADMIN_ID = os.getenv('ADMIN_ID')

# Проверка токена
if not API_TOKEN:
    logger.error("Переменная BOT_TOKEN не установлена!")
    exit(1)

# Проверка ID админа
try:
    ADMIN_ID = int(RAW_ADMIN_ID) if RAW_ADMIN_ID else 0
except ValueError:
    logger.error(f"Некорректный ADMIN_ID: {RAW_ADMIN_ID}")
    ADMIN_ID = 0

if ADMIN_ID == 0:
    logger.error("ADMIN_ID не настроен! Отчеты не будут приходить.")

# 3. Инициализация бота
bot = Bot(token=API_TOKEN.strip())
dp = Dispatcher()

# 4. Состояния опроса
class CoffeeReview(StatesGroup):
    choosing_number = State()
    writing_feedback = State()
    brand_discussion = State()

# 5. Клавиатуры
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="☕ Оценить кофе")],
            [KeyboardButton(text="💡 Обсудить бренд")]
        ],
        resize_keyboard=True
    )

def get_numbers_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5")]
        ],
        resize_keyboard=True
    )

# 6. Обработка команд и сообщений
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Мы проводим дегустацию кофе. Выберите действие:",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "☕ Оценить кофе")
async def start_review(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.choosing_number)
    await message.answer("Выберите номер образца (1-5):", reply_markup=get_numbers_keyboard())

@dp.message(CoffeeReview.choosing_number)
async def coffee_number_chosen(message: types.Message, state: FSMContext):
    if message.text in ["1", "2", "3", "4", "5"]:
        await state.update_data(coffee_num=message.text)
        await state.set_state(CoffeeReview.writing_feedback)
        await message.answer(
            f"Вы выбрали образец №{message.text}. Что вам в нем понравилось или не понравилось?",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("Пожалуйста, выберите номер от 1 до 5 на клавиатуре.")

@dp.message(CoffeeReview.writing_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    data = await state.get_data()
    coffee_num = data.get("coffee_num")
    user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    
    report = (f"📥 НОВЫЙ ОТЗЫВ\n"
              f"Кофе: №{coffee_num}\n"
              f"От: {user_info}\n"
              f"Текст: {message.text}")
    
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, report)
    
    await state.clear()
    await message.answer("Спасибо за ваш отзыв!", reply_markup=get_main_menu())

@dp.message(F.text == "💡 Обсудить бренд")
async def brand_idea(message: types.Message, state: FSMContext):
    await state.set_state(CoffeeReview.brand_discussion)
    await message.answer("Напишите свои идеи по названию или бренду:", reply_markup=ReplyKeyboardRemove())

@dp.message(CoffeeReview.brand_discussion)
async def process_brand(message: types.Message, state: FSMContext):
    user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    report = f"💡 ИДЕЯ БРЕНДА\nОт: {user_info}\nТекст: {message.text}"
    
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, report)
        
    await state.clear()
    await message.answer("Ваша идея принята!", reply_markup=get_main_menu())

# 7. Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
