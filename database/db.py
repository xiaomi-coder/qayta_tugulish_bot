import aiosqlite
import logging
from datetime import datetime, date
from config import DB_PATH

logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # USERS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                gender TEXT DEFAULT 'erkak',
                region TEXT DEFAULT '',
                height REAL DEFAULT 0,
                weight REAL DEFAULT 0,
                plan_key TEXT DEFAULT '',
                challenge_day INTEGER DEFAULT 0,
                challenge_started TEXT,
                water_goal INTEGER DEFAULT 5000,
                is_premium INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                registered_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # PAYMENTS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                method TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                receipt_file_id TEXT,
                plan_key TEXT,
                wlcm_order_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)
        # Migration: mavjud DB ga wlcm_order_id ustunini qo'shish
        try:
            await db.execute("ALTER TABLE payments ADD COLUMN wlcm_order_id INTEGER")
            await db.commit()
        except Exception:
            pass  # ustun allaqachon bor
        # Migration: to'lov xabari message_id (vaqt tugaganda tahrirlash uchun)
        try:
            await db.execute("ALTER TABLE payments ADD COLUMN tg_message_id INTEGER")
            await db.commit()
        except Exception:
            pass  # ustun allaqachon bor
        # Migration: foydalanuvchi mashq turi (gym=sport zali, home=uy sharoiti)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN workout_type TEXT DEFAULT 'gym'")
            await db.commit()
        except Exception:
            pass  # ustun allaqachon bor
        # NUTRITION PLANS (admin kiritadi)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_key TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                cal_range TEXT,
                protein TEXT,
                carb TEXT,
                fat TEXT,
                description TEXT,
                meals TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # CHALLENGE PROGRESS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS challenge_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                day INTEGER NOT NULL,
                completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                UNIQUE(user_id, day)
            )
        """)
        # WATER LOGS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS water_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)
        # MEAL LOGS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS meal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                day INTEGER NOT NULL,
                meal_index INTEGER NOT NULL,
                logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                UNIQUE(user_id, day, meal_index)
            )
        """)
        # EXERCISE LOGS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS exercise_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                day INTEGER NOT NULL,
                exercise_index INTEGER NOT NULL,
                logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                UNIQUE(user_id, day, exercise_index)
            )
        """)
        # MEAL PHOTOS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS meal_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                meal_index INTEGER NOT NULL,
                photo_file_id TEXT NOT NULL,
                caption TEXT DEFAULT '',
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(day, meal_index)
            )
        """)
        # Mavjud jadvalga caption ustunini qo'shish (migration)
        try:
            await db.execute("ALTER TABLE meal_photos ADD COLUMN caption TEXT DEFAULT ''")
        except Exception:
            pass
        # EXERCISE VIDEOS
        await db.execute("""
            CREATE TABLE IF NOT EXISTS exercise_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_key TEXT NOT NULL,
                video_file_id TEXT NOT NULL,
                video_type TEXT DEFAULT 'video_note',
                caption TEXT DEFAULT '',
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(exercise_key)
            )
        """)
        # Mavjud jadvalga caption ustunini qo'shish (migration)
        try:
            await db.execute("ALTER TABLE exercise_videos ADD COLUMN caption TEXT DEFAULT ''")
        except Exception:
            pass
        # Migration: eski kun videolari (day{N}_v{i}) 'gym' kategoriyasiga o'tkaziladi
        # (yangi sxema: {category}_day{N}_v{i}). Idempotent — qayta ishga tushса ta'sir qilmaydi.
        try:
            await db.execute(
                "UPDATE exercise_videos SET exercise_key='gym_'||exercise_key "
                "WHERE exercise_key GLOB 'day[0-9]*_v[0-9]*'"
            )
            await db.commit()
        except Exception:
            pass
        # PROGRESS PHOTOS (boshlang'ich / yakuniy tan surati)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS progress_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phase TEXT DEFAULT 'before',
                file_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # RATSION PLAN RASMLARI (80+, 90-110, 110+, 9-13 yosh)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ration_plan_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_key TEXT UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                caption TEXT DEFAULT '',
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Users jadvaliga age_group ustunini qo'shish
        try:
            await db.execute("ALTER TABLE users ADD COLUMN age_group TEXT DEFAULT 'adult'")
        except Exception:
            pass
        # BOT MEDIA (welcome video etc)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_key TEXT UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                media_type TEXT DEFAULT 'video',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Default nutrition plans
        await _insert_default_plans(db)
        await db.commit()
        logger.info("✅ Database initialized")

