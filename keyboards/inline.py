from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from locales import t


def currency_kb(lang: str, card_reqs: list[dict] | None = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора валюты сделки. Вместо одной общей кнопки «Карта»
    показывает конкретные привязанные карты продавца (страна + номер) —
    так покупатель сразу видит, на какую карту какой страны платить.
    Если карт нет, кнопка карты не показывается вовсе (см. no_cards_hint)."""
    icons = {"card_ua": "🇺🇦", "card_ru": "🇷🇺", "card_by": "🇧🇾"}
    b = InlineKeyboardBuilder()
    for r in card_reqs or []:
        icon = icons.get(r["type"], "💳")
        b.button(text=f"💳 {icon} {r['value']}", callback_data=f"card_req:{r['id']}")
    b.button(text=t(lang, "currency_gram"), callback_data="currency:gram")
    b.button(text=t(lang, "currency_stars"), callback_data="currency:stars")
    b.adjust(1)
    return b.as_markup()


def buyer_deal_kb(lang: str, deal_number: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "btn_pay_via_support"), callback_data=f"pay_support:{deal_number}")
    b.button(text=t(lang, "btn_i_paid"), callback_data=f"i_paid:{deal_number}")
    b.button(text=t(lang, "btn_request_deletion"), callback_data=f"req_del:{deal_number}")
    b.adjust(1)
    return b.as_markup()


def support_contact_kb(lang: str, support_username: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "btn_support"), url=f"https://t.me/{support_username}")
    b.adjust(1)
    return b.as_markup()


def admin_review_kb(deal_number: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Подтвердить", callback_data=f"admin_confirm:{deal_number}")
    b.button(text="❌ Отклонить", callback_data=f"admin_reject:{deal_number}")
    b.adjust(2)
    return b.as_markup()


def admin_deletion_kb(request_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Удалить", callback_data=f"admin_del_approve:{request_id}")
    b.button(text="❌ Отклонить", callback_data=f"admin_del_reject:{request_id}")
    b.adjust(2)
    return b.as_markup()


def language_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.button(text="🇺🇦 Українська", callback_data="lang:ua")
    b.button(text="🇬🇧 English", callback_data="lang:en")
    b.adjust(1)
    return b.as_markup()


def requisites_menu_kb(lang: str, reqs: list[dict]) -> InlineKeyboardMarkup:
    icons = {"card_ua": "🇺🇦", "card_ru": "🇷🇺", "card_by": "🇧🇾", "ton": "💎"}
    b = InlineKeyboardBuilder()
    for r in reqs:
        icon = icons.get(r["type"], "💳")
        b.button(text=f"🗑 {icon} {r['value'][:15]}", callback_data=f"del_req:{r['id']}")
    b.button(text=t(lang, "btn_add_card"), callback_data="add_card")
    b.button(text=t(lang, "btn_add_ton"), callback_data="add_ton")
    b.adjust(1)
    return b.as_markup()


def card_country_kb(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "card_ua"), callback_data="card_country:ua")
    b.button(text=t(lang, "card_ru"), callback_data="card_country:ru")
    b.button(text=t(lang, "card_by"), callback_data="card_country:by")
    b.adjust(1)
    return b.as_markup()
