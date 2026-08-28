from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

import database as db
from handlers.deal_view import show_deal_to_buyer
from keyboards.main_menu import main_menu_kb
from locales import t

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    payload = command.args
    if payload:
        await show_deal_to_buyer(message, payload.strip(), lang)
        return

    await message.answer(t(lang, "welcome"), reply_markup=main_menu_kb(lang))
