import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "helpes_deal")
DB_PATH = os.getenv("DB_PATH", "guarant_bot.db")

# Заполняется в bot.py при старте через set_bot_username(),
# используется для формирования ссылок на сделки (t.me/<username>?start=...)
BOT_USERNAME = None


def set_bot_username(username: str) -> None:
    global BOT_USERNAME
    BOT_USERNAME = username
