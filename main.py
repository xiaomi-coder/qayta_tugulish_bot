import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from handlers.handlers import router
from utils.scheduler import setup_scheduler

# ── Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("🚀 QAYTA TUG'ILISH Bot ishga tushmoqda...")

    # ── Database initsializatsiya
    await init_db()
    logger.info("✅ Database tayyor")

    # ── Bot va Dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # ── Scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("✅ Scheduler ishga tushdi")

    # ── Webhook o'chirish (polling uchun)
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("✅ Bot polling boshlandi!")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("   QAYTA TUG'ILISH FITNESS BOT")
    logger.info("   @farruxradjabov tomonidan")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("🛑 Bot to'xtatildi")


if __name__ == "__main__":
    asyncio.run(main())
