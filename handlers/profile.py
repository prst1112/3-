from aiogram import F, Router
from aiogram.types import Message

import database as db
from locales import all_variants, t
from utils.helpers import format_amount

router = Router()


@router.message(F.text.in_(all_variants("menu_profile")))
async def show_profile(message: Message) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]
    stats = await db.get_user_stats(message.from_user.id)

    text = t(
        lang,
        "profile_text",
        user_id=message.from_user.id,
        balance=format_amount(stats["balance"], "card", lang),
        sold=stats["sold"],
        bought=stats["bought"],
        total=stats["total"],
    )
    await message.answer(text)
