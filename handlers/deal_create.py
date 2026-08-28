from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import database as db
from keyboards.inline import currency_kb
from keyboards.main_menu import main_menu_kb
from locales import all_variants, t
from states.states import DealCreate
from utils.helpers import card_line, format_amount, generate_deal_number, is_menu_command

router = Router()


@router.message(F.text.in_(all_variants("menu_create_deal")))
async def start_deal_creation(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    reqs = await db.get_requisites(message.from_user.id)
    card_reqs = [r for r in reqs if r["type"].startswith("card_")]

    await state.set_state(DealCreate.choosing_currency)

    text = t(lang, "choose_currency")
    if not card_reqs:
        # Карту нельзя выбрать в сделке, пока она не привязана в Реквизитах —
        # поэтому кнопки карты в клавиатуре не будет, только подсказка.
        text += "\n\n" + t(lang, "no_cards_hint")

    await message.answer(text, reply_markup=currency_kb(lang, card_reqs))


@router.callback_query(DealCreate.choosing_currency, F.data.startswith("card_req:"))
async def choose_card_requisite(callback: CallbackQuery, state: FSMContext) -> None:
    """Продавец выбрал одну из своих привязанных карт — валюта сделки становится
    'card', а конкретные страна+номер карты сохраняются вместе со сделкой."""
    req_id = int(callback.data.split(":")[1])
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    req = await db.get_requisite_by_id(req_id, callback.from_user.id)
    if not req:
        await callback.answer(t(lang, "deal_not_found"), show_alert=True)
        return

    country = req["type"].removeprefix("card_")
    await state.update_data(currency="card", card_country=country, card_value=req["value"])
    await state.set_state(DealCreate.entering_amount)
    await callback.message.edit_text(t(lang, "enter_amount"))
    await callback.answer()


@router.callback_query(DealCreate.choosing_currency, F.data.startswith("currency:"))
async def choose_currency(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.split(":")[1]
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    await state.update_data(currency=currency, card_country=None, card_value=None)
    await state.set_state(DealCreate.entering_amount)
    await callback.message.edit_text(t(lang, "enter_amount"))
    await callback.answer()


@router.message(DealCreate.entering_amount)
async def enter_amount(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    if is_menu_command(message.text):
        await state.clear()
        await message.answer(t(lang, "action_cancelled"), reply_markup=main_menu_kb(lang))
        return

    raw = (message.text or "").replace(",", ".").strip()
    try:
        amount = float(raw)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(t(lang, "invalid_amount"))
        return

    await state.update_data(amount=amount)
    await state.set_state(DealCreate.entering_description)
    await message.answer(t(lang, "enter_description"))


@router.message(DealCreate.entering_description)
async def enter_description(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    if is_menu_command(message.text):
        await state.clear()
        await message.answer(t(lang, "action_cancelled"), reply_markup=main_menu_kb(lang))
        return

    description = (message.text or "").strip()[:500]
    if not description:
        await message.answer(t(lang, "enter_description"))
        return

    data = await state.get_data()
    deal_number = generate_deal_number()

    await db.create_deal(
        deal_number=deal_number,
        seller_id=message.from_user.id,
        currency=data["currency"],
        amount=data["amount"],
        description=description,
        card_country=data.get("card_country"),
        card_value=data.get("card_value"),
    )
    await state.clear()

    link = f"https://t.me/{config.BOT_USERNAME}?start={deal_number}"
    amount_str = format_amount(data["amount"], data["currency"], lang)

    text = t(
        lang,
        "deal_created",
        deal_number=deal_number,
        amount=amount_str,
        description=description,
        link=link,
    )
    text += card_line(lang, data.get("card_country"), data.get("card_value"))

    await message.answer(
        text,
        reply_markup=main_menu_kb(lang),
        disable_web_page_preview=True,
    )