async def _insert_default_plans(db):
    plans = [
        ("standard", "⚪ Standart Plan (100 kg gacha)", "2000-2400", "150g", "260g", "65g",
         "Standart vazn uchun balansli ratsion. Sport natijalari uchun optimal.",
         "Nonushta: Suli+tuxum+meva|Tushlik: Tovuq+guruch+salat|Kechki: Baliq+sabzavot"),
        ("plan_100_150", "🟡 Plan A — 100-150 kg", "1800-2200", "200g", "180g", "60g",
         "Intensiv yog' yoqish rejimi. Past uglevod, yuqori oqsil. Kaloriyadar 500 taqchil.",
         "Nonushta: Tuxum oq 6ta+sabzavot|Tushlik: Tovuq 300g+brokkoli|Kechki: Baliq+salat"),
        ("plan_150_200", "🟠 Plan B — 150-200 kg", "1600-2000", "220g", "150g", "55g",
         "Maxsus intensiv dastur. Har 3 soatda kichik porsiyalar. Shifokor nazoratida.",
         "Nonushta: Tuxum oq 8ta|Tushlik: Tovuq 350g+ko'k sabzavot|Kechki: Baliq+brokkoli"),
        ("plan_200_plus", "🔴 Plan C — 200+ kg", "1400-1800", "250g", "120g", "50g",
         "Eng intensiv dastur. Faqat oqsil va sabzavot. Shifokor va dietolog bilan birgalikda.",
         "Nonushta: Tuxum oq 10ta|Tushlik: Tovuq 400g+sabzavot|Kechki: Tuna+salat"),
    ]
    for p in plans:
        try:
            await db.execute("""
                INSERT OR IGNORE INTO nutrition_plans
                (plan_key, title, cal_range, protein, carb, fat, description, meals)
                VALUES (?,?,?,?,?,?,?,?)
            """, p)
        except Exception:
            pass

# ════════ USER ════════
async def get_user(tid: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)) as c:
            r = await c.fetchone()
            return dict(r) if r else None

async def create_user(tid: int, username: str, full_name: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (telegram_id,username,full_name) VALUES(?,?,?)",
                         (tid, username, full_name))
        await db.commit()

async def update_user(tid: int, **kw) -> None:
    if not kw: return
    fields = ", ".join(f"{k}=?" for k in kw)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {fields} WHERE telegram_id=?",
                         [*kw.values(), tid])
        await db.commit()

async def get_all_users() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE is_active=1") as c:
            return [dict(r) for r in await c.fetchall()]

async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            r = await c.fetchone(); return r[0] if r else 0

async def get_premium_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium=1") as c:
            r = await c.fetchone(); return r[0] if r else 0

