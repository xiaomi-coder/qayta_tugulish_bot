import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.db import get_all_users, get_today_water, get_bot_media, confirm_payment_auto
from data.meals_data import get_day_tip, get_motivation
from config import ADMIN_IDS, wlcm_enabled, LAUNCH_LOCKED

logger = logging.getLogger(__name__)


# ── Ertalabki xabar + motivatsiya video ──────────────────────
async def send_morning_message(bot):
    """Har kuni ertalab 07:00 da xabar yuboradi"""
    if LAUNCH_LOCKED:
        return  # bot yopiq — eslatmalar dushanbadan
    users = await get_all_users()
    sent = 0

    # Motivatsiya video bormi?
    motiv_video = await get_bot_media("motivation_video")

    for user in users:
        try:
            uid = user["telegram_id"]
            day = user.get("challenge_day", 1)
            tip = get_day_tip(day)
            motivation = get_motivation(day)

            text = (
                f"☀️ *Xayrli tong, {user['full_name']}!*\n\n"
                f"🔥 Bugun *{day}-kun* challendj!\n\n"
                f"_{motivation}_\n\n"
                f"💡 _{tip}_\n\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🌅 Nonushta: *07:00 — 08:30*\n"
                f"🍗 Tushlik: *12:30 — 13:30*\n"
                f"🥗 Oraliq: *15:30 — 16:30*\n"
                f"🌙 Kechki: *19:00 — 20:00*\n"
                f"💊 Yotishdan oldin: *21:30 — 22:30*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"Botni oching va kunni boshlang! 💪"
            )

            # Avval motivatsiya video (agar bor bo'lsa)
            if motiv_video:
                try:
                    if motiv_video.get("type") == "video_note":
                        await bot.send_video_note(uid, video_note=motiv_video["file_id"])
                    else:
                        await bot.send_video(
                            uid, video=motiv_video["file_id"],
                            caption="🔥 *Bugungi motivatsiya!*", parse_mode="Markdown"
                        )
                except Exception:
                    pass

            await bot.send_message(uid, text, parse_mode="Markdown")
            sent += 1
        except Exception as e:
            logger.warning(f"Xabar yuborilmadi {user.get('telegram_id')}: {e}")

    logger.info(f"✅ Ertalabki xabar: {sent} ta yuborildi")


# ── Ovqat eslatmasi ──────────────────────────────────────────
async def send_meal_reminder(bot, meal_name: str, meal_time: str, icon: str):
    """Ovqat vaqtida eslatma"""
    if LAUNCH_LOCKED:
        return
    users = await get_all_users()
    for user in users:
        try:
            await bot.send_message(
                user["telegram_id"],
                f"{icon} *{meal_name} vaqti — {meal_time}!*\n\n"
                f"Ovqatni o'z vaqtida isting — natija shu!\n\n"
                f"Botni oching 👇",
                parse_mode="Markdown"
            )
        except Exception:
            pass


# ── Mashq eslatmasi ──────────────────────────────────────────
async def send_workout_reminder(bot):
    """17:00 da mashq eslatmasi"""
    if LAUNCH_LOCKED:
        return
    users = await get_all_users()
    for user in users:
        try:
            day = user.get("challenge_day", 1)
            await bot.send_message(
                user["telegram_id"],
                f"💪 *MASHQ VAQTI!*\n\n"
                f"🔥 Bugun {day}-kun mashqlari sizni kutmoqda!\n\n"
                f"Keyin emas — HOZIR boshlang! 🚀",
                parse_mode="Markdown"
            )
        except Exception:
            pass


# ── Suv eslatmasi ────────────────────────────────────────────
async def send_water_reminder(bot):
    """Suv eslatmasi"""
    if LAUNCH_LOCKED:
        return
    users = await get_all_users()
    for user in users:
        try:
            water = await get_today_water(user["telegram_id"])
            goal = user.get("water_goal", 5000)  # 90-110kg uchun 4-6 litr
            if water < goal:
                remaining = goal - water
                await bot.send_message(
                    user["telegram_id"],
                    f"💧 *Suv ichish vaqti!*\n\n"
                    f"Bugun ichildi: *{water}ml*\n"
                    f"Qoldi: *{remaining}ml*\n\n"
                    f"Hozir bir stakan suv iching! 🥤\n"
                    f"_Maqsad: 4-6 litr/kun_",
                    parse_mode="Markdown"
                )
        except Exception:
            pass


