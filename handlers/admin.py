import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

import config
import database as db
from locales import t
from utils.helpers import format_amount

router = Router()
logger = logging.getLogger(__name__)


def _is_admin_user(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def _is_admin(callback: CallbackQuery) -> bool:
    return callback.from_user.id in config.ADMIN_IDS


@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    deal_number = callback.data.split(":")[1]
    deal = await db.get_deal_by_number(deal_number)
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return

    await db.update_deal_status(deal["id"], "completed", admin_id=callback.from_user.id)

    try:
        await callback.message.edit_caption(caption=(callback.message.caption or "") + "\n\n✅ Подтверждено")
    except Exception:
        logger.exception("Не удалось отредактировать сообщение админа по сделке #%s", deal_number)
    await callback.answer("Подтверждено")

    seller = await db.get_user(deal["seller_id"])
    if seller:
        try:
            await bot.send_message(
                deal["seller_id"], t(seller["language"], "deal_confirmed_seller", deal_number=deal_number)
            )
        except Exception:
            logger.exception("Не удалось уведомить продавца %s о подтверждении сделки #%s", deal["seller_id"], deal_number)

    if deal["buyer_id"]:
        buyer = await db.get_user(deal["buyer_id"])
        if buyer:
            try:
                await bot.send_message(
                    deal["buyer_id"], t(buyer["language"], "deal_confirmed_buyer", deal_number=deal_number)
                )
            except Exception:
                logger.exception("Не удалось уведомить покупателя %s о подтверждении сделки #%s", deal["buyer_id"], deal_number)


@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    deal_number = callback.data.split(":")[1]
    deal = await db.get_deal_by_number(deal_number)
    if not deal:
        await callback.answer("Сделка не найдена", show_alert=True)
        return

    await db.update_deal_status(deal["id"], "rejected", admin_id=callback.from_user.id)

    try:
        await callback.message.edit_caption(caption=(callback.message.caption or "") + "\n\n❌ Отклонено")
    except Exception:
        logger.exception("Не удалось отредактировать сообщение админа по сделке #%s", deal_number)
    await callback.answer("Отклонено")

    seller = await db.get_user(deal["seller_id"])
    if seller:
        try:
            await bot.send_message(
                deal["seller_id"], t(seller["language"], "deal_rejected_seller", deal_number=deal_number)
            )
        except Exception:
            logger.exception("Не удалось уведомить продавца %s об отклонении сделки #%s", deal["seller_id"], deal_number)

    if deal["buyer_id"]:
        buyer = await db.get_user(deal["buyer_id"])
        if buyer:
            try:
                await bot.send_message(
                    deal["buyer_id"], t(buyer["language"], "deal_rejected_buyer", deal_number=deal_number)
                )
            except Exception:
                logger.exception("Не удалось уведомить покупателя %s об отклонении сделки #%s", deal["buyer_id"], deal_number)

    # покупатель может попробовать оплатить ещё раз
    await db.update_deal_status(deal["id"], "waiting_payment")


@router.callback_query(F.data.startswith("admin_del_approve:"))
async def admin_del_approve(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    req = await db.get_deletion_request(req_id)
    if not req:
        await callback.answer("Запрос не найден", show_alert=True)
        return

    deal = await db.get_deal_by_id(req["deal_id"])
    await db.update_deletion_request_status(req_id, "approved", callback.from_user.id)
    await db.update_deal_status(deal["id"], "deleted", admin_id=callback.from_user.id)

    try:
        await callback.message.edit_text((callback.message.text or "") + "\n\n✅ Удалено")
    except Exception:
        logger.exception("Не удалось отредактировать сообщение админа по запросу на удаление #%s", req_id)
    await callback.answer("Удалено")

    participant_ids = {deal["seller_id"]}
    if deal["buyer_id"]:
        participant_ids.add(deal["buyer_id"])

    for uid in participant_ids:
        u = await db.get_user(uid)
        if u:
            try:
                await bot.send_message(uid, t(u["language"], "deletion_approved", deal_number=deal["deal_number"]))
            except Exception:
                logger.exception("Не удалось уведомить %s об удалении сделки #%s", uid, deal["deal_number"])


@router.callback_query(F.data.startswith("admin_del_reject:"))
async def admin_del_reject(callback: CallbackQuery, bot) -> None:
    if not _is_admin(callback):
        await callback.answer("Недоступно", show_alert=True)
        return

    req_id = int(callback.data.split(":")[1])
    req = await db.get_deletion_request(req_id)
    if not req:
        await callback.answer("Запрос не найден", show_alert=True)
        return

    deal = await db.get_deal_by_id(req["deal_id"])
    await db.update_deletion_request_status(req_id, "rejected", callback.from_user.id)

    try:
        await callback.message.edit_text((callback.message.text or "") + "\n\n❌ Отклонено")
    except Exception:
        logger.exception("Не удалось отредактировать сообщение админа по запросу на удаление #%s", req_id)
    await callback.answer("Отклонено")

    requester = await db.get_user(req["requested_by"])
    if requester:
        try:
            await bot.send_message(
                req["requested_by"],
                t(requester["language"], "deletion_declined", deal_number=deal["deal_number"]),
            )
        except Exception:
            logger.exception("Не удалось уведомить %s об отклонении запроса на удаление сделки #%s", req["requested_by"], deal["deal_number"])


# ---------- редактирование профилей (доступно только админам) ----------

@router.message(Command("viewprofile"))
async def admin_view_profile(message: Message, command: CommandObject) -> None:
    if not _is_admin_user(message.from_user.id):
        return  # не палим существование команды не-админам

    args = (command.args or "").split()
    if len(args) != 1:
        await message.answer("Использование: /viewprofile <user_id>")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await message.answer("❗ user_id должен быть числом.")
        return

    target = await db.get_user(target_id)
    if not target:
        await message.answer(f"❗ Пользователь {target_id} не найден в базе (ещё не писал боту).")
        return

    stats = await db.get_user_stats(target_id)
    label = f"@{target['username']}" if target["username"] else target["full_name"] or str(target_id)

    text = (
        f"👤 Профиль пользователя {label} (ID: {target_id})\n\n"
        f"Баланс: {format_amount(stats['balance'], 'card', 'ru')}\n"
        f"  из них сумма завершённых сделок: {format_amount(stats['completed_sum'], 'card', 'ru')}\n"
        f"  ручная корректировка: {format_amount(stats['balance_adjustment'], 'card', 'ru')}\n"
        f"Сделок как продавец: {stats['sold']}\n"
        f"Сделок как покупатель: {stats['bought']}\n"
        f"Всего сделок: {stats['total']}\n\n"
        f"Изменить баланс: /setbalance {target_id} <новый_баланс>"
    )
    await message.answer(text)


@router.message(Command("setbalance"))
async def admin_set_balance(message: Message, command: CommandObject) -> None:
    if not _is_admin_user(message.from_user.id):
        return

    args = (command.args or "").split()
    if len(args) != 2:
        await message.answer("Использование: /setbalance <user_id> <новый_баланс>")
        return

    try:
        target_id = int(args[0])
        new_balance = float(args[1].replace(",", "."))
    except ValueError:
        await message.answer("❗ user_id и баланс должны быть числами.")
        return

    target = await db.get_user(target_id)
    if not target:
        await message.answer(f"❗ Пользователь {target_id} не найден в базе (ещё не писал боту).")
        return

    stats_before = await db.get_user_stats(target_id)
    new_adjustment = new_balance - stats_before["completed_sum"]
    await db.set_balance_adjustment(target_id, new_adjustment)

    await message.answer(
        f"✅ Баланс пользователя {target_id} изменён:\n"
        f"было {format_amount(stats_before['balance'], 'card', 'ru')} → "
        f"стало {format_amount(new_balance, 'card', 'ru')}"
    )

    try:
        await message.bot.send_message(
            target_id,
            f"ℹ️ Ваш баланс в профиле изменён администратором. "
            f"Текущий баланс: {format_amount(new_balance, 'card', 'ru')}",
        )
    except Exception:
        logger.exception("Не удалось уведомить пользователя %s об изменении баланса", target_id)
