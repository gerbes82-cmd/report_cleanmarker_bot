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
ALLOWED_USERS = [419259652, 6188049, 1054872862]
def is_allowed(user_id):
    return user_id in ALLOWED_USERS
    
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
    keyboard=[[KeyboardButton(text="📊 Хисобот")]],
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
     if not is_allowed(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    await message.answer(
        "Хисобот яратиш учун пастдаги кнопкани босин",
        reply_markup=main_kb
    )

# ===== КНОПКА =====
@dp.message(F.text == "📊 Новый отчёт")
async def new_report(message: Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ У вас нет доступа")
        return
async def new_report(message: Message, state: FSMContext):
    date = get_now().strftime("%Y-%m-%d")
    user_id = message.from_user.id

    cursor.execute(
        "SELECT * FROM reports WHERE date=? AND user_id=?",
        (date, user_id)
    )

    if cursor.fetchone():
        await message.answer("❗ Сиз бугунги хисоботни юборгансиз", reply_markup=main_kb)
        return

    await message.answer("НАКД колдигини киритин:")
    await state.set_state(ReportForm.cash_start)

# ===== ШАГИ =====
@dp.message(ReportForm.cash_start)
async def cash_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_start=val)
        await message.answer("КАРТА колдигини киритин:")
        await state.set_state(ReportForm.card_start)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.card_start)
async def card_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_start=val)
        await message.answer("НАКД кирим:")
        await state.set_state(ReportForm.cash_income)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.cash_income)
async def cash_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_income=val)
        await message.answer("КАРТА кирим:")
        await state.set_state(ReportForm.card_income)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.card_income)
async def card_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_income=val)
        await message.answer("НАКД чиким:")
        await state.set_state(ReportForm.cash_expense)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.cash_expense)
async def cash_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_expense=val)
        await message.answer("КАРТА чиким:")
        await state.set_state(ReportForm.card_expense)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.card_expense)
async def card_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_expense=val)
        await message.answer("Чикимлар кискача таснифи:")
        await state.set_state(ReportForm.comment)
    except:
        await message.answer("Сон киритин")

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
📅 Хисобот {date}

👤 Ходим: {user}

━━━━━━━━━━━━━━━━━━
💵 НАКД
━━━━━━━━━━━━━━━━━━
Бошига:      {format_money(data['cash_start'])} сум
Кирим:       {format_money(data['cash_income'])} сум
Чиким:       {format_money(data['cash_expense'])} сум
Колдик:      {format_money(cash_end)} сум

━━━━━━━━━━━━━━━━━━
💳 КАРТА
━━━━━━━━━━━━━━━━━━
Бошига:      {format_money(data['card_start'])} сум
Кирим:       {format_money(data['card_income'])} сум
Чиким:       {format_money(data['card_expense'])} сум
Колдик:      {format_money(card_end)} сум

━━━━━━━━━━━━━━━━━━
📊 ЖАМИ
━━━━━━━━━━━━━━━━━━
Кун бошига:  {format_money(total_start)} сум
Кун охирига: {format_money(total_end)} сум

━━━━━━━━━━━━━━━━━━
📝 ЧИКИМЛАР ИЗОХИ
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
