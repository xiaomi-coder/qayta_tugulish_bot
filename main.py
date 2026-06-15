import asyncio
import logging
import os
import signal
import socket
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN, wlcm_enabled, WLCM_WEBHOOK_PORT
from database.db import init_db
from handlers.handlers import router
from utils.scheduler import setup_scheduler

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


def _free_port(port: int) -> None:
    """Portni band qilgan processni o'ldiradi."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", port))
    except OSError:
        # Port band — fuser bilan o'ldiramiz
        os.system(f"fuser -k {port}/tcp 2>/dev/null")
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.5))


async def main():
    logger.info("🚀 QAYTA TUG'ILISH Bot ishga tushmoqda...")

    await init_db()
    logger.info("✅ Database tayyor")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("✅ Scheduler ishga tushdi")

    await bot.delete_webhook(drop_pending_updates=True)

    # ── WLCM Webhook server
    wlcm_runner = None
    if wlcm_enabled():
        try:
            _free_port(WLCM_WEBHOOK_PORT)
            from utils.webhook_server import create_webhook_app
            wlcm_app = create_webhook_app(bot)
            wlcm_runner = web.AppRunner(wlcm_app)
            await wlcm_runner.setup()
            site = web.TCPSite(wlcm_runner, "0.0.0.0", WLCM_WEBHOOK_PORT,
                               reuse_address=True, reuse_port=True)
            await site.start()
            logger.info("✅ WLCM webhook server port %s da ishga tushdi", WLCM_WEBHOOK_PORT)
        except Exception as e:
            logger.error("❌ WLCM webhook server ishga tushmadi: %s", e)
            wlcm_runner = None

    logger.info("✅ Bot polling boshlandi!")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("   QAYTA TUG'ILISH FITNESS BOT")
    logger.info("   @QaytaTugulishBot")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        if wlcm_runner:
            await wlcm_runner.cleanup()
        await bot.session.close()
        logger.info("🛑 Bot to'xtatildi")


if __name__ == "__main__":
    asyncio.run(main())
