from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📈 Statistics"), KeyboardButton(text="📂 Transactions")],
        [KeyboardButton(text="📊 Expenses by Category"), KeyboardButton(text="🖼 Expense Chart (%)")],
        [KeyboardButton(text="🕘 History"), KeyboardButton(text="🔄 New Analysis")],
        [KeyboardButton(text="ℹ️ Help")],
    ],
    resize_keyboard=True,
)