import logging
from aiohttp import web

logger = logging.getLogger(__name__)


async def wlcm_webhook(request: web.Request) -> web.Response:
    """WLCM dan kelgan to'lov bildirishnomasi."""
    from config import WLCM_API_SECRET
    from database.db import get_payment_by_external, confirm_payment_auto
    from utils.wlcm import verify_webhook_signature

    raw_body = await request.read()
    logger.info("WLCM webhook headers: %s", dict(request.headers))
    logger.info("WLCM webhook raw body: %s", raw_body.decode(errors="replace"))

    try:
        import json
        data = json.loads(raw_body)
        logger.info("WLCM webhook parsed: %s", data)
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    # Imzo tekshirish — header yoki body dan
    if WLCM_API_SECRET:
        header_sig = request.headers.get("X-Webhook-Signature", "")
        body_sig = data.get("signature", "")
        if header_sig or body_sig:
            from utils.wlcm import verify_webhook_signature
            check_data = dict(data)
            if header_sig:
                check_data["signature"] = header_sig
            if not verify_webhook_signature(WLCM_API_SECRET, check_data):
                logger.warning("WLCM webhook: imzo noto'g'ri! header=%s body_sig=%s", header_sig, body_sig)
                return web.Response(status=403, text="Bad signature")
        else:
            logger.warning("WLCM webhook: imzo yo'q — davom etilmoqda (sandbox)")

    state = data.get("state")
    external_id = data.get("external_id")

    if state == 2 and external_id:
        # To'lov muvaffaqiyatli
        try:
            pay_id = int(external_id)
            bot = request.app["bot"]
            await confirm_payment_auto(bot, pay_id)
            logger.info("WLCM: pay_id=%s tasdiqland", pay_id)
        except Exception as e:
            logger.error("WLCM webhook confirm error: %s", e)
    elif state == -2:
        logger.info("WLCM: to'lov bekor qilindi, external_id=%s", external_id)

    return web.Response(text="OK")


def create_webhook_app(bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/wlcm/webhook", wlcm_webhook)
    return app
