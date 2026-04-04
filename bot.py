import asyncio
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

# ===== НАСТРОЙКИ =====
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== БАЗА =====
conn = sqlite3.connect("reports.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT
)
""")
conn.commit()

# ===== КНОПКИ =====
confirm_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Ха"), KeyboardButton(text="Узгартириш")]],
    resize_keyboard=True
)

# ===== ФОРМАТ ДЕНЕГ =====
def format_money(value):
    return f"{int(value):,}".replace(",", " ")

# ===== СОСТОЯНИЯ =====
class ReportForm(StatesGroup):
    cash_start = State()
    confirm_cash_start = State()

    card_start = State()
    confirm_card_start = State()

    cash_income = State()
    confirm_cash_income = State()

    card_income = State()
    confirm_card_income = State()

    cash_expense = State()
    confirm_cash_expense = State()

    card_expense = State()
    confirm_card_expense = State()

    comment = State()
    confirm_comment = State()

# ===== СТАРТ =====
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Используй /report для отправки отчёта")

# ===== ПРОВЕРКА ДУБЛЯ =====
@dp.message(Command("report"))
async def start_report(message: Message, state: FSMContext):
    date = datetime.now().strftime("%Y-%m-%d")
    user_id = message.from_user.id

    cursor.execute(
        "SELECT * FROM reports WHERE date=? AND user_id=?",
        (date, user_id)
    )

    if cursor.fetchone():
        await message.answer("❗ Вы уже отправили отчёт за сегодня")
        return

    await message.answer("Кун бошига Накд колдик:")
    await state.set_state(ReportForm.cash_start)

# ===== НАЛ =====
@dp.message(ReportForm.cash_start)
async def cash_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_start=val)
        await message.answer(f"{format_money(val)} сум\nТугрими?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_cash_start)
    except:
        await message.answer("Сон киритин")
