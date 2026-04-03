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
    keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Изменить")]],
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

    await message.answer("Введите остаток НАЛИЧНЫХ:")
    await state.set_state(ReportForm.cash_start)

# ===== НАЛ =====
@dp.message(ReportForm.cash_start)
async def cash_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_start=val)
        await message.answer(f"{format_money(val)} сум\nВсе верно?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_cash_start)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.confirm_cash_start)
async def confirm_cash(message: Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите остаток НА КАРТЕ:")
        await state.set_state(ReportForm.card_start)
    else:
        await state.set_state(ReportForm.cash_start)

# ===== КАРТА =====
@dp.message(ReportForm.card_start)
async def card_start(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_start=val)
        await message.answer(f"{format_money(val)} сум\nВсе верно?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_card_start)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.confirm_card_start)
async def confirm_card(message: Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите поступления НАЛИЧНЫМИ:")
        await state.set_state(ReportForm.cash_income)
    else:
        await state.set_state(ReportForm.card_start)

# ===== ПОСТУПЛЕНИЯ НАЛ =====
@dp.message(ReportForm.cash_income)
async def cash_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_income=val)
        await message.answer(f"{format_money(val)} сум\nВсе верно?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_cash_income)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.confirm_cash_income)
async def confirm_cash_income(message: Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите поступления НА КАРТУ:")
        await state.set_state(ReportForm.card_income)
    else:
        await state.set_state(ReportForm.cash_income)

# ===== ПОСТУПЛЕНИЯ КАРТА =====
@dp.message(ReportForm.card_income)
async def card_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_income=val)
        await message.answer(f"{format_money(val)} сум\nВсе верно?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_card_income)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.confirm_card_income)
async def confirm_card_income(message: Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите расходы НАЛИЧНЫМИ:")
        await state.set_state(ReportForm.cash_expense)
    else:
        await state.set_state(ReportForm.card_income)

# ===== РАСХОД НАЛ =====
@dp.message(ReportForm.cash_expense)
async def cash_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_expense=val)
        await message.answer(f"{format_money(val)} сум\nВсе верно?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_cash_expense)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.confirm_cash_expense)
async def confirm_cash_expense(message: Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите расходы С КАРТЫ:")
        await state.set_state(ReportForm.card_expense)
    else:
        await state.set_state(ReportForm.cash_expense)

# ===== РАСХОД КАРТА =====
@dp.message(ReportForm.card_expense)
async def card_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_expense=val)
        await message.answer(f"{format_money(val)} сум\nВсе верно?", reply_markup=confirm_kb)
        await state.set_state(ReportForm.confirm_card_expense)
    except:
        await message.answer("Введите число")

@dp.message(ReportForm.confirm_card_expense)
async def confirm_card_expense(message: Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Кратко опишите расходы:")
        await state.set_state(ReportForm.comment)
    else:
        await state.set_state(ReportForm.card_expense)

# ===== КОММЕНТАРИЙ =====
@dp.message(ReportForm.comment)
async def comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Все верно?", reply_markup=confirm_kb)
    await state.set_state(ReportForm.confirm_comment)

# ===== ФИНАЛ =====
@dp.message(ReportForm.confirm_comment)
async def finish(message: Message, state: FSMContext):
    if message.text != "Да":
        await state.set_state(ReportForm.comment)
        return

    data = await state.get_data()

    cash_start = data['cash_start']
    card_start = data['card_start']
    cash_income = data['cash_income']
    card_income = data['card_income']
    cash_expense = data['cash_expense']
    card_expense = data['card_expense']
    comment = "• " + data['comment'].replace(",", "\n•")

    cash_end = cash_start + cash_income - cash_expense
    card_end = card_start + card_income - card_expense

    total_start = cash_start + card_start
    total_end = cash_end + card_end

    date = datetime.now().strftime("%d.%m.%Y")
    user = message.from_user.full_name

    text = f"""
📅 Отчёт за {date}

👤 Сотрудник: {user}

━━━━━━━━━━━━━━━━━━
💵 НАЛИЧНЫЕ
━━━━━━━━━━━━━━━━━━
Начало:        {format_money(cash_start)} сум
Поступления:   {format_money(cash_income)} сум
Расходы:       {format_money(cash_expense)} сум
Остаток:       {format_money(cash_end)} сум

━━━━━━━━━━━━━━━━━━
💳 КАРТА
━━━━━━━━━━━━━━━━━━
Начало:        {format_money(card_start)} сум
Поступления:   {format_money(card_income)} сум
Расходы:       {format_money(card_expense)} сум
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
        (message.from_user.id, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()

    await message.answer(text)
    await bot.send_message(CHANNEL_ID, text)

    await state.clear()

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
