import asyncio
import sqlite3
from datetime import datetime
import pytz
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

# ===== НАСТРОЙКИ =====
TOKEN = os.getenv("TOKEN") or "ВСТАВЬ_ТОКЕН"
CHANNEL_ID = int(os.getenv("CHANNEL_ID") or "-1000000000000")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== ВРЕМЯ =====
def get_now():
    tz = pytz.timezone("Asia/Tashkent")
    return datetime.now(tz)

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

# ===== КНОПКА =====
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📊 Новый отчёт")]],
    resize_keyboard=True
)

# ===== ФОРМАТ =====
def format_money(value):
    return f"{int(value):,}".replace(",", " ")

# ===== СОСТОЯНИЯ =====
class ReportForm(StatesGroup):
    cash_start = State()
    card_start = State()
    cash_income = State()
    card_income = State()
    cash_expense = State()
    card_expense = State()
    comment = State()

# ===== СТАРТ =====
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Нажмите кнопку для создания отчёта",
        reply_markup=main_kb
    )

# ===== КНОПКА =====
@dp.message(F.text == "📊 Новый отчёт")
async def new_report(message: Message, state: FSMContext):
    date = get_now().strftime("%Y-%m-%d")
    user_id = message.from_user.id

    cursor.execute(
        "SELECT * FROM reports WHERE date=? AND user_id=?",
        (date, user_id)
    )

    if cursor.fetchone():
        await message.answer("❗ Вы уже отправили отчёт за сегодня", reply_markup=main_kb)
        return

    await message.answer("Введите остаток НАЛИЧНЫХ:")
    await state.set_state(ReportForm.cash_start)

# ===== ШАГИ =====
@dp.message(ReportForm.cash_start)
async def cash_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_start=val)
        await message.answer("Введите остаток НА КАРТЕ:")
        await state.set_state(ReportForm.card_start)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.card_start)
async def card_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_start=val)
        await message.answer("Введите поступления НАЛИЧНЫМИ:")
        await state.set_state(ReportForm.cash_income)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.cash_income)
async def cash_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_income=val)
        await message.answer("Введите поступления НА КАРТУ:")
        await state.set_state(ReportForm.card_income)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.card_income)
async def card_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_income=val)
        await message.answer("Введите расходы НАЛИЧНЫМИ:")
        await state.set_state(ReportForm.cash_expense)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.cash_expense)
async def cash_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_expense=val)
        await message.answer("Введите расходы С КАРТЫ:")
        await state.set_state(ReportForm.card_expense)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.card_expense)
async def card_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_expense=val)
        await message.answer("Кратко опишите расходы:")
        await state.set_state(ReportForm.comment)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.comment)
async def finish(message: Message, state: FSMContext):
    data = await state.get_data()

    cash_end = data['cash_start'] + data['cash_income'] - data['cash_expense']
    card_end = data['card_start'] + data['card_income'] - data['card_expense']

    total_start = data['cash_start'] + data['card_start']
    total_end = cash_end + card_end

    comment = "• " + message.text.replace(",", "\n•")

    date = get_now().strftime("%d.%m.%Y")
    user = message.from_user.full_name

    text = f"""
📅 Отчёт за {date}

👤 Сотрудник: {user}

━━━━━━━━━━━━━━━━━━
💵 НАЛИЧНЫЕ
━━━━━━━━━━━━━━━━━━
Начало:        {format_money(data['cash_start'])} сум
Поступления:   {format_money(data['cash_income'])} сум
Расходы:       {format_money(data['cash_expense'])} сум
Остаток:       {format_money(cash_end)} сум

━━━━━━━━━━━━━━━━━━
💳 КАРТА
━━━━━━━━━━━━━━━━━━
Начало:        {format_money(data['card_start'])} сум
Поступления:   {format_money(data['card_income'])} сум
Расходы:       {format_money(data['card_expense'])} сум
Остаток:       {format_money(card_end)} сум

━━━━━━━━━━━━━━━━━━
📊 ОБЩИЙ ИТОГ
━━━━━━━━━━━━━━━━━━
На начало:     {format_money(total_start)} сум
На конец:      {format_money(total_end)} сум

━━━━━━━━━━━━━━━━━━
📝 РАСХОДЫ
━━━━━━━━━━━━━━━━━━
{comment}
"""

    cursor.execute(
        "INSERT INTO reports (user_id, date) VALUES (?, ?)",
        (message.from_user.id, get_now().strftime("%Y-%m-%d"))
    )
    conn.commit()

    await message.answer(text, reply_markup=main_kb)
    await bot.send_message(CHANNEL_ID, text)

    await state.clear()

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
