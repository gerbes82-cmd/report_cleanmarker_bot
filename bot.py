import asyncio
import sqlite3
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ===== НАСТРОЙКИ =====
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))


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

# ===== КНОПКИ =====
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📊 Хисобот")]],
    resize_keyboard=True
)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Ха"), KeyboardButton(text="Узгартириш")]],
    resize_keyboard=True
)

# ===== ФОРМАТ =====
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
@dp.message()
async def start(message: Message):
    if message.text == "/start":
        await message.answer(
            "Хуш келибсиз 👋\nПастдаги кнопкани босин",
            reply_markup=main_kb
        )

# ===== НОВЫЙ ОТЧЁТ =====
@dp.message()
async def new_report(message: Message, state: FSMContext):
    if message.text != "📊 Хисобот":
        return

    date = get_now().strftime("%Y-%m-%d")
    user_id = message.from_user.id

    cursor.execute(
        "SELECT * FROM reports WHERE date=? AND user_id=?",
        (date, user_id)
    )

    if cursor.fetchone():
        await message.answer("❗ Сиз бугунга хисобот жунатиб булдингиз", reply_markup=main_kb)
        return

    await message.answer("Кун бошига НАКД колдиги:")
    await state.set_state(ReportForm.cash_start)

# ===== ДАЛЕЕ ВСЯ ЛОГИКА =====
@dp.message(ReportForm.cash_start)
async def cash_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_start=val)
        await message.answer(f"{format_money(val)} сум\nТугрими?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_cash_start)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.confirm_cash_start)
async def confirm_cash(message: Message, state: FSMContext):
    if message.text == "Ха":
        await message.answer("Кун бошига КАРТА колдиги:")
        await state.set_state(ReportForm.card_start)
    else:
        await state.set_state(ReportForm.cash_start)

@dp.message(ReportForm.card_start)
async def card_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_start=val)
        await message.answer(f"{format_money(val)} сум\nТугрими?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_card_start)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.confirm_card_start)
async def confirm_card(message: Message, state: FSMContext):
    if message.text == "Ха":
        await message.answer("НАКД кирим:")
        await state.set_state(ReportForm.cash_income)
    else:
        await state.set_state(ReportForm.card_start)

@dp.message(ReportForm.cash_income)
async def cash_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_income=val)
        await message.answer(f"{format_money(val)} сум\nТугрими?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_cash_income)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.confirm_cash_income)
async def confirm_cash_income(message: Message, state: FSMContext):
    if message.text == "Ха":
        await message.answer("КАРТАга кирим:")
        await state.set_state(ReportForm.card_income)
    else:
        await state.set_state(ReportForm.cash_income)

@dp.message(ReportForm.card_income)
async def card_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_income=val)
        await message.answer(f"{format_money(val)} сум\nТугрими?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_card_income)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.confirm_card_income)
async def confirm_card_income(message: Message, state: FSMContext):
    if message.text == "Ха":
        await message.answer("НАКД чиким:")
        await state.set_state(ReportForm.cash_expense)
    else:
        await state.set_state(ReportForm.card_income)

@dp.message(ReportForm.cash_expense)
async def cash_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_expense=val)
        await message.answer(f"{format_money(val)} сум\nТугрими?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_cash_expense)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.confirm_cash_expense)
async def confirm_cash_expense(message: Message, state: FSMContext):
    if message.text == "Ха":
        await message.answer("КАРТАдан чиким:")
        await state.set_state(ReportForm.card_expense)
    else:
        await state.set_state(ReportForm.cash_expense)

@dp.message(ReportForm.card_expense)
async def card_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_expense=val)
        await message.answer(f"{format_money(val)} сум\nТугрими?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_card_expense)
    except:
        await message.answer("Сон киритин")

@dp.message(ReportForm.confirm_card_expense)
async def confirm_card_expense(message: Message, state: FSMContext):
    if message.text == "Ха":
        await message.answer("Чикимлар киска изохи:")
        await state.set_state(ReportForm.comment)
    else:
        await state.set_state(ReportForm.card_expense)

@dp.message(ReportForm.comment)
async def comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Все верно?", reply_markup=confirm_kb)
    await state.set_state(ReportForm.confirm_comment)

# ===== ФИНАЛ =====
@dp.message(ReportForm.confirm_comment)
async def finish(message: Message, state: FSMContext):
    if message.text != "Ха":
        await state.set_state(ReportForm.comment)
        return

    data = await state.get_data()

    cash_end = data['cash_start'] + data['cash_income'] - data['cash_expense']
    card_end = data['card_start'] + data['card_income'] - data['card_expense']

    total_start = data['cash_start'] + data['card_start']
    total_end = cash_end + card_end

    comment = "• " + data['comment'].replace(",", "\n•")

    date = get_now().strftime("%d.%m.%Y")
    user = message.from_user.full_name

    text = f"""
📅 Хисобот {date}

👤 Ходим: {user}

━━━━━━━━━━━━━━━━━━
💵 НАКД
━━━━━━━━━━━━━━━━━━
Кун бошига колдик:   {format_money(data['cash_start'])} сум
Кирим:               {format_money(data['cash_income'])} сум
Чиким:               {format_money(data['cash_expense'])} сум
Кун охирига колдик:  {format_money(cash_end)} сум

━━━━━━━━━━━━━━━━━━
💳 КАРТА
━━━━━━━━━━━━━━━━━━
Кун бошига колдик:   {format_money(data['card_start'])} сум
Кирим:               {format_money(data['card_income'])} сум
Чиким:               {format_money(data['card_expense'])} сум
Кун охирига колдик:  {format_money(card_end)} сум

━━━━━━━━━━━━━━━━━━
📊 ЖАМИ
━━━━━━━━━━━━━━━━━━
Кун бошига колдик:   {format_money(total_start)} сум
Кун охирига колдик:  {format_money(total_end)} сум

━━━━━━━━━━━━━━━━━━
📝 ЧИКИМ
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
