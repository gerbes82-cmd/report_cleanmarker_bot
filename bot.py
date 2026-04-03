import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ============================================

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# база данных
conn = sqlite3.connect("reports.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    cash_start REAL,
    card_start REAL,
    cash_income REAL,
    card_income REAL,
    cash_expense REAL,
    card_expense REAL,
    comment TEXT
)
""")
conn.commit()

# ===== КНОПКИ =====
confirm_kb = ReplyKeyboardMarkup(resize_keyboard=True)
confirm_kb.add(KeyboardButton("Да"), KeyboardButton("Изменить"))

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
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Используй /report для отправки отчёта")

# ===== ПРОВЕРКА ДУБЛЯ =====
@dp.message_handler(commands=['report'])
async def start_report(message: types.Message):
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
    await ReportForm.cash_start.set()

# ===== НАЛИЧНЫЕ =====
@dp.message_handler(state=ReportForm.cash_start)
async def cash_start(message: types.Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_start=val)
        await message.answer(f"{val} верно?", reply_markup=confirm_kb)
        await ReportForm.confirm_cash_start.set()
    except:
        await message.answer("Введите число")

@dp.message_handler(state=ReportForm.confirm_cash_start)
async def confirm_cash_start(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите остаток НА КАРТЕ:")
        await ReportForm.card_start.set()
    else:
        await message.answer("Введите заново:")
        await ReportForm.cash_start.set()

# ===== КАРТА =====
@dp.message_handler(state=ReportForm.card_start)
async def card_start(message: types.Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_start=val)
        await message.answer(f"{val} верно?", reply_markup=confirm_kb)
        await ReportForm.confirm_card_start.set()
    except:
        await message.answer("Введите число")

@dp.message_handler(state=ReportForm.confirm_card_start)
async def confirm_card_start(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите поступления НАЛИЧНЫМИ:")
        await ReportForm.cash_income.set()
    else:
        await message.answer("Введите заново:")
        await ReportForm.card_start.set()

# ===== ПОСТУПЛЕНИЯ НАЛ =====
@dp.message_handler(state=ReportForm.cash_income)
async def cash_income(message: types.Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_income=val)
        await message.answer(f"{val} верно?", reply_markup=confirm_kb)
        await ReportForm.confirm_cash_income.set()
    except:
        await message.answer("Введите число")

@dp.message_handler(state=ReportForm.confirm_cash_income)
async def confirm_cash_income(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите поступления НА КАРТУ:")
        await ReportForm.card_income.set()
    else:
        await message.answer("Введите заново:")
        await ReportForm.cash_income.set()

# ===== ПОСТУПЛЕНИЯ КАРТА =====
@dp.message_handler(state=ReportForm.card_income)
async def card_income(message: types.Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_income=val)
        await message.answer(f"{val} верно?", reply_markup=confirm_kb)
        await ReportForm.confirm_card_income.set()
    except:
        await message.answer("Введите число")

@dp.message_handler(state=ReportForm.confirm_card_income)
async def confirm_card_income(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите расходы НАЛИЧНЫМИ:")
        await ReportForm.cash_expense.set()
    else:
        await message.answer("Введите заново:")
        await ReportForm.card_income.set()

# ===== РАСХОД НАЛ =====
@dp.message_handler(state=ReportForm.cash_expense)
async def cash_expense(message: types.Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(cash_expense=val)
        await message.answer(f"{val} верно?", reply_markup=confirm_kb)
        await ReportForm.confirm_cash_expense.set()
    except:
        await message.answer("Введите число")

@dp.message_handler(state=ReportForm.confirm_cash_expense)
async def confirm_cash_expense(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите расходы С КАРТЫ:")
        await ReportForm.card_expense.set()
    else:
        await message.answer("Введите заново:")
        await ReportForm.cash_expense.set()

# ===== РАСХОД КАРТА =====
@dp.message_handler(state=ReportForm.card_expense)
async def card_expense(message: types.Message, state: FSMContext):
    try:
        val = float(message.text)
        await state.update_data(card_expense=val)
        await message.answer(f"{val} верно?", reply_markup=confirm_kb)
        await ReportForm.confirm_card_expense.set()
    except:
        await message.answer("Введите число")

@dp.message_handler(state=ReportForm.confirm_card_expense)
async def confirm_card_expense(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Кратко опишите расходы:")
        await ReportForm.comment.set()
    else:
        await message.answer("Введите заново:")
        await ReportForm.card_expense.set()

# ===== КОММЕНТАРИЙ =====
@dp.message_handler(state=ReportForm.comment)
async def comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("Все верно?", reply_markup=confirm_kb)
    await ReportForm.confirm_comment.set()

# ===== ФИНАЛ =====
@dp.message_handler(state=ReportForm.confirm_comment)
async def finish(message: types.Message, state: FSMContext):
    if message.text != "Да":
        await message.answer("Введите заново:")
        await ReportForm.comment.set()
        return

    data = await state.get_data()

    cash_end = data['cash_start'] + data['cash_income'] - data['cash_expense']
    card_end = data['card_start'] + data['card_income'] - data['card_expense']

    total_start = data['cash_start'] + data['card_start']
    total_end = cash_end + card_end

    date = datetime.now().strftime("%Y-%m-%d")
    user = message.from_user.full_name

    text = f"""
📅 {date}
👤 {user}

💵 Нал: {cash_end}
💳 Карта: {card_end}

📊 Итого: {total_end}

📝 {data['comment']}
"""

    cursor.execute("""
    INSERT INTO reports VALUES (NULL,?,?,?,?,?,?,?,?,?,?)
    """, (
        message.from_user.id, date,
        data['cash_start'], data['card_start'],
        data['cash_income'], data['card_income'],
        data['cash_expense'], data['card_expense'],
        data['comment']
    ))
    conn.commit()

    await message.answer(text)
    await bot.send_message(CHANNEL_ID, text)

    await state.finish()

# ===== НАПОМИНАНИЕ =====
scheduler = AsyncIOScheduler()

async def reminder():
    date = datetime.now().strftime("%Y-%m-%d")
    for user in USERS:
        cursor.execute("SELECT * FROM reports WHERE date=? AND user_id=?", (date, user))
        if not cursor.fetchone():
            await bot.send_message(user, "❗ Сдайте отчёт за сегодня")

scheduler.add_job(reminder, "cron", hour=18)
scheduler.start()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    executor.start_polling(dp)
