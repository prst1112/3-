from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from keyboards.main_menu import main_menu_kb
from locales import all_variants, t

router = Router()


@router.message(F.text.in_(all_variants("menu_withdraw")))
async def withdraw_stub(message: Message) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]
    await message.answer(t(lang, "withdraw_stub"))


@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]
    await state.clear()
    await message.answer(t(lang, "action_cancelled"), reply_markup=main_menu_kb(lang))
