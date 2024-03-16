from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales.translations import _
from utils.locales import locales_dict

langs_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🇦🇿 Azərbaycan", callback_data="az")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="en")],
    ]
)


async def tiktok_video_options(chat_id, cover, cover_gif, link):
    lang = locales_dict[chat_id]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=await _("00003", lang), url=cover),
                InlineKeyboardButton(text=await _("00004", lang), url=cover_gif),
            ],
            [InlineKeyboardButton(text=await _("00005", lang), callback_data=f"watermark=={link}")],
        ]
    )
    return keyboard
