from . import en, ru, ua

LOCALES = {
    "ru": ru.TEXTS,
    "ua": ua.TEXTS,
    "en": en.TEXTS,
}


def t(lang: str, key: str, **kwargs) -> str:
    """Возвращает локализованный текст по ключу, с fallback на русский."""
    texts = LOCALES.get(lang, LOCALES["ru"])
    template = texts.get(key) or LOCALES["ru"].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


def all_variants(key: str) -> list[str]:
    """Все переводы данного ключа — используется для фильтров reply-кнопок,
    чтобы бот узнавал нажатие кнопки независимо от текущего языка юзера."""
    return [texts.get(key, key) for texts in LOCALES.values()]
