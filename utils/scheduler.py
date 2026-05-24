import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database.db import get_all_users, get_today_water
from data.meals_data import get_day_meals, get_day_tip, get_motivation

logger = logging.getLogger(__name__)


async def send_morning_message(bot):
    """Har kuni ertalab 07:00 da xabar yuboradi"""
    users = await get_all_users()
    sent = 0
    for user in users:
        try:
            uid = user["telegram_id"]
            day = user.get("challenge_day", 1)
            tip = get_day_tip(day)
            motivation = get_motivation(day)
            meals = get_day_meals(day)
            first_meal = meals[0] if meals else None

            text = (
                f"☀️ *Xayrli tong, {user['full_name']}!*\n\n"
                f"🔥 Bugun *{day}-kun* challendj!\n\n"
                f"_{motivation}_\n\n"
                f"💡 _{tip}_\n\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🌅 Birinchi ovqat: *{first_meal['name']} — {first_meal['time']}*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"Botni oching va kunni boshlang! 💪"
            )

            await bot.send_message(uid, text, parse_mode="Markdown")
            sent += 1
        except Exception as e:
            logger.warning(f"Xabar yuborilmadi {user.get('telegram_id')}: {e}")

    logger.info(f"✅ Ertalabki xabar: {sent} ta yuborildi")


async def send_meal_reminder(bot, meal_name: str, meal_time: str, icon: str):
    """Ovqat vaqtida eslatma"""
    users = await get_all_users()
    for user in users:
        try:
            await bot.send_message(
                user["telegram_id"],
                f"{icon} *{meal_name} vaqti — {meal_time}!*\n\n"
                f"Ovqatni o'z vaqtida isting — natija shu!\n\n"
                f"/start — Botni ochish",
                parse_mode="Markdown"
            )
        except Exception:
            pass


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
                f"Keyin emas — HOZIR boshlang! 🚀\n\n"
                f"/start — Mashqlarga o'tish",
                parse_mode="Markdown"
            )
        except Exception:
            pass


async def send_water_reminder(bot):
    """Har 2 soatda suv eslatmasi"""
    users = await get_all_users()
    for user in users:
        try:
            water = await get_today_water(user["telegram_id"])
            goal = user.get("water_goal", 3000)
            if water < goal:
                remaining = goal - water
                await bot.send_message(
                    user["telegram_id"],
                    f"💧 *Suv içish vaqti!*\n\n"
                    f"Bugun ichildi: *{water}ml*\n"
                    f"Qoldi: *{remaining}ml*\n\n"
                    f"Hozir bir stakan suv iching! 🥤",
                    parse_mode="Markdown"
                )
        except Exception:
            pass


async def send_evening_summary(bot):
    """Kechqurun 21:00 da kunlik hisobot"""
    users = await get_all_users()
    for user in users:
        try:
            uid = user["telegram_id"]
            water = await get_today_water(uid)
            goal = user.get("water_goal", 3000)
            water_pct = min(int((water / goal) * 100), 100)

            await bot.send_message(
                uid,
                f"🌙 *Kunlik hisobot*\n\n"
                f"💧 Suv: *{water}ml / {goal}ml* ({water_pct}%)\n"
                f"{'✅ Maqsad bajarildi!' if water >= goal else '❌ Maqsad bajarilmadi'}\n\n"
                f"😴 Uxlashdan oldin:\n"
                f"• Telefon ekranidan uzoqroq yuring\n"
                f"• Ertaga uchun dam oling\n\n"
                f"*Yaxshi tun! Ertaga yangi kun — yangi imkoniyat!* 🌟",
                parse_mode="Markdown"
            )
        except Exception:
            pass


def setup_scheduler(bot) -> AsyncIOScheduler:
    """Barcha schedulerlarni sozlash"""
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # Ertalabki xabar — 07:00
    scheduler.add_job(
        send_morning_message, CronTrigger(hour=7, minute=0),
        args=[bot], id="morning_msg", replace_existing=True
    )

    # Nonushta eslatmasi — 07:25
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=7, minute=25),
        args=[bot, "Nonushta", "07:30", "🌅"],
        id="breakfast_reminder", replace_existing=True
    )

    # 2-Nonushta — 10:25
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=10, minute=25),
        args=[bot, "2-Nonushta", "10:30", "🥜"],
        id="second_breakfast_reminder", replace_existing=True
    )

    # Tushlik — 12:55
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=12, minute=55),
        args=[bot, "Tushlik", "13:00", "🍗"],
        id="lunch_reminder", replace_existing=True
    )

    # Kechki oldi — 16:25
    scheduler.add_job(
        send_meal_reminder, CronTrigger(hour=16, minute=25),
        args=[bot, "Kechki oldi", "16:30", "🥗"],
        id="pre_dinner_reminder", replace_existing=True
    )

    # Mashq eslatmasi — 17:00
    scheduler.add_job(
        send_workout_reminder, CronTrigger(hour=17, minute=0),
        args=[bot], id="workout_reminder", replace_existing=True
    )

    # Suv eslatmasi — 10:00, 14:00, 16:00
    for hour in [10, 14, 16]:
        scheduler.add_job(
            send_water_reminder, CronTrigger(hour=hour, minute=0),
            args=[bot], id=f"water_reminder_{hour}", replace_existing=True
        )

    # Kechki hisobot — 21:00
    scheduler.add_job(
        send_evening_summary, CronTrigger(hour=21, minute=0),
        args=[bot], id="evening_summary", replace_existing=True
    )

    return scheduler
