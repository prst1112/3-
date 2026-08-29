from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from locales import t


def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=t(lang, "menu_create_deal"))],
        [KeyboardButton(text=t(lang, "menu_profile"))],
        [KeyboardButton(text=t(lang, "menu_withdraw")), KeyboardButton(text=t(lang, "menu_requisites"))],
        [KeyboardButton(text=t(lang, "menu_language"))],
        [KeyboardButton(text=t(lang, "menu_support"))],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
