from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales.translations import _, translations
from utils.locales import locales_dict

langs_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=translations[key]["name"], callback_data=key)] for key in translations
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
            [
                InlineKeyboardButton(text=await _("00013", lang), callback_data=f"stats=={link}"),
                InlineKeyboardButton(text=await _("00012", lang), callback_data=f"profile=={link}")
			]
        ]
    )
    return keyboard

async def download_videos(chat_id, link):
    lang = locales_dict[chat_id]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=await _("00019", lang), callback_data=f"videos(5)=={link}"),
            ],
            [
                InlineKeyboardButton(text=await _("00020", lang), callback_data=f"videos(10)=={link}"),
			]
        ]
    )
    return keyboard