# ════════ PAYMENT ════════
async def create_payment(uid: int, amount: int, method: str, plan_key: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO payments (user_id, amount, method, plan_key)
            VALUES (?,?,?,?)
        """, (uid, amount, method, plan_key))
        await db.commit()
        return cur.lastrowid

async def update_payment(pay_id: int, **kw) -> None:
    if not kw: return
    fields = ", ".join(f"{k}=?" for k in kw)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE payments SET {fields} WHERE id=?", [*kw.values(), pay_id])
        await db.commit()

async def get_pending_payments() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, u.full_name, u.phone, u.weight, u.username
            FROM payments p JOIN users u ON p.user_id=u.telegram_id
            WHERE p.status='pending' ORDER BY p.created_at DESC
        """) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_payment(pay_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE id=?", (pay_id,)) as c:
            r = await c.fetchone(); return dict(r) if r else None

async def get_payment_by_external(external_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM payments WHERE id=?", (external_id,)) as c:
            r = await c.fetchone(); return dict(r) if r else None

async def confirm_payment_auto(bot, pay_id: int) -> None:
    """WLCM webhook orqali to'lovni avtomatik tasdiqlaydi va premium beradi."""
    from datetime import datetime
    payment = await get_payment(pay_id)
    if not payment:
        return
    if payment.get("status") == "confirmed":
        return  # Ikki marta tasdiqlamaslik

    uid = payment["user_id"]
    plan_key = payment.get("plan_key", "standard")

    await update_payment(pay_id, status="confirmed", confirmed_at=datetime.now().isoformat())
    await update_user(uid, is_premium=1, challenge_day=1,
                      challenge_started=datetime.now().isoformat())

    # ── Adminlarga "Yangi to'lov" bildirishnomasi ──
    try:
        from config import ADMIN_IDS
        _u = await get_user(uid)
        _txt = (
            f"💰 <b>YANGI TO'LOV!</b>\n\n"
            f"👤 {(_u.get('full_name') if _u else '') or '-'}\n"
            f"📱 {(_u.get('phone') if _u else '') or '-'}\n"
            f"💵 {payment.get('amount', 0):,} so'm — {str(payment.get('method','')).upper()}\n"
            f"🆔 pay_id={pay_id}"
        )
        for _aid in ADMIN_IDS:
            try:
                await bot.send_message(_aid, _txt, parse_mode="HTML")
            except Exception:
                pass
    except Exception:
        pass

    # ── Bot vaqtincha yopiq: to'lov qabul, lekin kontent dushanbadan ──
    from config import LAUNCH_LOCKED, LAUNCH_DATE_TEXT
    if LAUNCH_LOCKED:
        try:
            await bot.send_message(
                uid,
                f"🎉 <b>TABRIKLAYMIZ! To'lovingiz qabul qilindi!</b> ✅\n\n"
                f"🔒 Joyingiz band — siz marafon ishtirokchisisiz!\n"
                f"🗓 Mashqlar va ratsion <b>{LAUNCH_DATE_TEXT}dan</b> boshlanadi.\n\n"
                f"{LAUNCH_DATE_TEXT.capitalize()}da botda sizga xabar beramiz. Tayyor turing! 💪",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # Foydalanuvchiga xabar
    from config import PLAN_NAMES, RATION_PLAN_KEYS, get_ration_plan_key
    user = await get_user(uid)
    plan = await get_nutrition_plan(plan_key)
    plan_name = PLAN_NAMES.get(plan_key, "")
    meals_list = ""
    if plan and plan.get("meals"):
        for m in plan["meals"].split("|"):
            meals_list += f"• {m.strip()}\n"

    from keyboards.keyboards import main_menu_kb
    try:
        await bot.send_message(
            uid,
            f"🎉 <b>TABRIKLAYMIZ!</b>\n\n"
            f"✅ To'lovingiz tasdiqlandi! (Paylov)\n"
            f"🔥 30-kunlik challendj boshlandi!\n\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🥗 <b>SIZNING RATSIONINGIZ:</b>\n"
            f"<b>{plan_name}</b>\n\n"
            f"📊 Kaloriya: {plan['cal_range'] if plan else '-'} kkal\n"
            f"💪 Oqsil: {plan['protein'] if plan else '-'}\n"
            f"🌾 Uglevod: {plan['carb'] if plan else '-'}\n"
            f"🫒 Yog': {plan['fat'] if plan else '-'}\n\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🍽️ <b>Kunlik menyu:</b>\n{meals_list}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"Pastdagi menyudan boshlang! 💪",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
    except Exception:
        pass

    # Ratsion plan rasmini yuborish
    user_age_group = user.get("age_group", "adult") if user else "adult"
    user_weight = float(user.get("weight") or 80) if user else 80.0
    rp_key = get_ration_plan_key(user_weight, user_age_group)
    rp_img = await get_ration_plan_image(rp_key)
    if rp_img:
        rp_cap = (rp_img.get("caption") or
                  f"🥗 {RATION_PLAN_KEYS.get(rp_key, 'Sizning ratsioningiz')}\n\nKunlik ovqatlanish rejangiz! 💪")
        try:
            await bot.send_photo(uid, photo=rp_img["file_id"],
                                 caption=rp_cap[:1024], protect_content=True)
        except Exception:
            pass

# ════════ NUTRITION PLANS ════════
async def get_nutrition_plan(plan_key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM nutrition_plans WHERE plan_key=?", (plan_key,)) as c:
            r = await c.fetchone(); return dict(r) if r else None

async def update_nutrition_plan(plan_key: str, **kw) -> None:
    if not kw: return
    fields = ", ".join(f"{k}=?" for k in kw)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE nutrition_plans SET {fields},updated_at=? WHERE plan_key=?",
                         [*kw.values(), datetime.now().isoformat(), plan_key])
        await db.commit()

async def get_all_nutrition_plans() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM nutrition_plans") as c:
            return [dict(r) for r in await c.fetchall()]

# ════════ BOT MEDIA ════════
async def save_bot_media(key: str, file_id: str, mtype: str = "video") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO bot_media (media_key,file_id,media_type) VALUES(?,?,?)",
                         (key, file_id, mtype))
        await db.commit()

async def get_bot_media(key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bot_media WHERE media_key=?", (key,)) as c:
            r = await c.fetchone(); return dict(r) if r else None

# ════════ CHALLENGE ════════
async def get_completed_days(uid: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT day FROM challenge_progress WHERE user_id=? ORDER BY day", (uid,)) as c:
            return [r[0] for r in await c.fetchall()]

async def complete_day(uid: int, day: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO challenge_progress (user_id,day) VALUES(?,?)", (uid, day))
            await db.execute("UPDATE users SET challenge_day=MAX(challenge_day,?) WHERE telegram_id=?", (day, uid))
            await db.commit(); return True
        except aiosqlite.IntegrityError: return False

async def uncomplete_day(uid: int, day: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM challenge_progress WHERE user_id=? AND day=?", (uid, day))
        await db.commit()

# ════════ WATER ════════
async def get_today_water(uid: int) -> int:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COALESCE(SUM(amount),0) FROM water_logs WHERE user_id=? AND log_date=?",
                               (uid, today)) as c:
            r = await c.fetchone(); return r[0] if r else 0

async def add_water(uid: int, amount: int) -> int:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO water_logs (user_id,amount,log_date) VALUES(?,?,?)", (uid, amount, today))
        await db.commit()
    return await get_today_water(uid)

# ════════ MEALS ════════
async def log_meal(uid: int, day: int, idx: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO meal_logs (user_id,day,meal_index) VALUES(?,?,?)", (uid,day,idx))
            await db.commit(); return True
        except aiosqlite.IntegrityError:
            await db.execute("DELETE FROM meal_logs WHERE user_id=? AND day=? AND meal_index=?", (uid,day,idx))
            await db.commit(); return False

async def get_logged_meals(uid: int, day: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT meal_index FROM meal_logs WHERE user_id=? AND day=?", (uid,day)) as c:
            return [r[0] for r in await c.fetchall()]

# ════════ EXERCISES ════════
async def log_exercise(uid: int, day: int, idx: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO exercise_logs (user_id,day,exercise_index) VALUES(?,?,?)", (uid,day,idx))
            await db.commit(); return True
        except aiosqlite.IntegrityError:
            await db.execute("DELETE FROM exercise_logs WHERE user_id=? AND day=? AND exercise_index=?", (uid,day,idx))
            await db.commit(); return False

async def get_logged_exercises(uid: int, day: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT exercise_index FROM exercise_logs WHERE user_id=? AND day=?", (uid,day)) as c:
            return [r[0] for r in await c.fetchall()]

# ════════ MEAL PHOTOS ════════
async def save_meal_photo(day: int, idx: int, fid: str, caption: str = "") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO meal_photos (day,meal_index,photo_file_id,caption) VALUES(?,?,?,?)",
            (day, idx, fid, caption)
        )
        await db.commit()

async def get_meal_photo(day: int, idx: int) -> dict | None:
    """Returns {'file_id': ..., 'caption': ...} or None"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT photo_file_id, caption FROM meal_photos WHERE day=? AND meal_index=?",
            (day, idx)
        ) as c:
            r = await c.fetchone()
            return {"file_id": r[0], "caption": r[1] or ""} if r else None

# Ratsion ovqatlari uchun alohida (day=0 ishlatiladi)
async def save_ration_photo(meal_idx: int, fid: str, caption: str = "") -> None:
    await save_meal_photo(0, meal_idx, fid, caption)

async def get_ration_photo(meal_idx: int) -> dict | None:
    return await get_meal_photo(0, meal_idx)

# ════════ RATSION PLAN RASMLARI ════════
async def save_ration_plan_image(plan_key: str, file_id: str, caption: str = "") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO ration_plan_images (plan_key, file_id, caption) VALUES (?,?,?)",
            (plan_key, file_id, caption)
        )
        await db.commit()

async def get_ration_plan_image(plan_key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id, caption FROM ration_plan_images WHERE plan_key=?",
            (plan_key,)
        ) as c:
            r = await c.fetchone()
            return {"file_id": r[0], "caption": r[1] or ""} if r else None

async def get_all_ration_plan_images() -> dict:
    """Barcha plan rasmlarini {plan_key: {file_id, caption}} formatida qaytaradi"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan_key, file_id, caption FROM ration_plan_images") as c:
            rows = await c.fetchall()
            return {r[0]: {"file_id": r[1], "caption": r[2] or ""} for r in rows}

# ════════ EXERCISE VIDEOS ════════
async def save_exercise_video(key: str, fid: str, vtype: str = "video_note", caption: str = "") -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO exercise_videos (exercise_key,video_file_id,video_type,caption) VALUES(?,?,?,?)",
            (key, fid, vtype, caption)
        )
        await db.commit()

async def get_exercise_video(key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT video_file_id, video_type, caption FROM exercise_videos WHERE exercise_key=?",
            (key,)
        ) as c:
            r = await c.fetchone()
            return {"file_id": r[0], "type": r[1], "caption": r[2] or ""} if r else None

# ════════ KUN ASOSIDA VIDEO (har bir kun uchun ko'p video) ════════
async def save_day_video(day: int, fid: str, vtype: str = "video_note",
                         caption: str = "", category: str = "gym") -> int:
    """Kun uchun video saqlaydi. category: 'gym' (sport zali) yoki 'home' (uy sharoiti).
    Bir kun+kategoriyaga ko'p video bo'lishi mumkin. Qaytaradi: shu kategoriyadagi jami video soni."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM exercise_videos WHERE exercise_key GLOB ?",
            (f"{category}_day{day}_v*",)
        ) as c:
            count = (await c.fetchone())[0]
        key = f"{category}_day{day}_v{count}"
        await db.execute(
            "INSERT OR REPLACE INTO exercise_videos (exercise_key,video_file_id,video_type,caption) VALUES(?,?,?,?)",
            (key, fid, vtype, caption)
        )
        await db.commit()
        return count + 1

async def save_progress_photo(user_id: int, file_id: str, phase: str = "before") -> int:
    """Foydalanuvchi tan suratini saqlaydi. phase: 'before' yoki 'after'.
    Qaytaradi: shu foydalanuvchi+fazadagi jami surat soni."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO progress_photos (user_id, phase, file_id) VALUES (?,?,?)",
            (user_id, phase, file_id)
        )
        await db.commit()
        async with db.execute(
            "SELECT COUNT(*) FROM progress_photos WHERE user_id=? AND phase=?",
            (user_id, phase)
        ) as c:
            return (await c.fetchone())[0]

async def get_progress_photos(user_id: int, phase: str = "before") -> list:
    """Foydalanuvchining tan suratlarini (file_id) qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id FROM progress_photos WHERE user_id=? AND phase=? ORDER BY id",
            (user_id, phase)
        ) as c:
            return [r[0] for r in await c.fetchall()]


async def get_day_videos(day: int, category: str = "gym") -> list:
    """Kun+kategoriya uchun barcha videolarni tartibida qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT video_file_id, video_type, caption FROM exercise_videos "
            "WHERE exercise_key GLOB ? ORDER BY exercise_key",
            (f"{category}_day{day}_v*",)
        ) as c:
            rows = await c.fetchall()
            return [{"file_id": r[0], "type": r[1], "caption": r[2] or ""} for r in rows]

async def delete_day_videos(day: int, category: str = "gym") -> int:
    """Kun+kategoriyaning barcha videolarini o'chiradi. Qaytaradi: o'chirilgan soni."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM exercise_videos WHERE exercise_key GLOB ?",
            (f"{category}_day{day}_v*",)
        ) as c:
            count = (await c.fetchone())[0]
        await db.execute(
            "DELETE FROM exercise_videos WHERE exercise_key GLOB ?",
            (f"{category}_day{day}_v*",)
        )
        await db.commit()
        return count

# ════════ REGION STATS ════════
async def get_users_by_region() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT region, COUNT(*) as cnt FROM users GROUP BY region ORDER BY cnt DESC"
        ) as c:
            rows = await c.fetchall()
            return {r[0] or "Noma'lum": r[1] for r in rows}

async def get_all_users_detailed() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT telegram_id, full_name, phone, region, weight, height,
                   gender, plan_key, is_premium, challenge_day, created_at
            FROM users ORDER BY created_at DESC
        """) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_users_by_filter(region: str = None, premium: int = None) -> list:
    conditions, params = [], []
    if region:
        conditions.append("region = ?"); params.append(region)
    if premium is not None:
        conditions.append("is_premium = ?"); params.append(premium)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(f"SELECT * FROM users {where}", params) as c:
            return [dict(r) for r in await c.fetchall()]

async def search_user(query: str) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM users
            WHERE full_name LIKE ? OR phone LIKE ? OR username LIKE ?
            LIMIT 10
        """, (f"%{query}%", f"%{query}%", f"%{query}%")) as c:
            return [dict(r) for r in await c.fetchall()]

# ════════ PAYMENT ANALYTICS ════════
async def get_pending_payments_full() -> list:
    """To'lagan lekin admin tasdiqlamagan"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, u.full_name, u.phone, u.region,
                   u.weight, u.username, u.telegram_id as uid
            FROM payments p
            JOIN users u ON p.user_id = u.telegram_id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
        """) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_rejected_payments() -> list:
    """Rad etilgan to'lovlar"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, u.full_name, u.phone, u.region, u.weight
            FROM payments p
            JOIN users u ON p.user_id = u.telegram_id
            WHERE p.status = 'rejected'
            ORDER BY p.created_at DESC
            LIMIT 20
        """) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_never_paid_users() -> list:
    """Ro'yxatdan o'tgan lekin hech to'lov qilmagan"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT u.*
            FROM users u
            LEFT JOIN payments p ON u.telegram_id = p.user_id
            WHERE p.id IS NULL
              AND u.registered_at IS NOT NULL
              AND u.is_active = 1
            ORDER BY u.created_at DESC
        """) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_inactive_premium_users() -> list:
    """Premium lekin challendjda qatnashmayotganlar"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT u.*,
                   COUNT(cp.day) as done_days
            FROM users u
            LEFT JOIN challenge_progress cp ON u.telegram_id = cp.user_id
            WHERE u.is_premium = 1 AND u.is_active = 1
            GROUP BY u.telegram_id
            HAVING done_days < 3
            ORDER BY done_days ASC
        """) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_pending_users_ids() -> list:
    """To'lov kutilayotgan userlar ID si"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT DISTINCT user_id FROM payments WHERE status = 'pending'
        """) as c:
            return [r[0] for r in await c.fetchall()]

async def get_payment_summary() -> dict:
    """To'lov umumiy hisobot"""
    async with aiosqlite.connect(DB_PATH) as db:
        summary = {}
        for status in ["pending", "confirmed", "rejected"]:
            async with db.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount),0) FROM payments WHERE status=?",
                (status,)
            ) as c:
                r = await c.fetchone()
                summary[status] = {"count": r[0], "amount": r[1]}
        return summary
