from aiogram import Router, Bot
from aiogram.types.error_event import ErrorEvent

from config import owner_id

router = Router()

@router.error()
async def error_handler(event: ErrorEvent, bot: Bot):
    if hasattr(event.update, 'message'):
        error_text = f'Ошибка: {event.update.message.text}\n{event.update.message.chat.id}'
    else:
        error_text = f'Ошибка: {event.update.call.message.text} {event.update.call.message.chat.id}'
    await bot.send_message(owner_id, error_text)
    print(error_text)