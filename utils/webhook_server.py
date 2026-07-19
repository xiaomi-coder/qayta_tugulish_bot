import json
import logging
from aiohttp import web

logger = logging.getLogger(__name__)


async def _verify_paid_via_api(wlcm_order_id) -> bool:
    """WLCM order status API orqali to'lov haqiqatan amalga oshganini tekshiradi.
    Bu webhook body ga emas, WLCM ning o'z ma'lumotiga ishonadi (xavfsiz)."""
    if not wlcm_order_id:
        return False
    import aiohttp
    from config import WLCM_BASE_URL
    url = f"{WLCM_BASE_URL}/api/v1/orders/{wlcm_order_id}/status"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10),
                                   headers={"User-Agent": "curl/7.88.1"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return bool(data.get("is_paid"))
    except Exception as e:
        logger.warning("Webhook API verify error (order_id=%s): %s", wlcm_order_id, e)
    return False


async def wlcm_webhook(request: web.Request) -> web.Response:
    """WLCM dan kelgan to'lov bildirishnomasi.

    Strategiya: webhook faqat "tekshir" signali sifatida ishlatiladi.
    Body ga ishonmasdan, WLCM order status API orqali is_paid tasdiqlanadi —
    shuning uchun imzo formati noma'lum bo'lsa ham xavfsiz ishlaydi.
    """
    from database.db import get_payment_by_external, confirm_payment_auto

    raw_body = await request.read()
    logger.info("WLCM webhook headers: %s", dict(request.headers))
    logger.info("WLCM webhook raw body: %s", raw_body.decode(errors="replace"))

    try:
        data = json.loads(raw_body)
        logger.info("WLCM webhook parsed: %s", data)
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    # external_id = bizning pay_id (checkout da shunday yuborganmiz).
    # Turli formatlarni qamrab olamiz.
    external_id = (
        data.get("external_id")
        or data.get("external_order_id")
        or (data.get("order") or {}).get("external_id")
        or (data.get("payment") or {}).get("external_id")
    )
    order_id = (
        data.get("order_id")
        or (data.get("order") or {}).get("id")
        or (data.get("payment") or {}).get("order_id")
    )

    if not external_id:
        logger.warning("WLCM webhook: external_id topilmadi — e'tiborsiz qoldirildi")
        return web.Response(text="OK")

    try:
        pay_id = int(external_id)
    except (TypeError, ValueError):
        logger.warning("WLCM webhook: external_id raqam emas: %s", external_id)
        return web.Response(text="OK")

    payment = await get_payment_by_external(str(pay_id))
    if not payment:
        logger.warning("WLCM webhook: pay_id=%s DB da topilmadi", pay_id)
        return web.Response(text="OK")

    # Tekshirish uchun WLCM order ID: DB dagi yoki webhook dagi
    wlcm_order_id = payment.get("wlcm_order_id") or order_id

    # WLCM API orqali haqiqatan to'langanligini tasdiqlaymiz
    if await _verify_paid_via_api(wlcm_order_id):
        try:
            bot = request.app["bot"]
            await confirm_payment_auto(bot, pay_id)
            logger.info("WLCM webhook: pay_id=%s API orqali tasdiqlandi va premium berildi", pay_id)
        except Exception as e:
            logger.error("WLCM webhook confirm error pay_id=%s: %s", pay_id, e)
    else:
        logger.info("WLCM webhook: pay_id=%s — API da hali to'lanmagan (order_id=%s)",
                    pay_id, wlcm_order_id)

    return web.Response(text="OK")


def create_webhook_app(bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/wlcm/webhook", wlcm_webhook)
    return app
