import uuid

from locales import LOCALES, t

MENU_KEYS = [
    "menu_create_deal",
    "menu_profile",
    "menu_withdraw",
    "menu_requisites",
    "menu_language",
    "menu_support",
]

CURRENCY_ICONS = {
    "card": "💳",
    "gram": "💎",
    "stars": "⭐",
}

COUNTRY_FLAGS = {
    "ua": "🇺🇦",
    "ru": "🇷🇺",
    "by": "🇧🇾",
}

# Реальная валюта, привязанная к стране карты — показывается вместо
# generic-иконки 💳, чтобы сумма сделки сразу читалась как настоящие деньги.
CARD_CURRENCY_SYMBOLS = {
    "ua": "₴",
    "ru": "₽",
    "by": "Br",
}


def generate_deal_number() -> str:
    """Короткий публичный номер сделки, например 37410e49."""
    return uuid.uuid4().hex[:8]


def format_amount(amount: float, currency: str, lang: str = "ru", card_country: str | None = None) -> str:
    if float(amount) == int(amount):
        amount_str = str(int(amount))
    else:
        amount_str = f"{amount:.2f}".rstrip("0").rstrip(".")

    if currency == "card" and card_country in CARD_CURRENCY_SYMBOLS:
        unit = CARD_CURRENCY_SYMBOLS[card_country]
    else:
        unit = CURRENCY_ICONS.get(currency, "")

    return f"{amount_str} {unit}".strip()


def card_line(lang: str, card_country: str | None, card_value: str | None) -> str:
    """Строка вида '\\nКарта: 🇺🇦 4441 1111 2222 3333' для показа в карточке сделки.
    Возвращает пустую строку, если сделка не привязана к конкретной карте."""
    if not card_value:
        return ""
    flag = COUNTRY_FLAGS.get(card_country or "", "💳")
    label = t(lang, "card_label")
    return f"\n{label}: {flag} {card_value}"


def is_menu_command(text: str | None) -> bool:
    """Проверяет, не является ли текст нажатием одной из кнопок главного меню
    (на любом из языков) — используется, чтобы не "проглатывать" переключение
    меню, если юзер передумал посреди FSM-сценария (создание сделки и т.п.)."""
    if not text:
        return False
    for key in MENU_KEYS:
        for texts in LOCALES.values():
            if texts.get(key) == text:
                return True
    return False
