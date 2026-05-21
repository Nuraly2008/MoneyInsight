from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

start_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📊 Analyze Statement")]],
    resize_keyboard=True,
)
