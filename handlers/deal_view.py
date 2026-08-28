import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import database as db
from keyboards.inline import admin_deletion_kb, admin_review_kb, buyer_deal_kb, support_contact_kb
from keyboards.main_menu import main_menu_kb
from locales import t
from states.states import BuyerPay
from utils.helpers import card_line, format_amount, is_menu_command

router = Router()
logger = logging.getLogger(__name__)


async def show_deal_to_buyer(message: Message, deal_number: str, lang: str) -> None:
    deal = await db.get_deal_by_number(deal_number)
    if not deal:
        await message.answer(t(lang, "deal_not_found"), reply_markup=main_menu_kb(lang))
        return

    if deal["seller_id"] == message.from_user.id:
        await message.answer(t(lang, "deal_own"), reply_markup=main_menu_kb(lang))
        return

    if deal["buyer_id"] and deal["buyer_id"] != message.from_user.id:
        await message.answer(t(lang, "deal_taken"), reply_markup=main_menu_kb(lang))
        return

    if not deal["buyer_id"]:
        await db.set_deal_buyer(deal["id"], message.from_user.id)

    seller_stats = await db.get_user_stats(deal["seller_id"])
    amount_str = format_amount(deal["amount"], deal["currency"], lang)

    text = t(
        lang,
        "deal_card_for_buyer",
        deal_number=deal["deal_number"],
        amount=amount_str,
        description=deal["description"],
    )
    text += card_line(lang, deal.get("card_country"), deal.get("card_value"))
    text += "\n\n" + t(
        lang,
        "seller_profile_preview",
        balance=format_amount(seller_stats["balance"], "card", lang),
        deals_count=seller_stats["total"],
    )

    await message.answer(text, reply_markup=buyer_deal_kb(lang, deal["deal_number"]))


@router.callback_query(F.data.startswith("pay_support:"))
async def pay_via_support(callback: CallbackQuery) -> None:
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]
    await callback.message.answer(
        t(lang, "pay_via_support"),
        reply_markup=support_contact_kb(lang, config.SUPPORT_USERNAME),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("i_paid:"))
async def i_paid(callback: CallbackQuery, state: FSMContext) -> None:
    deal_number = callback.data.split(":")[1]
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    deal = await db.get_deal_by_number(deal_number)
    if not deal or deal["buyer_id"] != callback.from_user.id:
        await callback.answer(t(lang, "deal_not_found"), show_alert=True)
        return

    await state.update_data(deal_number=deal_number)
    await state.set_state(BuyerPay.waiting_screenshot)
    await callback.message.answer(t(lang, "ask_screenshot"))
    await callback.answer()


@router.message(BuyerPay.waiting_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext, bot) -> None:
    data = await state.get_data()
    deal_number = data.get("deal_number")

    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    deal = await db.get_deal_by_number(deal_number) if deal_number else None
    if not deal:
        await state.clear()
        return

    file_id = message.photo[-1].file_id
    await db.update_deal_screenshot(deal["id"], file_id)
    await db.update_deal_status(deal["id"], "pending_review")
    await state.clear()

    await message.answer(t(lang, "screenshot_received"))

    seller = await db.get_user(deal["seller_id"])
    buyer = await db.get_user(deal["buyer_id"])
    amount_str = format_amount(deal["amount"], deal["currency"], "ru")

    seller_label = f"@{seller['username']}" if seller and seller["username"] else f"id{deal['seller_id']}"
    buyer_label = f"@{buyer['username']}" if buyer and buyer["username"] else f"id{deal['buyer_id']}"

    admin_text = (
        f"🆕 Новая сделка на проверку\n\n"
        f"Сделка: #{deal['deal_number']}\n"
        f"Сумма: {amount_str}\n"
        f"Описание: {deal['description']}"
        f"{card_line('ru', deal.get('card_country'), deal.get('card_value'))}\n\n"
        f"Продавец: {seller_label}\n"
        f"Покупатель: {buyer_label}"
    )

    if not config.ADMIN_IDS:
        logger.warning("ADMIN_IDS пуст — некому отправить сделку #%s на проверку.", deal["deal_number"])

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id, file_id, caption=admin_text, reply_markup=admin_review_kb(deal["deal_number"])
            )
        except Exception:
            logger.exception(
                "Не удалось отправить сделку #%s админу %s. Убедитесь, что админ уже нажал /start в этом боте.",
                deal["deal_number"],
                admin_id,
            )


@router.message(BuyerPay.waiting_screenshot)
async def waiting_screenshot_fallback(message: Message, state: FSMContext) -> None:
    user = await db.get_or_create_user(message.from_user)
    lang = user["language"]

    if is_menu_command(message.text):
        await state.clear()
        await message.answer(t(lang, "action_cancelled"), reply_markup=main_menu_kb(lang))
        return

    await message.answer(t(lang, "ask_screenshot"))


@router.callback_query(F.data.startswith("req_del:"))
async def request_deletion(callback: CallbackQuery, bot) -> None:
    deal_number = callback.data.split(":")[1]
    user = await db.get_or_create_user(callback.from_user)
    lang = user["language"]

    deal = await db.get_deal_by_number(deal_number)
    if not deal:
        await callback.answer(t(lang, "deal_not_found"), show_alert=True)
        return

    req_id = await db.create_deletion_request(deal["id"], callback.from_user.id)
    await callback.answer(t(lang, "deletion_request_sent"), show_alert=True)

    requester_label = f"@{user['username']}" if user["username"] else f"id{callback.from_user.id}"
    amount_str = format_amount(deal["amount"], deal["currency"], "ru")

    admin_text = (
        f"🗑 Запрос на удаление сделки #{deal['deal_number']}\n\n"
        f"От: {requester_label}\n"
        f"Сумма: {amount_str}\n"
        f"Описание: {deal['description']}"
    )

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=admin_deletion_kb(req_id))
        except Exception:
            logger.exception(
                "Не удалось отправить запрос на удаление сделки #%s админу %s.",
                deal["deal_number"],
                admin_id,
            )
