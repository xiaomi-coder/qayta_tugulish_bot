import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from config import (ADMIN_IDS, PAYMENT_CARD, PAYMENT_PAYME, PAYMENT_CLICK,
                    PRICE_30_DAY, get_plan_by_weight, PLAN_NAMES)
from database.db import *
from keyboards.keyboards import *
from data.meals_data import get_day_meals, get_day_exercises, get_day_tip, get_motivation

logger = logging.getLogger(__name__)
router = Router()


# ═══════════════════════════
# WATERMARK & CONTENT PROTECTION
# ═══════════════════════════
WATERMARKS = [
    "Bugun ogrik - ertaga gurur! 🔥",
    "Toxtagan odam hech qachon yetmaydi! ⚡",
    "Har qadam maqsadga yaqinlashtiradi! 🎯",
    "Qiyin - chunki siz osib boryapsiz! 💪",
    "Champion hech qachon bahona aytmaydi! 🏆",
    "Bugun bajargan - ertangi sogliqing! 🌟",
    "Kuch - bu odatdan boshlanadi! ⚙",
    "Maqsad aniq bolsa - yol topiladi! 🧭",
    "Hech kim seni toxtata olmaydi! 🚀",
    "30 kun - bir umrlik ozgarish! 👑",
    "Semizlikdan ozginlikka - bu yangi hayot! 🌅",
    "Har kuni bir qadam - 30 kunda yangi odam! 💫",
    "Ogir vaqtlar otadi - kuchli odam qoladi! 💎",
    "Bugun sen - ertaga misol! 🌈",
    "Natija = sabr + mashq + ratsion! ⚖",
]

def get_watermark() -> str:
    idx = datetime.now().day % len(WATERMARKS)
    line = "=" * 17
    return (
        "\n" + line + "\n"
        + "💬 " + WATERMARKS[idx] + "\n"
        + "🔥 Qayta Tug'ilish Marafon | @QaytaTugulishBot\n"
        + line
    )

def wprotect(text: str) -> str:
    return text + get_watermark()

def get_watermark() -> str:
    idx = datetime.now().day % len(WATERMARKS)
    return (
        f"\n━━━━━━━━━━━━━━━━━\n"
        f"💬 {WATERMARKS[idx]}\n"
        f"🔥 Qayta Tug'ilish Marafon | @QaytaTugulishBot\n"
        f"━━━━━━━━━━━━━━━━━"
    )

def protect(text: str) -> str:
    """Har xabarga watermark qo'shish"""
    return text + get_watermark()



# ══════════════════════════════════
# STATES
# ══════════════════════════════════
class Reg(StatesGroup):
    name   = State()
    phone  = State()
    weight = State()
    height = State()
    gender = State()

class PayState(StatesGroup):
    method  = State()
    receipt = State()

class AdminSt(StatesGroup):
    broadcast    = State()
    photo_day    = State()
    photo_meal   = State()
    photo_file   = State()
    video_set    = State()
    video_index  = State()
    video_type   = State()
    video_file   = State()
    welcome_vid  = State()
    premium_id   = State()
    edit_plan_key = State()
    edit_plan_field = State()
    edit_plan_value = State()

# ══════════════════════════════════
# HELPERS
# ══════════════════════════════════
def wbar(cur, goal):
    p = min(cur/goal, 1.0)
    return f"{'▓'*int(p*10)}{'░'*(10-int(p*10))} {cur}/{goal}ml"

def greeting():
    h = datetime.now().hour
    return "☀️ Xayrli tong" if h<12 else "🌤️ Xayrli kun" if h<17 else "🌙 Xayrli kech"

def progress_bar(done, total=30):
    p = done/total
    return f"{'▓'*int(p*15)}{'░'*(15-int(p*15))} {done}/{total}"

# ══════════════════════════════════
# /START — WELCOME
# ══════════════════════════════════
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    user = await get_user(msg.from_user.id)

    if user and user.get("is_premium"):
        # Premium foydalanuvchi — asosiy menyu
        await msg.answer(
            f"{greeting()}, *{user['full_name']}*! 👋\n\n"
            f"🔥 *QAYTA TUG'ILISH*\n\n"
            f"_{get_motivation(user.get('challenge_day',1))}_",
            reply_markup=main_menu_kb(), parse_mode="Markdown"
        )
        return

    if user and user.get("registered_at") and not user.get("is_premium"):
        # Ro'yxatdan o'tgan lekin to'lamagan
        await msg.answer(
            f"Salom, *{user['full_name']}*! 👋\n\n"
            f"Siz hali to'lov qilmagansiz.\n"
            f"To'lovni amalga oshiring va 30-kunlik challendj boshlang! 💪",
            reply_markup=payment_method_kb(), parse_mode="Markdown"
        )
        await state.set_state(PayState.method)
        return

    # Yangi foydalanuvchi
    await create_user(msg.from_user.id, msg.from_user.username or "", msg.from_user.full_name or "")

    # Welcome video bormi?
    media = await get_bot_media("welcome_video")

    welcome_text = (
        "🔥 *QAYTA TUG'ILISH*\n"
        "_Professional GYM Trener — Farrux Rajabov_\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "💪 *30-KUNLIK CHALLENDJ*\n\n"
        "✅ Har kuni ovqat ratsioni\n"
        "✅ Har kuni mashq dasturi\n"
        "✅ Suv tracker\n"
        "✅ Kunlik eslatmalar\n"
        "✅ Vazningizga mos ratsion\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "🚀 Boshlashga tayyormisiz?"
    )

    if media:
        await msg.answer_video(
            video=media["file_id"],
            caption=welcome_text,
            reply_markup=start_kb(),
            parse_mode="Markdown"
        )
    else:
        await msg.answer(welcome_text, reply_markup=start_kb(), parse_mode="Markdown")