# ── Kechki hisobot ───────────────────────────────────────────
async def send_evening_summary(bot):
    """Kechqurun 21:00 da kunlik hisobot"""
    if LAUNCH_LOCKED:
        return
    users = await get_all_users()
    for user in users:
        try:
            uid = user["telegram_id"]
            water = await get_today_water(uid)
            goal = user.get("water_goal", 5000)
            water_pct = min(int((water / goal) * 100), 100)

            await bot.send_message(
                uid,
                f"🌙 *Kunlik hisobot*\n\n"
                f"💧 Suv: *{water}ml / {goal}ml* ({water_pct}%)\n"
                f"{'✅ Maqsad bajarildi!' if water >= goal else '❌ Maqsad bajarilmadi'}\n\n"
                f"💊 Eslatma: Yotishdan oldin proteinni iching!\n"
                f"_21:30 — 22:30_\n\n"
                f"*Yaxshi tun! Ertaga yangi kun — yangi imkoniyat!* 🌟",
                parse_mode="Markdown"
            )
        except Exception:
            pass


_notified_pay_ids: set = set()  # session ichida takroriy xabar yubormaslik uchun


# ── WLCM API orqali to'lov statusini tekshirish ─────────────
async def _check_wlcm_order_status(order_id: int) -> bool:
    """WLCM /api/v1/orders/{order_id}/status endpoint ni chaqiradi.
    is_paid=True bo'lsa True qaytaradi."""
    import aiohttp
    from config import WLCM_BASE_URL
    url = f"{WLCM_BASE_URL}/api/v1/orders/{order_id}/status"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10),
                                   headers={"User-Agent": "curl/7.88.1"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("is_paid", False)
    except Exception as e:
        logger.warning("WLCM order status check error (order_id=%s): %s", order_id, e)
    return False


# ── WLCM pending to'lovlarni tekshirish ─────────────────────
async def check_pending_wlcm_payments(bot):
    """Har 2 daqiqada: WLCM to'lovlarini API orqali tekshirib avtomatik tasdiqlaydi.
    30 daqiqa ichida to'lanmasa — 'expired' qilib, foydalanuvchiga vaqt tugaganini bildiradi.
    wlcm_order_id bo'lmasa va 15 daqiqa o'tsa — adminга bildiradi."""
    if not wlcm_enabled():
        return
    import aiosqlite
    from datetime import datetime, timezone
    from config import DB_PATH
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT p.id, p.user_id, p.amount, p.method, p.created_at,
                       p.wlcm_order_id, p.tg_message_id, u.full_name, u.phone
                FROM payments p
                JOIN users u ON p.user_id = u.telegram_id
                WHERE p.status = 'pending'
                  AND p.method IN ('payme','click','paylov','uzum','card')
                ORDER BY p.created_at ASC
            """) as cur:
                rows = [dict(r) for r in await cur.fetchall()]
    except Exception as e:
        logger.error("check_pending_wlcm_payments DB error: %s", e)
        return

    for pay in rows:
        wlcm_oid = pay.get("wlcm_order_id")

        # To'lov yoshi (daqiqada)
        try:
            created = datetime.fromisoformat(pay["created_at"].replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_min = (datetime.now(timezone.utc) - created).total_seconds() / 60
        except Exception:
            age_min = 999

        # WLCM order ID bor — API orqali statusni tekshir
        if wlcm_oid:
            is_paid = await _check_wlcm_order_status(wlcm_oid)
            if is_paid:
                try:
                    from database.db import confirm_payment_auto
                    await confirm_payment_auto(bot, pay["id"])
                    logger.info("WLCM polling: order_id=%s to'langan — pay_id=%s avtomatik tasdiqlandi",
                                wlcm_oid, pay["id"])
                except Exception as e:
                    logger.error("WLCM polling confirm error pay_id=%s: %s", pay["id"], e)
                continue

            # To'lanmagan va 30 daqiqa o'tgan — vaqt tugadi
            if age_min >= 30:
                try:
                    from database.db import update_payment
                    await update_payment(pay["id"], status="expired")
                    msg_id = pay.get("tg_message_id")
                    if msg_id:
                        b = InlineKeyboardBuilder()
                        b.button(text="🔄 Qaytadan to'lash", callback_data="go_payment")
                        await bot.edit_message_text(
                            chat_id=pay["user_id"], message_id=msg_id,
                            text=(
                                "⏰ <b>Vaqtingiz tugadi</b>\n\n"
                                "To'lov 30 daqiqa ichida amalga oshmadi.\n"
                                "Iltimos, to'lovni qaytadan boshlang 👇"
                            ),
                            reply_markup=b.as_markup()
                        )
                    logger.info("WLCM polling: pay_id=%s vaqti tugadi (expired)", pay["id"])
                except Exception as e:
                    logger.warning("WLCM polling expire error pay_id=%s: %s", pay["id"], e)
            continue  # API orqali tekshirildi, admin ga xabar shart emas

        # wlcm_order_id yo'q va 15 daqiqa o'tgan — adminга bildirish
        if pay["id"] in _notified_pay_ids:
            continue

        if age_min < 15:
            continue

        try:
            b = InlineKeyboardBuilder()
            b.button(text="✅ Premiumni ber", callback_data=f"admin_confirm:{pay['id']}:{pay['user_id']}")
            b.button(text="❌ Rad et",        callback_data=f"admin_reject:{pay['id']}:{pay['user_id']}")
            b.adjust(2)
            text = (
                f"⏳ <b>Tasdiqlanmagan to'lov</b>\n\n"
                f"👤 {pay['full_name']} ({pay['phone']})\n"
                f"💰 {pay['amount']:,} so'm — {pay['method'].upper()}\n"
                f"🕐 {pay['created_at']}\n"
                f"🆔 pay_id={pay['id']}\n\n"
                f"<i>WLCM order ID yo'q — qo'lda tasdiqlang</i>"
            )
            for admin_id in ADMIN_IDS:
                await bot.send_message(admin_id, text, reply_markup=b.as_markup())
            _notified_pay_ids.add(pay["id"])
            logger.info("WLCM polling: admin ga pay_id=%s haqida xabar yuborildi", pay["id"])
        except Exception as e:
            logger.warning("check_pending_wlcm_payments notify error: %s", e)


# ── Barcha schedulerlar ──────────────────────────────────────
def setup_scheduler(bot) -> AsyncIOScheduler:
    """Barcha schedulerlarni sozlash"""
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # ── Ertalabki xabar + motivatsiya video — 07:00
    scheduler.add_job(
        send_morning_message, CronTrigger(hour=7, minute=0),
        args=[bot], id="morning_msg", replace_existing=True
    )

    # ── Ratsion eslatmalari (haqiqiy vaqtlar) ──
    # Nonushta — 06:55 (07:00-08:30 dan 5 daqiqa oldin)
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=6, minute=55),
        args=[bot, "NONUSHTA", "07:00 — 08:30", "🌅"],
        id="breakfast_reminder", replace_existing=True
    )

    # Tushlik — 12:25
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=12, minute=25),
        args=[bot, "TUSHLIK", "12:30 — 13:30", "🍗"],
        id="lunch_reminder", replace_existing=True
    )

    # Oraliq ovqat — 15:25
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=15, minute=25),
        args=[bot, "ORALIQ OVQAT", "15:30 — 16:30", "🥗"],
        id="mid_reminder", replace_existing=True
    )

    # Kechki ovqat — 18:55
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=18, minute=55),
        args=[bot, "KECHKI OVQAT", "19:00 — 20:00", "🌙"],
        id="dinner_reminder", replace_existing=True
    )

    # Yotishdan oldin — 21:25
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=21, minute=25),
        args=[bot, "YOTISHDAN OLDIN (protein + arginin)", "21:30 — 22:30", "💊"],
        id="night_reminder", replace_existing=True
    )

    # ── Mashq eslatmasi — 17:00
    scheduler.add_job(
        send_workout_reminder, CronTrigger(hour=17, minute=0),
        args=[bot], id="workout_reminder", replace_existing=True
    )

    # ── Suv eslatmasi — 09:00, 11:00, 14:00, 16:00, 18:00
    for hour in [9, 11, 14, 16, 18]:
        scheduler.add_job(
            send_water_reminder, CronTrigger(hour=hour, minute=0),
            args=[bot], id=f"water_reminder_{hour}", replace_existing=True
        )

    # ── Kechki hisobot — 21:00
    scheduler.add_job(
        send_evening_summary, CronTrigger(hour=21, minute=0),
        args=[bot], id="evening_summary", replace_existing=True
    )

    # ── WLCM pending to'lovlar — har 2 daqiqada
    scheduler.add_job(
        check_pending_wlcm_payments,
        "interval", minutes=2,
        args=[bot], id="wlcm_pending_check", replace_existing=True
    )

    return scheduler
