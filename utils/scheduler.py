import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.db import get_all_users, get_today_water, get_bot_media
from data.meals_data import get_day_tip, get_motivation

logger = logging.getLogger(__name__)


# ── Ertalabki xabar + motivatsiya video ──────────────────────
async def send_morning_message(bot):
    """Har kuni ertalab 07:00 da xabar yuboradi"""
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
    users = await get_all_users()
    for user in users:
        try:
            water = await get_today_water(user["telegram_id"])
            goal = user.get("water_goal", 4000)  # 90-110kg uchun 4-6 litr
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
    users = await get_all_users()
    for user in users:
        try:
            uid = user["telegram_id"]
            water = await get_today_water(uid)
            goal = user.get("water_goal", 4000)
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

    return scheduler
