from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards.inline import language_kb
from keyboards.main_menu import main_menu_kb
from locales import all_variants, t

router = Router()


@router.message(F.text.in_(all_variants("menu_language")))
async def choose_language(message: Message) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]
    await message.answer(t(lang, "choose_language"), reply_markup=language_kb())


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery) -> None:
    new_lang = callback.data.split(":")[1]
    await db.set_language(callback.from_user.id, new_lang)

    try:
        await callback.message.edit_text(t(new_lang, "language_set"))
    except Exception:
        pass

    await callback.message.answer(t(new_lang, "menu_updated"), reply_markup=main_menu_kb(new_lang))
    await callback.answer()
