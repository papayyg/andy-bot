from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

langs_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🇦🇿 Azərbaycan", callback_data="az")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="en")],
    ]
)
