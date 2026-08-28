import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
import database as db
from handlers import admin, deal_create, deal_view, language, misc, profile, requisites, start, support

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан. Проверьте .env / переменные окружения.")

    if not config.ADMIN_IDS:
        logger.warning("ADMIN_IDS не заданы — подтверждать сделки будет некому!")
    else:
        logger.info("Загружены ADMIN_IDS: %s", config.ADMIN_IDS)

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок важен только там, где могли бы пересекаться фильтры;
    # здесь у каждого роутера свои уникальные команды/callback-префиксы.
    dp.include_router(start.router)
    dp.include_router(deal_create.router)
    dp.include_router(deal_view.router)
    dp.include_router(profile.router)
    dp.include_router(requisites.router)
    dp.include_router(language.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)
    dp.include_router(misc.router)

    await db.init_db()

    me = await bot.get_me()
    config.set_bot_username(me.username)
    logger.info("Бот запущен: @%s", me.username)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