# ══════════════════════════════════
# REGISTRATION FLOW
# ══════════════════════════════════
@router.callback_query(F.data == "start_reg")
async def cb_start_reg(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    await call.message.answer(
        "📝 *RO'YXATDAN O'TISH*\n\n"
        "Ism va familiyangizni yozing:\n"
        "_Masalan: Jasur Toshmatov_",
        parse_mode="Markdown"
    )
    await state.set_state(Reg.name)
    await call.answer()

@router.message(Reg.name)
async def reg_name(msg: Message, state: FSMContext):
    if len(msg.text.strip()) < 2:
        await msg.answer("❌ Ism juda qisqa. Qaytadan yozing:"); return
    await state.update_data(name=msg.text.strip())
    await msg.answer(
        "📱 *Telefon raqamingizni yuboring*\n\n"
        "Tugmani bosib yuboring yoki qo'lda yozing (+998XXXXXXXXX)",
        reply_markup=phone_kb(), parse_mode="Markdown"
    )
    await state.set_state(Reg.phone)

@router.message(Reg.phone, F.contact)
async def reg_phone_contact(msg: Message, state: FSMContext):
    phone = msg.contact.phone_number
    await state.update_data(phone=phone)
    await msg.answer(
        "⚖️ *Vazningizni kiriting* (kg da)\n_Masalan: 120_",
        reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown"
    )
    await state.set_state(Reg.weight)

@router.message(Reg.phone)
async def reg_phone_text(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.text.strip())
    await msg.answer(
        "⚖️ *Vazningizni kiriting* (kg da)\n_Masalan: 120_",
        reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown"
    )
    await state.set_state(Reg.weight)

@router.message(Reg.weight)
async def reg_weight(msg: Message, state: FSMContext):
    try:
        w = float(msg.text.strip().replace(",","."))
        if not 30 <= w <= 500: raise ValueError
    except ValueError:
        await msg.answer("❌ Noto'g'ri. 30-500 orasida kiriting:"); return
    await state.update_data(weight=w)
    await msg.answer(
        "📏 *Bo'yingizni kiriting* (sm da)\n_Masalan: 175_",
        parse_mode="Markdown"
    )
    await state.set_state(Reg.height)

@router.message(Reg.height)
async def reg_height(msg: Message, state: FSMContext):
    try:
        h = float(msg.text.strip())
        if not 100 <= h <= 250: raise ValueError
    except ValueError:
        await msg.answer("❌ Noto'g'ri. 100-250 orasida kiriting:"); return
    await state.update_data(height=h)
    await msg.answer(
        "👤 *Jinsingizni tanlang:*",
        reply_markup=gender_kb(), parse_mode="Markdown"
    )
    await state.set_state(Reg.gender)

@router.callback_query(Reg.gender, F.data.startswith("gender:"))
async def reg_gender(call: CallbackQuery, state: FSMContext):
    gender = call.data.split(":")[1]
    data = await state.get_data()
    await state.clear()

    w = data["weight"]
    h = data["height"]
    bmi = w / ((h/100)**2)
    plan_key = get_plan_by_weight(w)
    plan_name = PLAN_NAMES[plan_key]

    bmi_text = ("🔵 Kam vazn" if bmi<18.5 else "🟢 Ideal" if bmi<25 else
                "🟡 Ortiqcha" if bmi<30 else "🔴 Semiz")
    gender_emoji = "👨" if gender == "erkak" else "👩"

    # Foydalanuvchini saqlash
    await update_user(call.from_user.id,
        full_name=data["name"], phone=data["phone"],
        weight=w, height=h, gender=gender, plan_key=plan_key,
        registered_at=datetime.now().isoformat()
    )

    await call.message.edit_reply_markup()
    await call.message.answer(
        f"✅ *Ma'lumotlaringiz saqlandi!*\n\n"
        f"{gender_emoji} {data['name']}\n"
        f"📱 {data['phone']}\n"
        f"⚖️ {w} kg | 📏 {h} sm\n"
        f"📊 BMI: {bmi:.1f} — {bmi_text}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🥗 *Sizning ratsion planingiz:*\n"
        f"*{plan_name}*\n\n"
        f"_To'lovdan so'ng ratsion va challendj avtomatik ochiladi!_",
        parse_mode="Markdown"
    )

    # Challenge haqida ma'lumot
    await call.message.answer(
        f"🔥 *30-KUNLIK CHALLENDJ NIMA?*\n\n"
        f"📅 *30 kun davomida:*\n"
        f"• Har kuni 4-5 ta ovqat retsepti\n"
        f"• Har kuni 4 ta mashq video\n"
        f"• Suv tracker (kunlik norma)\n"
        f"• Avtomatik eslatmalar\n"
        f"• Vazningizga mos ratsion\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 *Narx: {PRICE_30_DAY:,} so'm*\n\n"
        f"To'lovni amalga oshiring va boshlang! 👇",
        reply_markup=challenge_info_kb(), parse_mode="Markdown"
    )
    await call.answer()

# ══════════════════════════════════
# PAYMENT FLOW
# ══════════════════════════════════
@router.callback_query(F.data == "go_payment")
async def cb_go_payment(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    await call.message.answer(
        f"💳 *TO'LOV USULINI TANLANG*\n\n"
        f"💰 Narx: *{PRICE_30_DAY:,} so'm*\n\n"
        f"Qaysi usulda to'lashni xohlaysiz?",
        reply_markup=payment_method_kb(), parse_mode="Markdown"
    )
    await state.set_state(PayState.method)

@router.callback_query(PayState.method, F.data.startswith("pay_method:"))
async def cb_pay_method(call: CallbackQuery, state: FSMContext):
    method = call.data.split(":")[1]
    user = await get_user(call.from_user.id)
    plan_key = user.get("plan_key", "standard") if user else "standard"

    pay_id = await create_payment(call.from_user.id, PRICE_30_DAY, method, plan_key)
    await state.update_data(pay_id=pay_id, method=method)

    if method == "payme":
        details = (
            f"🟢 *PAYME ORQALI TO'LOV*\n\n"
            f"📱 Payme raqami: `{PAYMENT_PAYME}`\n"
            f"💰 Summa: *{PRICE_30_DAY:,} so'm*\n\n"
            f"1️⃣ Payme ilovasini oching\n"
            f"2️⃣ Yuborish → Raqam bo'yicha\n"
            f"3️⃣ `{PAYMENT_PAYME}` kiriting\n"
            f"4️⃣ *{PRICE_30_DAY:,} so'm* yuboring\n"
            f"5️⃣ Chek screenshotini saqlang\n\n"
            f"To'lovdan keyin chekni yuboring 👇"
        )
    elif method == "click":
        details = (
            f"🔵 *CLICK ORQALI TO'LOV*\n\n"
            f"🔗 Link: {PAYMENT_CLICK}\n"
            f"💰 Summa: *{PRICE_30_DAY:,} so'm*\n\n"
            f"1️⃣ Yuqoridagi linkni bosing\n"
            f"2️⃣ Click ilovasida to'lang\n"
            f"3️⃣ Chek screenshotini saqlang\n\n"
            f"To'lovdan keyin chekni yuboring 👇"
        )
    else:
        details = (
            f"💳 *KARTA ORQALI O'TKAZMA*\n\n"
            f"💳 Karta raqami: `{PAYMENT_CARD}`\n"
            f"💰 Summa: *{PRICE_30_DAY:,} so'm*\n\n"
            f"1️⃣ Bank ilovangizni oching\n"
            f"2️⃣ O'tkazma → Karta raqami\n"
            f"3️⃣ `{PAYMENT_CARD}` kiriting\n"
            f"4️⃣ *{PRICE_30_DAY:,} so'm* yuboring\n"
            f"5️⃣ Chek screenshotini saqlang\n\n"
            f"To'lovdan keyin chekni yuboring 👇"
        )

    await call.message.edit_text(details, reply_markup=after_payment_kb(), parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data == "send_receipt")
async def cb_send_receipt(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    await call.message.answer(
        "📸 *CHEKNI YUBORING*\n\n"
        "To'lov cheki (screenshot) rasmini yuboring.\n"
        "_Admin tekshirib, 5-15 daqiqada tasdiqlaydi._",
        parse_mode="Markdown"
    )
    await state.set_state(PayState.receipt)
    await call.answer()

@router.message(PayState.receipt, F.photo)
async def receipt_received(msg: Message, state: FSMContext):
    data = await state.get_data()
    pay_id = data.get("pay_id")
    method = data.get("method", "")
    file_id = msg.photo[-1].file_id
    user = await get_user(msg.from_user.id)

    if pay_id:
        await update_payment(pay_id, receipt_file_id=file_id)

    await state.clear()
    await msg.answer(
        "✅ *Chek qabul qilindi!*\n\n"
        "⏳ Admin tekshirmoqda...\n"
        "Tasdiqlangandan so'ng platformaga kirish beriladi!\n\n"
        "_Odatda 5-15 daqiqa ichida tasdiqlash amalga oshiriladi._",
        parse_mode="Markdown"
    )

    # Admin ga xabar
    method_name = {"payme":"🟢 Payme","click":"🔵 Click","card":"💳 Karta"}.get(method, method)
    plan_name = PLAN_NAMES.get(user.get("plan_key","standard"), "") if user else ""

    admin_text = (
        f"💰 *YANGI TO'LOV CHEKI*\n\n"
        f"👤 {user['full_name'] if user else 'Noma\'lum'}\n"
        f"📱 {user['phone'] if user else '-'}\n"
        f"⚖️ {user['weight'] if user else '-'} kg\n"
        f"🥗 Ratsion: {plan_name}\n"
        f"💳 Usul: {method_name}\n"
        f"💰 Summa: *{PRICE_30_DAY:,} so'm*\n"
        f"🆔 To'lov ID: #{pay_id}\n"
        f"👤 TG: @{user['username'] or 'yo\'q'} | ID: {msg.from_user.id}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await msg.bot.send_photo(
                admin_id,
                photo=file_id,
                caption=admin_text,
                reply_markup=payment_confirm_kb(pay_id, msg.from_user.id),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Admin ga xabar yuborilmadi: {e}")

# ══════════════════════════════════
# ADMIN: PAYMENT CONFIRM / REJECT
# ══════════════════════════════════
@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm_payment(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Ruxsat yo'q!"); return

    _, pay_id, uid = call.data.split(":")
    pay_id, uid = int(pay_id), int(uid)

    user = await get_user(uid)
    if not user:
        await call.answer("❌ Foydalanuvchi topilmadi!"); return

    plan_key = user.get("plan_key", "standard")
    plan = await get_nutrition_plan(plan_key)

    # Premium berish + challenge boshlash
    await update_user(uid, is_premium=1, challenge_day=1,
                      challenge_started=datetime.now().isoformat())
    await update_payment(pay_id, status="confirmed",
                         confirmed_at=datetime.now().isoformat())

    await call.message.edit_caption(
        call.message.caption + "\n\n✅ *TASDIQLANDI!*",
        parse_mode="Markdown"
    )
    await call.answer("✅ Tasdiqlandi!")

    # Foydalanuvchiga xabar
    plan_name = PLAN_NAMES.get(plan_key, "")
    meals_list = ""
    if plan and plan.get("meals"):
        for m in plan["meals"].split("|"):
            meals_list += f"• {m.strip()}\n"

    await call.bot.send_message(
        uid,
        f"🎉 *TABRIKLAYMIZ!*\n\n"
        f"✅ To'lovingiz tasdiqlandi!\n"
        f"🔥 30-kunlik challendj boshlandi!\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🥗 *SIZNING RATSIONINGIZ:*\n"
        f"*{plan_name}*\n\n"
        f"📊 Kaloriya: {plan['cal_range'] if plan else '-'} kkal\n"
        f"💪 Oqsil: {plan['protein'] if plan else '-'}\n"
        f"🌾 Uglevod: {plan['carb'] if plan else '-'}\n"
        f"🫒 Yog': {plan['fat'] if plan else '-'}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🍽️ *Kunlik menyu:*\n{meals_list}\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"Pastdagi menyudan boshlang! 💪",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject_payment(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Ruxsat yo'q!"); return

    _, pay_id, uid = call.data.split(":")
    pay_id, uid = int(pay_id), int(uid)

    await update_payment(int(pay_id), status="rejected")
    await call.message.edit_caption(
        call.message.caption + "\n\n❌ *RAD ETILDI*", parse_mode="Markdown"
    )
    await call.answer("❌ Rad etildi")

    await call.bot.send_message(
        int(uid),
        "❌ *To'lovingiz tasdiqlanmadi.*\n\n"
        "Muammo bo'lsa @QaytaTugulishBot ga murojaat qiling.\n\n"
        "Qayta to'lov qilish uchun /start bosing.",
        parse_mode="Markdown"
    )

# ══════════════════════════════════
# MAIN MENU HANDLERS
# ══════════════════════════════════
async def check_premium(msg: Message) -> bool:
    user = await get_user(msg.from_user.id)
    if not user or not user.get("is_premium"):
        await msg.answer(
            "🔒 *Bu bo'lim faqat premium foydalanuvchilar uchun!*\n\n"
            "To'lov qilib kirish olish uchun /start bosing.",
            parse_mode="Markdown"
        )
        return False
    return True

@router.message(F.text == "🔥 30-Kunlik Challendj")
async def challenge_main(msg: Message):
    if not await check_premium(msg): return
    user = await get_user(msg.from_user.id)
    completed = await get_completed_days(msg.from_user.id)
    current = user.get("challenge_day", 1)

    await msg.answer(
        f"🔥 *30-KUNLIK CHALLENDJ*\n\n"
        f"📊 {progress_bar(len(completed))}\n"
        f"✅ Bajarildi: *{len(completed)}* kun\n"
        f"⏳ Qoldi: *{30-len(completed)}* kun\n"
        f"📅 Joriy kun: *{current}-kun*\n\n"
        f"Kunni tanlang 👇",
        reply_markup=challenge_kb(completed, current),
        parse_mode="Markdown"
    )

@router.message(F.text == "🥗 Mening Ratsionim")
async def my_nutrition(msg: Message):
    if not await check_premium(msg): return
    user = await get_user(msg.from_user.id)
    plan_key = user.get("plan_key", "standard")
    plan = await get_nutrition_plan(plan_key)

    if not plan:
        await msg.answer("Ratsion topilmadi. Admin bilan bog'laning."); return

    meals_list = ""
    if plan.get("meals"):
        for m in plan["meals"].split("|"):
            meals_list += f"• {m.strip()}\n"

    await msg.answer(
        f"🥗 *SIZNING RATSIONINGIZ*\n\n"
        f"📋 *{plan['title']}*\n\n"
        f"📊 Kaloriya: *{plan['cal_range']}* kkal/kun\n"
        f"💪 Oqsil: *{plan['protein']}*\n"
        f"🌾 Uglevod: *{plan['carb']}*\n"
        f"🫒 Yog': *{plan['fat']}*\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📝 *Tavsif:*\n_{plan['description']}_\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🍽️ *Kunlik menyu:*\n{meals_list}" + get_watermark(),
        parse_mode="Markdown",
        protect_content=True
    )

@router.message(F.text == "💧 Suv Tracker")
async def water_main(msg: Message):
    if not await check_premium(msg): return
    water = await get_today_water(msg.from_user.id)
    user = await get_user(msg.from_user.id)
    goal = user.get("water_goal", 3000) if user else 3000
    await msg.answer(
        f"💧 *BUGUNGI SUV TRACKER*\n\n"
        f"{wbar(water, goal)}\n\n"
        f"✅ Ichildi: *{water}ml*\n"
        f"⏳ Qoldi: *{max(0,goal-water)}ml*\n\n"
        f"Qancha qo'shish kerak?",
        reply_markup=water_kb(), parse_mode="Markdown"
    )

@router.message(F.text == "🏋️ Mashqlar")
async def workouts_main(msg: Message):
    if not await check_premium(msg): return
    await msg.answer(
        "💪 *MASHQLAR*\n\n"
        "30-kunlik challendj ichida har kuni mashqlar ko'rsatiladi.\n\n"
        "🔥 Challendj menyusiga o'ting!",
        parse_mode="Markdown"
    )

@router.message(F.text == "📊 Statistika")
async def stats_main(msg: Message):
    user = await get_user(msg.from_user.id)
    if not user: return
    completed = await get_completed_days(msg.from_user.id)
    water = await get_today_water(msg.from_user.id)
    plan = PLAN_NAMES.get(user.get("plan_key","standard"), "")

    await msg.answer(
        f"📊 *MENING STATISTIKAM*\n\n"
        f"👤 {user['full_name']}\n"
        f"⚖️ {user['weight']} kg | 📏 {user['height']} sm\n"
        f"🥗 Ratsion: {plan}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🏆 Bajarilgan kunlar: *{len(completed)}/30*\n"
        f"📊 {progress_bar(len(completed))}\n"
        f"💧 Bugungi suv: *{water}ml*\n"
        f"👑 Premium: *{'Ha ✅' if user.get('is_premium') else 'Yo\'q ❌'}*",
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 Profilim")
async def profile_main(msg: Message):
    user = await get_user(msg.from_user.id)
    if not user: return
    bmi = user["weight"]/((user["height"]/100)**2) if user.get("height") else 0
    bt = ("🔵 Kam" if bmi<18.5 else "🟢 Ideal" if bmi<25 else "🟡 Ortiqcha" if bmi<30 else "🔴 Semiz")
    gender_e = "👨 Erkak" if user.get("gender")=="erkak" else "👩 Ayol"
    plan = PLAN_NAMES.get(user.get("plan_key","standard"), "")
    await msg.answer(
        f"👤 *MENING PROFILIM*\n\n"
        f"📛 *{user['full_name']}*\n"
        f"{gender_e}\n"
        f"📱 {user.get('phone','-')}\n"
        f"📏 {user.get('height',0)} sm | ⚖️ {user.get('weight',0)} kg\n"
        f"📊 BMI: {bmi:.1f} — {bt}\n"
        f"🥗 Ratsion: {plan}\n"
        f"👑 Premium: {'Ha ✅' if user.get('is_premium') else 'Yo\'q ❌'}",
        parse_mode="Markdown"
    )

@router.message(F.text == "⚙️ Sozlamalar")
async def settings_main(msg: Message):
    await msg.answer("⚙️ *SOZLAMALAR*", reply_markup=settings_kb(), parse_mode="Markdown")

# ══════════════════════════════════
# CHALLENGE CALLBACKS
# ══════════════════════════════════
@router.callback_query(F.data == "challenge_main")
async def cb_challenge_main(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    completed = await get_completed_days(call.from_user.id)
    current = user.get("challenge_day",1) if user else 1
    await call.message.edit_text(
        f"🔥 *30-KUNLIK CHALLENDJ*\n\n"
        f"📊 {progress_bar(len(completed))}\n"
        f"✅ Bajarildi: *{len(completed)}* | ⏳ Qoldi: *{30-len(completed)}*\n\n"
        f"Kunni tanlang 👇",
        reply_markup=challenge_kb(completed, current), parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data.startswith("day:"))
async def cb_day(call: CallbackQuery):
    day = int(call.data.split(":")[1])
    completed = await get_completed_days(call.from_user.id)
    is_done = day in completed
    meals = get_day_meals(day)
    exercises = get_day_exercises(day)
    logged_m = await get_logged_meals(call.from_user.id, day)
    logged_e = await get_logged_exercises(call.from_user.id, day)
    water = await get_today_water(call.from_user.id)

    await call.message.edit_text(
        f"📅 *{day}-KUN* {'✅' if is_done else ''}\n\n"
        f"_{get_motivation(day)}_\n\n"
        f"💡 _{get_day_tip(day)}_\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💧 Suv: {wbar(water,3000)}\n"
        f"🍽️ Ovqat: *{len(logged_m)}/{len(meals)}* | 💪 Mashq: *{len(logged_e)}/{len(exercises)}*\n"
        f"━━━━━━━━━━━━━━━━━",
        reply_markup=day_detail_kb(day), parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data.startswith("complete:"))
async def cb_complete(call: CallbackQuery):
    day = int(call.data.split(":")[1])
    newly = await complete_day(call.from_user.id, day)
    if newly:
        await call.answer(f"🎉 {day}-kun bajarildi!", show_alert=True)
        completed = await get_completed_days(call.from_user.id)
        user = await get_user(call.from_user.id)
        await call.message.edit_text(
            f"🔥 *30-KUNLIK CHALLENDJ*\n\n"
            f"📊 {progress_bar(len(completed))}\n"
            f"Kunni tanlang 👇",
            reply_markup=challenge_kb(completed, user.get("challenge_day",1) if user else 1),
            parse_mode="Markdown"
        )
    else:
        await call.answer("Bu kun allaqachon bajarilgan! ✅")

# ══════════════════════════════════
# MEALS CALLBACKS
# ══════════════════════════════════
@router.callback_query(F.data.startswith("meals:"))
async def cb_meals(call: CallbackQuery):
    day = int(call.data.split(":")[1])
    meals = get_day_meals(day)
    logged = await get_logged_meals(call.from_user.id, day)
    await call.message.edit_text(
        f"🍽️ *{day}-KUN OVQATLARI*\n✅ = Iste'mol qilindi",
        reply_markup=meals_kb(day, meals, logged), parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data.startswith("meal_detail:"))
async def cb_meal_detail(call: CallbackQuery):
    _, day, idx = call.data.split(":")
    day, idx = int(day), int(idx)
    meals = get_day_meals(day)
    meal = meals[idx]
    logged = await get_logged_meals(call.from_user.id, day)
    is_logged = idx in logged
    photo_id = await get_meal_photo(day, idx)

    text = (
        f"{meal['icon']} *{meal['name']}* — {meal['time']}\n\n"
        f"🔥 {meal['cal']} kkal | 💪 {meal['protein']}g oqsil\n\n"
        f"━━━━━━━━━━━━━━━━━\n🛒 *MAHSULOTLAR:*\n"
    )
    for f in meal["foods"]: text += f"• {f}\n"
    text += f"\n━━━━━━━━━━━━━━━━━\n👨‍🍳 *TAYYORLASH:*\n\n{meal['recipe']}"
    kb = meal_detail_kb(day, idx, is_logged)

    text_protected = wprotect(text)
    if photo_id:
        try:
            await call.message.delete()
            await call.bot.send_photo(
                call.message.chat.id, photo=photo_id,
                caption=text_protected, reply_markup=kb,
                parse_mode="Markdown",
                protect_content=True
            )
        except Exception:
            await call.message.answer(
                text_protected, reply_markup=kb,
                parse_mode="Markdown",
                protect_content=True
            )
    else:
        try:
            await call.message.edit_text(
                text_protected, reply_markup=kb, parse_mode="Markdown"
            )
        except Exception:
            await call.message.answer(
                text_protected, reply_markup=kb,
                parse_mode="Markdown",
                protect_content=True
            )
    await call.answer()

@router.callback_query(F.data.startswith("meal_toggle:"))
async def cb_meal_toggle(call: CallbackQuery):
    _, day, idx = call.data.split(":")
    day, idx = int(day), int(idx)
    logged_now = await log_meal(call.from_user.id, day, idx)
    await call.answer("✅ Qayd etildi!" if logged_now else "↩️ Bekor qilindi")
    logged = await get_logged_meals(call.from_user.id, day)
    meals = get_day_meals(day)
    meal = meals[idx]
    text = (
        f"{meal['icon']} *{meal['name']}* — {meal['time']}\n\n"
        f"🔥 {meal['cal']} kkal | 💪 {meal['protein']}g oqsil\n\n"
        f"━━━━━━━━━━━━━━━━━\n🛒 *MAHSULOTLAR:*\n"
    )
    for f in meal["foods"]: text += f"• {f}\n"
    text += f"\n━━━━━━━━━━━━━━━━━\n👨‍🍳 *TAYYORLASH:*\n\n{meal['recipe']}"
    try:
        await call.message.edit_text(text, reply_markup=meal_detail_kb(day,idx,idx in logged),
                                      parse_mode="Markdown")
    except Exception: pass

# ══════════════════════════════════
# EXERCISE CALLBACKS
# ══════════════════════════════════
@router.callback_query(F.data.startswith("exercises:"))
async def cb_exercises(call: CallbackQuery):
    day = int(call.data.split(":")[1])
    exs = get_day_exercises(day)
    logged = await get_logged_exercises(call.from_user.id, day)
    await call.message.edit_text(
        f"💪 *{day}-KUN MASHQLARI*\n✅ = Bajarildi",
        reply_markup=exercises_kb(day, exs, logged), parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data.startswith("ex_detail:"))
async def cb_ex_detail(call: CallbackQuery):
    _, day, idx = call.data.split(":")
    day, idx = int(day), int(idx)
    exs = get_day_exercises(day)
    ex = exs[idx]
    logged = await get_logged_exercises(call.from_user.id, day)
    is_logged = idx in logged
    ex_key = f"set{(day-1)%3}_ex{idx}"
    video = await get_exercise_video(ex_key)

    text = (
        f"{ex['icon']} *{ex['name']}*\n\n"
        f"🎯 *{ex['muscle']}*\n"
        f"📊 {ex['sets']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📝 *TEXNIKA:*\n\n{ex['desc']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{'✅ BAJARILDI!' if is_logged else '⭕ Bajarilmagan'}"
    )
    kb = exercise_detail_kb(day, idx, is_logged)

    text_protected = wprotect(text)
    wtext = wprotect(text)
    if video:
        try:
            await call.message.delete()
        except Exception:
            pass
        if video["type"] == "video_note":
            await call.bot.send_video_note(
                call.message.chat.id,
                video_note=video["file_id"],
                protect_content=True
            )
        else:
            await call.bot.send_video(
                call.message.chat.id,
                video=video["file_id"],
                caption=f"{ex['icon']} *{ex['name']}* — Texnika",
                parse_mode="Markdown",
                protect_content=True
            )
        await call.bot.send_message(
            call.message.chat.id,
            text_protected,
            reply_markup=kb,
            parse_mode="Markdown",
            protect_content=True
        )
    else:
        try:
            await call.message.edit_text(
                text_protected, reply_markup=kb, parse_mode="Markdown"
            )
        except Exception:
            await call.message.answer(
                text_protected, reply_markup=kb,
                parse_mode="Markdown",
                protect_content=True
            )
    await call.answer()  # ex_detail end

@router.callback_query(F.data.startswith("ex_toggle:"))
async def cb_ex_toggle(call: CallbackQuery):
    _, day, idx = call.data.split(":")
    day, idx = int(day), int(idx)
    logged_now = await log_exercise(call.from_user.id, day, idx)
    await call.answer("✅ Bajarildi!" if logged_now else "↩️ Bekor qilindi")
    exs = get_day_exercises(day)
    ex = exs[idx]
    logged = await get_logged_exercises(call.from_user.id, day)
    text = (
        f"{ex['icon']} *{ex['name']}*\n\n"
        f"🎯 *{ex['muscle']}*\n📊 {ex['sets']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n📝 *TEXNIKA:*\n\n{ex['desc']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n{'✅ BAJARILDI!' if idx in logged else '⭕ Bajarilmagan'}"
    )
    try:
        await call.message.edit_text(text,
                                      reply_markup=exercise_detail_kb(day,idx,idx in logged),
                                      parse_mode="Markdown")
    except Exception: pass

# ══════════════════════════════════
# WATER CALLBACKS
# ══════════════════════════════════
@router.callback_query(F.data.startswith("water:"))
async def cb_water(call: CallbackQuery):
    amount = int(call.data.split(":")[1])
    user = await get_user(call.from_user.id)
    goal = user.get("water_goal", 3000) if user else 3000
    total = await add_water(call.from_user.id, amount)
    await call.answer(f"💧 +{amount}ml!")
    await call.message.edit_text(
        f"💧 *SUV TRACKER*\n\n{wbar(total,goal)}\n\n"
        f"✅ *{total}ml* / {goal}ml\n"
        f"{'🎉 Maqsad bajarildi!' if total>=goal else f'Qoldi: {goal-total}ml'}",
        reply_markup=water_kb(), parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("water_day:"))
async def cb_water_day(call: CallbackQuery):
    water = await get_today_water(call.from_user.id)
    await call.message.edit_text(
        f"💧 *SUV TRACKER*\n\n{wbar(water,3000)}\n\n"
        f"Qo'shish uchun tugmani bosing:",
        reply_markup=water_kb(), parse_mode="Markdown"
    )
    await call.answer()

# ══════════════════════════════════
# ADMIN
# ══════════════════════════════════
@router.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!"); return
    total = await get_users_count()
    premium = await get_premium_count()
    payments = await get_pending_payments()
    await msg.answer(
        f"👑 *ADMIN PANEL*\n\n"
        f"👥 Jami: *{total}* | 👑 Premium: *{premium}*\n"
        f"⏳ Kutayotgan to'lovlar: *{len(payments)}*",
        reply_markup=admin_kb(), parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin:payments")
async def admin_payments(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌"); return
    payments = await get_pending_payments()
    if not payments:
        await call.answer("Kutayotgan to'lov yo'q ✅", show_alert=True); return
    await call.answer(f"{len(payments)} ta kutayotgan to'lov")

@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    await call.message.edit_text("📨 Yuboriladigan xabarni yozing (Markdown):")
    await state.set_state(AdminSt.broadcast)
    await call.answer()

@router.message(AdminSt.broadcast)
async def admin_broadcast_send(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    await state.clear()
    users = await get_all_users()
    sent = 0
    for u in users:
        try:
            await msg.bot.send_message(u["telegram_id"],
                f"📢 *TRENER XABARI:*\n\n{msg.text}", parse_mode="Markdown")
            sent += 1
        except Exception: pass
    await msg.answer(f"✅ Yuborildi: *{sent}/{len(users)}*", parse_mode="Markdown",
                     reply_markup=admin_kb())

@router.callback_query(F.data == "admin:welcome_video")
async def admin_welcome_video(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    await call.message.edit_text(
        "🎥 *SALOMLASHUV VIDEOSI*\n\n"
        "Yangi foydalanuvchilarga ko'rsatiladigan videoni yuboring:"
    )
    await state.set_state(AdminSt.welcome_vid)
    await call.answer()

@router.message(AdminSt.welcome_vid, F.video)
async def admin_welcome_video_save(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS: return
    await save_bot_media("welcome_video", msg.video.file_id, "video")
    await state.clear()
    await msg.answer("✅ Salomlashuv videosi saqlandi!", reply_markup=admin_kb())

@router.callback_query(F.data == "admin:edit_nutrition")
async def admin_edit_nutrition(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    plans = await get_all_nutrition_plans()
    await call.message.edit_text(
        "🥗 *RATSION REJALARI*\n\nQaysi rejani tahrirlash?",
        reply_markup=nutrition_plans_kb(plans), parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data.startswith("edit_plan:"))
async def admin_edit_plan(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    plan_key = call.data.split(":")[1]
    plan = await get_nutrition_plan(plan_key)
    await state.update_data(edit_plan_key=plan_key)
    await call.message.edit_text(
        f"🥗 *{plan['title']}*\n\n"
        f"📊 Kaloriya: {plan['cal_range']}\n"
        f"💪 Oqsil: {plan['protein']}\n"
        f"🌾 Uglevod: {plan['carb']}\n"
        f"🫒 Yog': {plan['fat']}\n"
        f"📝 Tavsif: {plan['description'][:50]}...\n"
        f"🍽️ Menyu: {plan['meals'][:80]}...\n\n"
        f"Qaysi maydonni o'zgartirish kerak?\n"
        f"(cal_range / protein / carb / fat / description / meals)\n\n"
        f"Maydon nomini yozing:",
        parse_mode="Markdown"
    )
    await state.set_state(AdminSt.edit_plan_field)
    await call.answer()

@router.message(AdminSt.edit_plan_field)
async def admin_edit_plan_field(msg: Message, state: FSMContext):
    field = msg.text.strip().lower()
    valid = ["cal_range","protein","carb","fat","description","meals"]
    if field not in valid:
        await msg.answer(f"❌ Noto'g'ri. Quyidagilardan birini yozing:\n{', '.join(valid)}")
        return
    await state.update_data(edit_field=field)
    await msg.answer(f"✅ '{field}' maydoni uchun yangi qiymat yozing:")
    await state.set_state(AdminSt.edit_plan_value)

@router.message(AdminSt.edit_plan_value)
async def admin_edit_plan_value(msg: Message, state: FSMContext):
    data = await state.get_data()
    await update_nutrition_plan(data["edit_plan_key"], **{data["edit_field"]: msg.text.strip()})
    await state.clear()
    await msg.answer(f"✅ Yangilandi!", reply_markup=admin_kb())

@router.callback_query(F.data == "admin:stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    total = await get_users_count()
    premium = await get_premium_count()
    await call.message.edit_text(
        f"📊 *BOT STATISTIKASI*\n\n"
        f"👥 Jami: *{total}*\n"
        f"👑 Premium: *{premium}*\n"
        f"🆓 Oddiy: *{total-premium}*\n"
        f"💰 Daromad: *{premium * PRICE_30_DAY:,} so'm*",
        reply_markup=back_kb("admin_main"), parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data == "admin:give_premium")
async def admin_give_premium(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    await call.message.edit_text("✅ Foydalanuvchi Telegram ID sini yozing:")
    await state.set_state(AdminSt.premium_id)
    await call.answer()

@router.message(AdminSt.premium_id)
async def admin_give_premium_id(msg: Message, state: FSMContext):
    try:
        uid = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Noto'g'ri ID"); return
    user = await get_user(uid)
    if not user:
        await msg.answer("❌ Foydalanuvchi topilmadi!"); await state.clear(); return
    await update_user(uid, is_premium=1, challenge_day=1,
                      challenge_started=datetime.now().isoformat())
    await state.clear()
    await msg.answer(f"✅ *{user['full_name']}* ga premium berildi!", parse_mode="Markdown",
                     reply_markup=admin_kb())
    try:
        await msg.bot.send_message(uid,
            "🎉 *Tabriklaymiz! Sizga Premium berildi!*\n\n"
            "30-kunlik challendj boshlandi! 🔥",
            reply_markup=main_menu_kb(), parse_mode="Markdown")
    except Exception: pass

@router.callback_query(F.data == "admin:upload_photo")
async def admin_upload_photo(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    await call.message.edit_text("📸 Qaysi kun? (1-30)")
    await state.set_state(AdminSt.photo_day); await call.answer()

@router.message(AdminSt.photo_day)
async def admin_photo_day(msg: Message, state: FSMContext):
    try:
        day = int(msg.text); assert 1<=day<=30
    except Exception:
        await msg.answer("❌ 1-30 kiriting:"); return
    await state.update_data(photo_day=day)
    meals = get_day_meals(day)
    lst = "\n".join([f"{i+1}. {m['icon']} {m['name']}" for i,m in enumerate(meals)])
    await msg.answer(f"Qaysi ovqat? (raqam)\n{lst}")
    await state.set_state(AdminSt.photo_meal)

@router.message(AdminSt.photo_meal)
async def admin_photo_meal(msg: Message, state: FSMContext):
    data = await state.get_data()
    meals = get_day_meals(data["photo_day"])
    try:
        idx = int(msg.text)-1; assert 0<=idx<len(meals)
    except Exception:
        await msg.answer(f"❌ 1-{len(meals)} kiriting:"); return
    await state.update_data(photo_meal=idx)
    await msg.answer(f"✅ {meals[idx]['name']} | Rasmni yuboring:")
    await state.set_state(AdminSt.photo_file)

@router.message(AdminSt.photo_file, F.photo)
async def admin_photo_file(msg: Message, state: FSMContext):
    data = await state.get_data()
    await save_meal_photo(data["photo_day"], data["photo_meal"], msg.photo[-1].file_id)
    await state.clear()
    await msg.answer("✅ Rasm saqlandi!", reply_markup=admin_kb())

@router.callback_query(F.data == "admin:upload_video")
async def admin_upload_video(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    await call.message.edit_text(
        "🎬 Qaysi SET? (1/2/3)\n"
        "1️⃣ Oyoq | 2️⃣ Ko'krak | 3️⃣ Orqa"
    )
    await state.set_state(AdminSt.video_set); await call.answer()

@router.message(AdminSt.video_set)
async def admin_video_set(msg: Message, state: FSMContext):
    from data.meals_data import EXERCISE_SETS
    try:
        s = int(msg.text)-1; assert 0<=s<=2
    except Exception:
        await msg.answer("❌ 1, 2 yoki 3 kiriting:"); return
    await state.update_data(video_set=s)
    exs = EXERCISE_SETS[s]
    lst = "\n".join([f"{i+1}. {e['icon']} {e['name']}" for i,e in enumerate(exs)])
    await msg.answer(f"Qaysi mashq?\n{lst}")
    await state.set_state(AdminSt.video_index)

@router.message(AdminSt.video_index)
async def admin_video_index(msg: Message, state: FSMContext):
    from data.meals_data import EXERCISE_SETS
    data = await state.get_data()
    exs = EXERCISE_SETS[data["video_set"]]
    try:
        idx = int(msg.text)-1; assert 0<=idx<len(exs)
    except Exception:
        await msg.answer(f"❌ 1-{len(exs)} kiriting:"); return
    ex_key = f"set{data['video_set']}_ex{idx}"
    await state.update_data(video_index=idx, video_key=ex_key)
    await msg.answer(f"✅ {exs[idx]['name']} | Video turini tanlang:",
                     reply_markup=video_type_kb(ex_key))
    await state.set_state(AdminSt.video_type)

@router.callback_query(F.data.startswith("vtype:"))
async def admin_video_type(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    _, vtype, ex_key = call.data.split(":", 2)
    await state.update_data(video_type=vtype, video_key=ex_key)
    t = "⭕ Aylana video" if vtype=="video_note" else "📹 Oddiy video"
    await call.message.edit_text(f"✅ {t} tanlandi\n\n📹 Videoni yuboring:")
    await state.set_state(AdminSt.video_file); await call.answer()

@router.message(AdminSt.video_file, F.video_note)
async def admin_video_note(msg: Message, state: FSMContext):
    data = await state.get_data()
    await save_exercise_video(data.get("video_key",""), msg.video_note.file_id, "video_note")
    await state.clear()
    await msg.answer("✅ Aylana video saqlandi! ⭕", reply_markup=admin_kb())

@router.message(AdminSt.video_file, F.video)
async def admin_video_file(msg: Message, state: FSMContext):
    data = await state.get_data()
    await save_exercise_video(data.get("video_key",""), msg.video.file_id, "video")
    await state.clear()
    await msg.answer("✅ Video saqlandi! 📹", reply_markup=admin_kb())

@router.callback_query(F.data == "admin_main")
async def cb_admin_main(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    total = await get_users_count()
    premium = await get_premium_count()
    payments = await get_pending_payments()
    await call.message.edit_text(
        f"👑 *ADMIN PANEL*\n\n👥 {total} | 👑 {premium} | ⏳ {len(payments)} kutmoqda",
        reply_markup=admin_kb(), parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data == "admin:users")
async def admin_users(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    users = await get_all_users()
    premium = [u for u in users if u.get("is_premium")]
    await call.message.edit_text(
        f"👥 *FOYDALANUVCHILAR*\n\n"
        f"Jami: *{len(users)}*\n"
        f"Premium: *{len(premium)}*\n\n"
        f"So'nggi 5 ta:\n" +
        "\n".join([f"• {u['full_name']} — {u['weight']}kg {'👑' if u.get('is_premium') else ''}"
                   for u in users[-5:]]),
        reply_markup=back_kb("admin_main"), parse_mode="Markdown"
    )
    await call.answer()

# ══════════════════════════════════════════════════════
# REGION — Ro'yxatdan o'tishga qo'shish
# ══════════════════════════════════════════════════════
# Reg state ga region qo'shamiz
class RegUpdated(StatesGroup):
    region = State()

# gender callback ni yangilaymiz — region so'raydi
# (handlers.py dagi reg_gender ni o'zgartirish o'rniga yangi handler)
@router.callback_query(F.data.startswith("gender:"))
async def reg_gender_v2(call: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state != Reg.gender.state:
        return  # faqat reg jarayonida ishlaydi

    from keyboards.keyboards import region_kb as rkb
    gender = call.data.split(":")[1]
    await state.update_data(gender=gender)
    g = "👨 Erkak" if gender == "erkak" else "👩 Ayol"
    await call.message.edit_reply_markup()
    await call.message.answer(
        f"✅ {g} tanlandi!\n\n"
        f"📍 *Qaysi viloyatda yashaysiz?*\n"
        f"Quyidan tanlang 👇",
        reply_markup=rkb(),
        parse_mode="Markdown"
    )
    await state.set_state(RegUpdated.region)
    await call.answer()

@router.message(RegUpdated.region)
async def reg_region(msg: Message, state: FSMContext):
    from keyboards.keyboards import UZBEKISTAN_REGIONS, challenge_info_kb
    from config import get_plan_by_weight, PLAN_NAMES, PRICE_30_DAY

    region = msg.text.strip()
    if region not in UZBEKISTAN_REGIONS:
        await msg.answer("❌ Ro'yxatdan tanlang:", reply_markup=__import__('keyboards.keyboards', fromlist=['region_kb']).region_kb())
        return

    data = await state.get_data()
    await state.clear()

    w = data.get("weight", 80)
    h = data.get("height", 175)
    gender = data.get("gender", "erkak")
    bmi = w / ((h/100)**2)
    plan_key = get_plan_by_weight(w)
    plan_name = PLAN_NAMES[plan_key]
    bmi_text = ("🔵 Kam" if bmi<18.5 else "🟢 Ideal" if bmi<25 else "🟡 Ortiqcha" if bmi<30 else "🔴 Semiz")
    gender_emoji = "👨" if gender == "erkak" else "👩"

    await update_user(
        msg.from_user.id,
        full_name=data.get("name",""),
        phone=data.get("phone",""),
        weight=w, height=h,
        gender=gender, region=region,
        plan_key=plan_key,
        registered_at=datetime.now().isoformat()
    )

    await msg.answer(
        f"✅ *Ro'yxatdan o'tdingiz!*\n\n"
        f"{gender_emoji} *{data.get('name','')}*\n"
        f"📱 {data.get('phone','')}\n"
        f"📍 {region}\n"
        f"📏 {h} sm | ⚖️ {w} kg\n"
        f"📊 BMI: {bmi:.1f} — {bmi_text}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🥗 *Sizning ratsioningiz:*\n{plan_name}\n\n"
        f"_To'lovdan so'ng avtomatik ochiladi!_",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

    await msg.answer(
        f"🔥 *30-KUNLIK CHALLENDJ*\n\n"
        f"✅ Har kuni ovqat retsepti + rasm\n"
        f"✅ Har kuni mashq + video\n"
        f"✅ Suv va kaloriya tracker\n"
        f"✅ Vazningizga mos ratsion\n"
        f"✅ Kunlik eslatmalar\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 *Narx: {PRICE_30_DAY:,} so'm*\n\n"
        f"Boshlashga tayyormisiz? 👇",
        reply_markup=challenge_info_kb(),
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════════════════
# /users — ADMIN FOYDALANUVCHILAR RO'YXATI
# ══════════════════════════════════════════════════════
@router.message(Command("users"))
async def cmd_users(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!")
        return

    from keyboards.keyboards import export_kb
    from database.db import get_all_users_detailed, get_users_by_region

    users = await get_all_users_detailed()
    total = len(users)
    premium = sum(1 for u in users if u.get("is_premium"))
    regions = await get_users_by_region()

    region_text = ""
    for reg, cnt in list(regions.items())[:8]:
        region_text += f"  📍 {reg}: *{cnt}* ta\n"

    await msg.answer(
        f"👥 *FOYDALANUVCHILAR BAZASI*\n\n"
        f"📊 Jami: *{total}* ta\n"
        f"👑 Premium: *{premium}* ta\n"
        f"🆓 Oddiy: *{total-premium}* ta\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📍 *VILOYATLAR BO'YICHA:*\n"
        f"{region_text}\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📤 Ma'lumotlarni yuklab olish:",
        reply_markup=export_kb(),
        parse_mode="Markdown"
    )

    # So'nggi 10 ta foydalanuvchi
    recent = users[:10]
    if recent:
        lines = []
        for i, u in enumerate(recent, 1):
            prem = "👑" if u.get("is_premium") else "🆓"
            lines.append(
                f"{i}. {prem} *{u['full_name']}*\n"
                f"   📍 {u.get('region','?')} | ⚖️ {u.get('weight','?')}kg\n"
                f"   📱 {u.get('phone','?')}\n"
                f"   📅 {str(u.get('created_at',''))[:10]}"
            )
        await msg.answer(
            f"📋 *SO'NGGI 10 TA FOYDALANUVCHI:*\n\n" + "\n\n".join(lines),
            parse_mode="Markdown"
        )

# Export handlers
@router.callback_query(F.data.startswith("export:"))
async def cb_export(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌"); return

    from database.db import get_all_users_detailed
    import io

    fmt = call.data.split(":")[1]
    users = await get_all_users_detailed()
    await call.answer("⏳ Tayyorlanmoqda...")

    if fmt == "csv":
        lines = ["ID,Ism,Telefon,Viloyat,Vazn,Boy,Jins,Plan,Premium,Kun,Sana"]
        for u in users:
            lines.append(
                f"{u['telegram_id']},"
                f"{u.get('full_name','').replace(',','')},"
                f"{u.get('phone','')},"
                f"{u.get('region','').replace(',','')},"
                f"{u.get('weight','')},"
                f"{u.get('height','')},"
                f"{u.get('gender','')},"
                f"{u.get('plan_key','')},"
                f"{'Ha' if u.get('is_premium') else 'Yoq'},"
                f"{u.get('challenge_day',0)},"
                f"{str(u.get('created_at',''))[:10]}"
            )
        content = "\n".join(lines)
        filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        doc = io.BytesIO(content.encode('utf-8-sig'))
        doc.name = filename
        await call.message.answer_document(
            document=doc,
            caption=f"📊 CSV — {len(users)} ta foydalanuvchi"
        )
    else:
        # TXT format
        lines = ["="*40, "QAYTA TUGILISH - FOYDALANUVCHILAR",
                f"Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                f"Jami: {len(users)} ta", "="*40, ""]
        for idx, u in enumerate(users, 1):
            name = str(u.get("full_name","Noma'lum"))
            phone = str(u.get("phone","-"))
            region = str(u.get("region","-"))
            weight = str(u.get("weight","-"))
            height = str(u.get("height","-"))
            gender = str(u.get("gender","-"))
            plan = str(u.get("plan_key","-"))
            prem = "Ha" if u.get("is_premium") else "Yoq"
            date = str(u.get("created_at",""))[:10]
            entry = (
                f"{idx}. {name}\n"
                f"   Tel: {phone}\n"
                f"   Viloyat: {region}\n"
                f"   Vazn: {weight} kg\n"
                f"   Boy: {height} sm\n"
                f"   Jins: {gender}\n"
                f"   Plan: {plan}\n"
                f"   Premium: {prem}\n"
                f"   Sana: {date}\n"
                f"   {chr(45)*30}"
            )
            lines.append(entry)
        doc = io.BytesIO(content.encode('utf-8'))
        doc.name = filename
        await call.message.answer_document(
            document=doc,
            caption=f"📄 TXT — {len(users)} ta foydalanuvchi"
        )

# ══════════════════════════════════════════════════════
# /broadcast — KUCHLI BROADCAST
# ══════════════════════════════════════════════════════
class BroadcastSt(StatesGroup):
    target   = State()
    region   = State()
    text     = State()
    confirm  = State()

@router.message(Command("broadcast"))
async def cmd_broadcast(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!")
        return

    from keyboards.keyboards import broadcast_target_kb
    await msg.answer(
        "📨 *BROADCAST XABAR*\n\n"
        "Kimga yubormoqchisiz?",
        reply_markup=broadcast_target_kb(),
        parse_mode="Markdown"
    )
    await state.set_state(BroadcastSt.target)

@router.callback_query(BroadcastSt.target, F.data.startswith("bc_target:"))
async def bc_target(call: CallbackQuery, state: FSMContext):
    target = call.data.split(":")[1]
    await state.update_data(target=target)

    if target == "region":
        from keyboards.keyboards import broadcast_regions_kb
        await call.message.edit_text(
            "📍 Qaysi viloyat?",
            reply_markup=broadcast_regions_kb()
        )
        await state.set_state(BroadcastSt.region)
    else:
        from database.db import get_users_by_filter
        if target == "premium":
            users = await get_users_by_filter(premium=1)
        elif target == "free":
            users = await get_users_by_filter(premium=0)
        else:
            users = await get_all_users()

        await state.update_data(target_users=[u["telegram_id"] for u in users])
        await call.message.edit_text(
            f"✅ *{len(users)} ta* foydalanuvchiga yuboriladi\n\n"
            f"Xabar matnini yozing:\n"
            f"_(Markdown formati ishlaydi)_",
            parse_mode="Markdown"
        )
        await state.set_state(BroadcastSt.text)
    await call.answer()

@router.callback_query(BroadcastSt.region, F.data.startswith("bc_region:"))
async def bc_region_select(call: CallbackQuery, state: FSMContext):
    region = call.data.split(":", 1)[1]
    from database.db import get_users_by_filter
    users = await get_users_by_filter(region=region)
    await state.update_data(
        region=region,
        target_users=[u["telegram_id"] for u in users]
    )
    await call.message.edit_text(
        f"📍 {region}\n"
        f"✅ *{len(users)} ta* foydalanuvchiga yuboriladi\n\n"
        f"Xabar matnini yozing:",
        parse_mode="Markdown"
    )
    await state.set_state(BroadcastSt.text)
    await call.answer()

@router.message(BroadcastSt.text)
async def bc_text(msg: Message, state: FSMContext):
    data = await state.get_data()
    targets = data.get("target_users", [])
    region = data.get("region", "")
    target = data.get("target", "all")

    target_names = {
        "all": "Hamma",
        "premium": "Premium",
        "free": "To'lovsizlar",
        "region": region,
    }

    await state.update_data(bc_text=msg.text)
    await msg.answer(
        f"📨 *XABAR PREVIEW*\n\n"
        f"👥 Kimga: *{target_names.get(target, target)}*\n"
        f"📊 Qancha: *{len(targets)} ta*\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{msg.text}\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"Yuborishni tasdiqlaysizmi?",
        reply_markup=__import__('keyboards.keyboards', fromlist=['confirm_cancel_kb']).confirm_cancel_kb("broadcast") if hasattr(__import__('keyboards.keyboards', fromlist=['confirm_cancel_kb']), 'confirm_cancel_kb') else None,
        parse_mode="Markdown"
    )
    # Inline confirm
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text=f"✅ Ha, {len(targets)} taga yuborish", callback_data="bc_confirm")
    b.button(text="❌ Bekor",                               callback_data="bc_cancel")
    b.adjust(1)
    await msg.answer("👇", reply_markup=b.as_markup())
    await state.set_state(BroadcastSt.confirm)

@router.callback_query(BroadcastSt.confirm, F.data == "bc_confirm")
async def bc_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    targets = data.get("target_users", [])
    text = data.get("bc_text", "")
    await state.clear()
    await call.message.edit_text(f"⏳ Yuborilmoqda... 0/{len(targets)}")
    sent = failed = 0
    for uid in targets:
        try:
            await call.bot.send_message(
                uid,
                f"📢 *TRENER XABARI:*\n\n{text}",
                parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            failed += 1
        if (sent + failed) % 20 == 0:
            try:
                await call.message.edit_text(f"⏳ Yuborilmoqda... {sent+failed}/{len(targets)}")
            except Exception:
                pass

    await call.message.edit_text(
        f"✅ *BROADCAST YAKUNLANDI*\n\n"
        f"✅ Yuborildi: *{sent}* ta\n"
        f"❌ Xatolik: *{failed}* ta\n"
        f"📊 Jami: *{len(targets)}* ta"
    )
    await call.answer()

@router.callback_query(BroadcastSt.confirm, F.data == "bc_cancel")
async def bc_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.")
    await call.answer()

# ══════════════════════════════════════════════════════
# /stats — ADMIN STATISTIKA
# ══════════════════════════════════════════════════════
@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!")
        return

    from database.db import get_all_users_detailed, get_users_by_region
    from config import PRICE_30_DAY

    users = await get_all_users_detailed()
    total = len(users)
    premium = sum(1 for u in users if u.get("is_premium"))
    regions = await get_users_by_region()

    # Bugun ro'yxatdan o'tganlar
    today = datetime.now().strftime("%Y-%m-%d")
    today_users = sum(1 for u in users if str(u.get("created_at","")).startswith(today))

    # Ushbu oyda
    month = datetime.now().strftime("%Y-%m")
    month_users = sum(1 for u in users if str(u.get("created_at","")).startswith(month))

    region_top = list(regions.items())[:5]
    region_text = "\n".join([f"  {i+1}. {r}: *{c}* ta" for i,(r,c) in enumerate(region_top)])

    await msg.answer(
        f"📊 *TO'LIQ STATISTIKA*\n\n"
        f"👥 *FOYDALANUVCHILAR:*\n"
        f"  Jami: *{total}* ta\n"
        f"  👑 Premium: *{premium}* ta\n"
        f"  🆓 Oddiy: *{total-premium}* ta\n"
        f"  📅 Bugun: *{today_users}* ta yangi\n"
        f"  📆 Bu oy: *{month_users}* ta yangi\n\n"
        f"💰 *DAROMAD:*\n"
        f"  Jami: *{premium * PRICE_30_DAY:,}* so'm\n"
        f"  Bu oy: hisoblash uchun to'lov bazasi kerak\n\n"
        f"📍 *TOP VILOYATLAR:*\n{region_text}\n\n"
        f"🔥 *CHALLENDJ:*\n"
        f"  Faol: *{sum(1 for u in users if u.get('challenge_day',0)>0)}* ta\n"
        f"  Tugagan (30 kun): hisoblash uchun challenge_progress kerak",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════════════════
# /search — FOYDALANUVCHI QIDIRISH
# ══════════════════════════════════════════════════════
@router.message(Command("search"))
async def cmd_search(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!")
        return

    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(
            "🔍 *QIDIRISH*\n\n"
            "Foydalanish: `/search [ism yoki telefon]`\n"
            "Masalan: `/search Jasur` yoki `/search +998901234567`",
            parse_mode="Markdown"
        )
        return

    from database.db import search_user
    from keyboards.keyboards import user_detail_kb

    query = args[1].strip()
    found = await search_user(query)

    if not found:
        await msg.answer(f"❌ `{query}` bo'yicha hech kim topilmadi.")
        return

    for u in found:
        prem = "👑 Premium" if u.get("is_premium") else "🆓 Oddiy"
        await msg.answer(
            f"👤 *{u.get('full_name','?')}*\n\n"
            f"📱 Tel: `{u.get('phone','-')}`\n"
            f"📍 Viloyat: {u.get('region','-')}\n"
            f"⚖️ Vazn: {u.get('weight','-')} kg | 📏 {u.get('height','-')} sm\n"
            f"👤 Jins: {u.get('gender','-')}\n"
            f"🥗 Plan: {u.get('plan_key','-')}\n"
            f"🆔 TG ID: `{u.get('telegram_id','-')}`\n"
            f"📊 Status: {prem}\n"
            f"📅 {str(u.get('created_at',''))[:10]}",
            reply_markup=user_detail_kb(u["telegram_id"], bool(u.get("is_premium"))),
            parse_mode="Markdown"
        )

# User detail actions
@router.callback_query(F.data.startswith("usr_give_prem:"))
async def usr_give_premium(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    uid = int(call.data.split(":")[1])
    await update_user(uid, is_premium=1, challenge_day=1,
                      challenge_started=datetime.now().isoformat())
    await call.answer("✅ Premium berildi!", show_alert=True)
    try:
        await call.bot.send_message(uid,
            "🎉 *Tabriklaymiz! Sizga Premium berildi!*\n"
            "30-kunlik challendj boshlandi! 🔥",
            reply_markup=main_menu_kb(), parse_mode="Markdown")
    except Exception: pass

@router.callback_query(F.data.startswith("usr_remove_prem:"))
async def usr_remove_premium(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    uid = int(call.data.split(":")[1])
    await update_user(uid, is_premium=0)
    await call.answer("❌ Premium olindi!", show_alert=True)

@router.callback_query(F.data.startswith("usr_block:"))
async def usr_block(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    uid = int(call.data.split(":")[1])
    await update_user(uid, is_active=0)
    await call.answer("🚫 Bloklandi!", show_alert=True)

# ══════════════════════════════════════════════════════
# /help — ADMIN BUYRUQLAR
# ══════════════════════════════════════════════════════
@router.message(Command("help"))
async def cmd_help(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    await msg.answer(
        "👑 *ADMIN BUYRUQLARI*\n\n"
        "👥 *Foydalanuvchilar:*\n"
        "/users — Ro'yxat + statistika + export\n"
        "/search [ism/tel] — Foydalanuvchi qidirish\n"
        "/stats — To'liq statistika\n\n"
        "📨 *Xabar:*\n"
        "/broadcast — Maqsadli xabar (viloyat, premium)\n\n"
        "⚙️ *Boshqaruv:*\n"
        "/admin — Admin panel\n\n"
        "💡 *Maslahat:*\n"
        "• /search +998901234567 — telefon bo'yicha\n"
        "• /broadcast → viloyat → Toshkent shahri",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════════════════
# /payments — TO'LOV BOSHQARUVI (YANGILANGAN)
# ══════════════════════════════════════════════════════
@router.message(Command("payments"))
async def cmd_payments(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!")
        return

    from database.db import get_payment_summary
    from keyboards.keyboards import payments_menu_kb

    summary = await get_payment_summary()
    pending   = summary.get("pending",   {"count":0,"amount":0})
    confirmed = summary.get("confirmed", {"count":0,"amount":0})
    rejected  = summary.get("rejected",  {"count":0,"amount":0})

    await msg.answer(
        f"💳 *TO'LOV BOSHQARUVI*\n\n"
        f"⏳ Kutayotgan:    *{pending['count']}* ta\n"
        f"✅ Tasdiqlangan:  *{confirmed['count']}* ta "
        f"({confirmed['amount']:,} so'm)\n"
        f"❌ Rad etilgan:   *{rejected['count']}* ta\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 *Jami daromad: {confirmed['amount']:,} so'm*\n\n"
        f"Qaysi ro'yxatni ko'rmoqchisiz?",
        reply_markup=payments_menu_kb(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("pay_list:"))
async def cb_pay_list(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌"); return

    from database.db import (get_pending_payments_full,
                              get_rejected_payments, get_payment_summary)
    from keyboards.keyboards import payment_confirm_kb, payments_menu_kb

    status = call.data.split(":")[1]

    if status == "summary":
        summary = await get_payment_summary()
        p = summary.get("pending",   {"count":0,"amount":0})
        c = summary.get("confirmed", {"count":0,"amount":0})
        r = summary.get("rejected",  {"count":0,"amount":0})
        await call.message.edit_text(
            f"📊 *TO'LOV HISOBOTI*\n\n"
            f"⏳ Kutayotgan:   *{p['count']}* ta\n"
            f"✅ Tasdiqlangan: *{c['count']}* ta → *{c['amount']:,}* so'm\n"
            f"❌ Rad etilgan:  *{r['count']}* ta\n\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💰 *JAMI DAROMAD: {c['amount']:,} so'm*",
            reply_markup=payments_menu_kb(),
            parse_mode="Markdown"
        )
        await call.answer()
        return

    if status == "pending":
        payments = await get_pending_payments_full()
        title = "⏳ KUTAYOTGAN TO'LOVLAR"
    elif status == "rejected":
        payments = await get_rejected_payments()
        title = "❌ RAD ETILGAN TO'LOVLAR"
    else:
        payments = []
        title = "✅ TASDIQLANGAN TO'LOVLAR"

    if not payments:
        await call.answer(f"Hozircha bu ro'yxat bo'sh ✅", show_alert=True)
        return

    await call.message.edit_text(
        f"💳 *{title}*\n"
        f"Jami: *{len(payments)}* ta\n\n"
        f"Har bir to'lov alohida ko'rsatiladi 👇",
        reply_markup=payments_menu_kb(),
        parse_mode="Markdown"
    )
    await call.answer()

    # Har bir to'lovni alohida ko'rsatish
    for pay in payments[:10]:  # Max 10 ta
        method_emoji = {"payme":"🟢","click":"🔵","card":"💳"}.get(
            pay.get("method",""), "💳"
        )
        status_text = {
            "pending":   "⏳ Kutmoqda",
            "confirmed": "✅ Tasdiqlangan",
            "rejected":  "❌ Rad etilgan"
        }.get(pay.get("status",""), pay.get("status",""))

        text = (
            f"💳 *To'lov #{pay.get('id','')}*\n\n"
            f"👤 {pay.get('full_name','?')}\n"
            f"📱 `{pay.get('phone','?')}`\n"
            f"📍 {pay.get('region','?')}\n"
            f"⚖️ {pay.get('weight','?')} kg\n"
            f"💰 {pay.get('amount',0):,} so'm\n"
            f"{method_emoji} {pay.get('method','?').upper()}\n"
            f"📊 Status: {status_text}\n"
            f"📅 {str(pay.get('created_at',''))[:16]}"
        )

        # Chek rasmi bor yoki yo'qligini tekshirish
        receipt = pay.get("receipt_file_id")
        uid = pay.get("uid") or pay.get("user_id")

        if receipt and pay.get("status") == "pending":
            try:
                await call.bot.send_photo(
                    call.message.chat.id,
                    photo=receipt,
                    caption=text,
                    reply_markup=payment_confirm_kb(pay["id"], uid),
                    parse_mode="Markdown"
                )
            except Exception:
                await call.bot.send_message(
                    call.message.chat.id,
                    text + "\n\n⚠️ Chek rasmi yuklanmagan",
                    reply_markup=payment_confirm_kb(pay["id"], uid),
                    parse_mode="Markdown"
                )
        elif pay.get("status") == "pending":
            # Cheksiz pending - oddiy confirm tugmasi
            await call.bot.send_message(
                call.message.chat.id,
                text + "\n\n⚠️ Chek rasmi yo'q",
                reply_markup=payment_confirm_kb(pay["id"], uid),
                parse_mode="Markdown"
            )
        else:
            await call.bot.send_message(
                call.message.chat.id, text, parse_mode="Markdown"
            )

# ══════════════════════════════════════════════════════
# /unpaid — HECH TO'LAMAGAN FOYDALANUVCHILAR
# ══════════════════════════════════════════════════════
@router.message(Command("unpaid"))
async def cmd_unpaid(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!")
        return

    from database.db import get_never_paid_users
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    users = await get_never_paid_users()

    if not users:
        await msg.answer("✅ Hamma foydalanuvchi to'lov qilgan!")
        return

    b = InlineKeyboardBuilder()
    b.button(
        text=f"📨 Hammaga xabar yuborish ({len(users)} ta)",
        callback_data="bc_target:never_paid"
    )

    await msg.answer(
        f"❌ *HECH TO'LAMAGAN FOYDALANUVCHILAR*\n\n"
        f"Jami: *{len(users)}* ta\n\n"
        f"_(Ro'yxatdan o'tgan lekin to'lov qilmagan)_\n\n"
        f"━━━━━━━━━━━━━━━━━",
        reply_markup=b.as_markup(),
        parse_mode="Markdown"
    )

    # Ro'yxat (max 20 ta)
    lines = []
    for i, u in enumerate(users[:20], 1):
        days_ago = ""
        if u.get("created_at"):
            try:
                reg_date = datetime.fromisoformat(str(u["created_at"])[:19])
                diff = (datetime.now() - reg_date).days
                days_ago = f"({diff} kun oldin)"
            except Exception:
                pass

        lines.append(
            f"{i}. *{u.get('full_name','?')}*\n"
            f"   📱 `{u.get('phone','-')}`\n"
            f"   📍 {u.get('region','-')} | ⚖️ {u.get('weight','-')} kg\n"
            f"   📅 {str(u.get('created_at',''))[:10]} {days_ago}"
        )

    if lines:
        # 10 tadan yuborish
        chunk = lines[:10]
        await msg.answer(
            f"📋 *Ro'yxat (1-{len(chunk)}/{len(users)}):*\n\n" +
            "\n\n".join(chunk),
            parse_mode="Markdown"
        )
        if len(lines) > 10:
            await msg.answer(
                f"📋 *Ro'yxat ({11}-{len(lines)}/{len(users)}):*\n\n" +
                "\n\n".join(lines[10:]),
                parse_mode="Markdown"
            )

# ══════════════════════════════════════════════════════
# /inactive — CHALLENDJDA YO'QLAR
# ══════════════════════════════════════════════════════
@router.message(Command("inactive"))
async def cmd_inactive(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Ruxsat yo'q!")
        return

    from database.db import get_inactive_premium_users
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    users = await get_inactive_premium_users()

    if not users:
        await msg.answer("🎉 Barcha premium foydalanuvchilar aktiv!")
        return

    b = InlineKeyboardBuilder()
    b.button(
        text=f"📨 Barchasiga eslatma yuborish ({len(users)} ta)",
        callback_data="bc_target:inactive"
    )

    # Guruhlash: umuman boshlamagan vs sekin borayotgan
    not_started = [u for u in users if u.get("done_days", 0) == 0]
    slow = [u for u in users if 0 < u.get("done_days", 0) < 3]

    await msg.answer(
        f"😴 *CHALLENDJDA FAOL BO'LMAGANLAR*\n\n"
        f"👑 Premium foydalanuvchilar:\n"
        f"  🚫 Boshlamagan: *{len(not_started)}* ta\n"
        f"  🐌 Sekin (1-2 kun): *{len(slow)}* ta\n"
        f"  Jami: *{len(users)}* ta\n\n"
        f"━━━━━━━━━━━━━━━━━",
        reply_markup=b.as_markup(),
        parse_mode="Markdown"
    )

    lines = []
    for i, u in enumerate(users[:15], 1):
        done = u.get("done_days", 0)
        status = "🚫 Boshlamagan" if done == 0 else f"📊 {done} kun bajarilgan"
        lines.append(
            f"{i}. *{u.get('full_name','?')}*\n"
            f"   📍 {u.get('region','-')} | {status}\n"
            f"   📱 `{u.get('phone','-')}`"
        )

    if lines:
        await msg.answer(
            f"📋 *Ro'yxat:*\n\n" + "\n\n".join(lines),
            parse_mode="Markdown"
        )

# ══════════════════════════════════════════════════════
# BROADCAST — YANGI TARGETLAR (pending, never_paid, inactive)
# ══════════════════════════════════════════════════════
@router.callback_query(BroadcastSt.target, F.data.startswith("bc_target:"))
async def bc_target_v2(call: CallbackQuery, state: FSMContext):
    target = call.data.split(":")[1]
    await state.update_data(target=target)

    from database.db import (get_pending_users_ids, get_never_paid_users,
                              get_inactive_premium_users)

    if target == "region":
        from keyboards.keyboards import broadcast_regions_kb
        await call.message.edit_text(
            "📍 Qaysi viloyat?",
            reply_markup=broadcast_regions_kb()
        )
        await state.set_state(BroadcastSt.region)
        await call.answer()
        return

    # Targetga qarab userlarni olish
    if target == "all":
        users = await get_all_users()
        target_ids = [u["telegram_id"] for u in users]
        label = "Hammaga"
    elif target == "premium":
        from database.db import get_users_by_filter
        users = await get_users_by_filter(premium=1)
        target_ids = [u["telegram_id"] for u in users]
        label = "Premium foydalanuvchilar"
    elif target == "pending":
        target_ids = await get_pending_users_ids()
        label = "⏳ To'lov kutilmoqda"
    elif target == "never_paid":
        users = await get_never_paid_users()
        target_ids = [u["telegram_id"] for u in users]
        label = "❌ Hech to'lamagan"
    elif target == "inactive":
        users = await get_inactive_premium_users()
        target_ids = [u["telegram_id"] for u in users]
        label = "😴 Challendjda yo'q (premium)"
    else:
        target_ids = []
        label = target

    await state.update_data(target_users=target_ids, target_label=label)

    if not target_ids:
        await call.answer(f"Bu guruhda hech kim yo'q!", show_alert=True)
        return

    # Default xabarlar taklif qilish
    suggestions = {
        "pending": (
            "⏳ *Hurmatli foydalanuvchi!*\n\n"
            "To'lovingiz hali tasdiqlanmagan.\n"
            "Agar to'lov qilgan bo'lsangiz, chek rasmini yuboring.\n\n"
            "Savollar uchun: @QaytaTugulishBot"
        ),
        "never_paid": (
            "🔥 *Salom!*\n\n"
            "Siz ro'yxatdan o'tdingiz, lekin hali to'lov qilmadingiz.\n\n"
            "30-kunlik challendj sizni kutmoqda! 💪\n"
            "Bugun boshlaganlar ertaga natija ko'radi!\n\n"
            "Boshlash uchun /start bosing 👇"
        ),
        "inactive": (
            "💪 *Salom, chempion!*\n\n"
            "Siz bir necha kun challendj qilmadingiz.\n\n"
            "Bir kunlik tanaffus maqsaddan chalg'itmasin! 🎯\n"
            "Bugun qaytib keling — biz sizi kutmoqdamiz!\n\n"
            "/start → 30-Kunlik Challendj"
        ),
    }

    suggestion = suggestions.get(target, "")
    suggestion_text = f"\n\n💡 *Tavsiya etilgan xabar:*\n```\n{suggestion}\n```\n\nYoki o'z xabaringizni yozing:" if suggestion else "\nXabar matnini yozing:"

    await call.message.edit_text(
        f"✅ *{label}*\n"
        f"👥 *{len(target_ids)}* ta foydalanuvchiga yuboriladi\n"
        f"{suggestion_text}",
        parse_mode="Markdown"
    )
    await state.set_state(BroadcastSt.text)
    await call.answer()

# ══════════════════════════════════════════════════════
# /help YANGILANGAN
# ══════════════════════════════════════════════════════
@router.message(Command("help"))
async def cmd_help_v2(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer(
        "👑 *ADMIN BUYRUQLARI*\n\n"

        "💳 *To'lovlar:*\n"
        "/payments — To'lov boshqaruvi\n"
        "  ├ ⏳ Kutayotganlar (tasdiqlash)\n"
        "  ├ ✅ Tasdiqlanganlar\n"
        "  └ ❌ Rad etilganlar\n\n"

        "👥 *Foydalanuvchilar:*\n"
        "/users — Ro'yxat + eksport (CSV/TXT)\n"
        "/unpaid — Hech to'lamagan [N ta]\n"
        "/inactive — Challendjda yo'q premium\n"
        "/search [ism/tel] — Qidirish\n"
        "/stats — Batafsil statistika\n\n"

        "📨 *Broadcast (xabar):*\n"
        "/broadcast — Maqsadli xabar\n"
        "  ├ 👥 Hammaga\n"
        "  ├ 👑 Premium\n"
        "  ├ ⏳ To'lov kutilmoqda\n"
        "  ├ ❌ Hech to'lamagan\n"
        "  ├ 😴 Challendjda yo'q\n"
        "  └ 📍 Viloyat bo'yicha\n\n"

        "⚙️ *Boshqaruv:*\n"
        "/admin — Admin panel\n"
        "/help — Ushbu menyu",
        parse_mode="Markdown"
    )
