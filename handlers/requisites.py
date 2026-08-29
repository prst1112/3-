from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards.inline import card_country_kb, requisites_menu_kb
from keyboards.main_menu import main_menu_kb
from locales import all_variants, t
from states.states import RequisiteAdd
from utils.helpers import is_menu_command

router = Router()


async def render_requisites(target: Message, lang: str, user_id: int) -> None:
    reqs = await db.get_requisites(user_id)
    if not reqs:
        text = t(lang, "requisites_empty")
    else:
        icons = {"card_ua": "🇺🇦", "card_ru": "🇷🇺", "card_by": "🇧🇾", "ton": "💎"}
        lines = [f"{icons.get(r['type'], '💳')} {r['value']}" for r in reqs]
        text = t(lang, "requisites_menu", list="\n".join(lines))
    await target.answer(text, reply_markup=requisites_menu_kb(lang, reqs))


@router.message(F.text.in_(all_variants("menu_requisites")))
async def show_requisites(message: Message) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]
    await render_requisites(message, lang, message.from_user.id)


@router.callback_query(F.data == "add_card")
async def add_card_start(callback: CallbackQuery, state: FSMContext) -> None:
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    reqs = await db.get_requisites(callback.from_user.id)
    cards = [r for r in reqs if r["type"].startswith("card_")]
    if len(cards) >= 2:
        await callback.answer(t(lang, "card_limit_reached"), show_alert=True)
        return

    await state.set_state(RequisiteAdd.entering_card_country)
    await callback.message.answer(t(lang, "choose_card_country"), reply_markup=card_country_kb(lang))
    await callback.answer()


@router.callback_query(RequisiteAdd.entering_card_country, F.data.startswith("card_country:"))
async def choose_card_country(callback: CallbackQuery, state: FSMContext) -> None:
    country = callback.data.split(":")[1]
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    await state.update_data(req_type=f"card_{country}")
    await state.set_state(RequisiteAdd.entering_value)
    await callback.message.edit_text(t(lang, "enter_card_number"))
    await callback.answer()


@router.callback_query(F.data == "add_ton")
async def add_ton_start(callback: CallbackQuery, state: FSMContext) -> None:
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    reqs = await db.get_requisites(callback.from_user.id)
    tons = [r for r in reqs if r["type"] == "ton"]
    if len(tons) >= 1:
        await callback.answer(t(lang, "ton_limit_reached"), show_alert=True)
        return

    await state.update_data(req_type="ton")
    await state.set_state(RequisiteAdd.entering_value)
    await callback.message.answer(t(lang, "enter_ton_address"))
    await callback.answer()


@router.message(RequisiteAdd.entering_value)
async def save_requisite_value(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    if is_menu_command(message.text):
        await state.clear()
        await message.answer(t(lang, "action_cancelled"), reply_markup=main_menu_kb(lang))
        return

    value = (message.text or "").strip()[:100]
    if not value:
        return

    data = await state.get_data()
    req_type = data.get("req_type")

    await db.add_requisite(message.from_user.id, req_type, value)
    await state.clear()

    await message.answer(t(lang, "requisite_added"))
    await render_requisites(message, lang, message.from_user.id)


@router.callback_query(F.data.startswith("del_req:"))
async def delete_requisite(callback: CallbackQuery) -> None:
    req_id = int(callback.data.split(":")[1])
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    await db.delete_requisite(req_id, callback.from_user.id)
    await callback.answer(t(lang, "requisite_deleted"))
    await render_requisites(callback.message, lang, callback.from_user.id)
