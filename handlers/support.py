from aiogram import F, Router
from aiogram.types import Message

import config
import database as db
from keyboards.inline import support_contact_kb
from locales import all_variants, t

router = Router()


@router.message(F.text.in_(all_variants("menu_support")))
async def show_support(message: Message) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]
    await message.answer(
        t(lang, "support_text", support_username=f"@{config.SUPPORT_USERNAME}"),
        reply_markup=support_contact_kb(lang, config.SUPPORT_USERNAME),
    )
