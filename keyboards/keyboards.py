from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ════ REGIONS ════
UZBEKISTAN_REGIONS = [
    "Toshkent shahri",
    "Toshkent viloyati",
    "Samarqand",
    "Buxoro",
    "Namangan",
    "Fargona",
    "Andijon",
    "Qashqadaryo",
    "Surxondaryo",
    "Xorazm",
    "Navoiy",
    "Sirdaryo",
    "Jizzax",
    "Qoraqalpogiston",
    "Xorijda yashayman",
]

def region_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    for r in UZBEKISTAN_REGIONS:
        b.button(text=r)
    b.adjust(2)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)

# ════ BROADCAST TARGET ════
def broadcast_target_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Hammaga",               callback_data="bc_target:all")
    b.button(text="Faqat premium",         callback_data="bc_target:premium")
    b.button(text="To'lov kutilmoqda",     callback_data="bc_target:pending")
    b.button(text="Hech to'lamagan",       callback_data="bc_target:never_paid")
    b.button(text="Challengeda yoq",       callback_data="bc_target:inactive")
    b.button(text="Viloyat boyicha",       callback_data="bc_target:region")
    b.adjust(1)
    return b.as_markup()

# ════ PAYMENTS ADMIN ════
def payments_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Kutayotganlar",    callback_data="pay_list:pending")
    b.button(text="Tasdiqlanganlar",  callback_data="pay_list:confirmed")
    b.button(text="Rad etilganlar",   callback_data="pay_list:rejected")
    b.button(text="Umumiy hisobot",   callback_data="pay_list:summary")
    b.button(text="Admin",            callback_data="admin_main")
    b.adjust(2, 2, 1)
    return b.as_markup()

def never_paid_kb(uid: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Xabar yuborish",    callback_data=f"np_msg:{uid}")
    b.button(text="Qolda premium",     callback_data=f"usr_give_prem:{uid}")
    b.adjust(2)
    return b.as_markup()

def broadcast_regions_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for r in UZBEKISTAN_REGIONS:
        b.button(text=r, callback_data=f"bc_region:{r}")
    b.button(text="Orqaga", callback_data="broadcast_back")
    b.adjust(2)
    return b.as_markup()

# ════ USER DETAIL ════
def user_detail_kb(uid: int, is_premium: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if is_premium:
        b.button(text="Premiumni olish", callback_data=f"usr_remove_prem:{uid}")
    else:
        b.button(text="Premium berish",  callback_data=f"usr_give_prem:{uid}")
    b.button(text="Xabar yuborish",      callback_data=f"usr_msg:{uid}")
    b.button(text="Bloklash",            callback_data=f"usr_block:{uid}")
    b.button(text="Royxatga",            callback_data="admin:users")
    b.adjust(1)
    return b.as_markup()

# ════ EXPORT FORMAT ════
def export_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="TXT format",  callback_data="export:txt")
    b.button(text="CSV format",  callback_data="export:csv")
    b.button(text="Orqaga",      callback_data="admin_main")
    b.adjust(2)
    return b.as_markup()

# ════ START ════
def start_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Boshlash!", callback_data="start_reg")
    return b.as_markup()

# ════ GENDER ════
def gender_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Erkak", callback_data="gender:erkak")
    b.button(text="Ayol",  callback_data="gender:ayol")
    b.adjust(2)
    return b.as_markup()

# ════ PHONE ════
def phone_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="Telefon raqamni yuborish", request_contact=True)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)

# ════ CHALLENGE INFO ════
def challenge_info_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Tolovga otish", callback_data="go_payment")
    return b.as_markup()

# ════ PAYMENT METHOD ════
def payment_method_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Payme",           callback_data="pay_method:payme")
    b.button(text="Click",           callback_data="pay_method:click")
    b.button(text="Karta (otkazma)", callback_data="pay_method:card")
    b.adjust(1)
    return b.as_markup()

# ════ AFTER PAYMENT DETAILS ════
def after_payment_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Tolov qildim, chek yuboraman", callback_data="send_receipt")
    return b.as_markup()

# ════ MAIN MENU (premium) ════
def main_menu_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="🔥 30-Kunlik Challendj"))
    b.row(KeyboardButton(text="🥗 Mening Ratsionim"),
          KeyboardButton(text="💧 Suv Tracker"))
    b.row(KeyboardButton(text="🏋️ Mashqlar"),
          KeyboardButton(text="📊 Statistika"))
    b.row(KeyboardButton(text="👤 Profilim"),
          KeyboardButton(text="⚙️ Sozlamalar"))
    return b.as_markup(resize_keyboard=True)

# ════ CHALLENGE ════
def challenge_kb(completed: list, current: int = 1) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for day in range(1, 31):
        if day in completed:
            text = f"✅ {day}"
        elif day == current:
            text = f"🔥 {day}"
        else:
            text = str(day)
        b.button(text=text, callback_data=f"day:{day}")
    b.adjust(5)
    return b.as_markup()

def day_detail_kb(day: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Ovqatlar",       callback_data=f"meals:{day}")
    b.button(text="Mashqlar",       callback_data=f"exercises:{day}")
    b.button(text="Suv qoshish",    callback_data=f"water_day:{day}")
    b.button(text="Kunni yakunlash",callback_data=f"complete:{day}")
    b.button(text="Challendj",      callback_data="challenge_main")
    b.adjust(2, 2, 1)
    return b.as_markup()

def meals_kb(day: int, meals: list, logged: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, m in enumerate(meals):
        done = "✅ " if i in logged else ""
        b.button(text=f"{done}{m['icon']} {m['name']} ({m['time']})",
                 callback_data=f"meal_detail:{day}:{i}")
    b.button(text="Orqaga", callback_data=f"day:{day}")
    b.adjust(1)
    return b.as_markup()

def meal_detail_kb(day: int, idx: int, logged: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Bekor" if logged else "Yedim!",
             callback_data=f"meal_toggle:{day}:{idx}")
    b.button(text="Ovqatlar", callback_data=f"meals:{day}")
    b.adjust(1)
    return b.as_markup()

def exercises_kb(day: int, exs: list, logged: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, ex in enumerate(exs):
        done = "✅ " if i in logged else ""
        b.button(text=f"{done}{ex['icon']} {ex['name']} — {ex['sets']}",
                 callback_data=f"ex_detail:{day}:{i}")
    b.button(text="Orqaga", callback_data=f"day:{day}")
    b.adjust(1)
    return b.as_markup()

def exercise_detail_kb(day: int, idx: int, logged: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Bekor" if logged else "Bajarildi!",
             callback_data=f"ex_toggle:{day}:{idx}")
    b.button(text="Mashqlar", callback_data=f"exercises:{day}")
    b.adjust(1)
    return b.as_markup()

def water_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="+250ml", callback_data="water:250")
    b.button(text="+500ml", callback_data="water:500")
    b.button(text="+750ml", callback_data="water:750")
    b.button(text="+1L",    callback_data="water:1000")
    b.adjust(2, 2)
    return b.as_markup()

# ════ ADMIN ════
def admin_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Kutayotgan tolovlar",    callback_data="admin:payments")
    b.button(text="Ratsion rasmi yuklash",  callback_data="admin:ration_photo")
    b.button(text="Ovqat rasmi yuklash",    callback_data="admin:upload_photo")
    b.button(text="Mashq videosi yuklash",  callback_data="admin:upload_video")
    b.button(text="Salomlashuv videosi",    callback_data="admin:welcome_video")
    b.button(text="Motivatsiya videosi",    callback_data="admin:motivation_video")
    b.button(text="Ratsion tahrirlash",     callback_data="admin:edit_nutrition")
    b.button(text="Hammaga xabar",          callback_data="admin:broadcast")
    b.button(text="Foydalanuvchilar",       callback_data="admin:users")
    b.button(text="Statistika",             callback_data="admin:stats")
    b.button(text="Premium berish",         callback_data="admin:give_premium")
    b.adjust(1)
    return b.as_markup()

def payment_confirm_kb(pay_id: int, uid: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Tasdiqlash — Kirish berish", callback_data=f"admin_confirm:{pay_id}:{uid}")
    b.button(text="Rad etish",                  callback_data=f"admin_reject:{pay_id}:{uid}")
    b.adjust(1)
    return b.as_markup()

def nutrition_plans_kb(plans: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in plans:
        b.button(text=p["title"], callback_data=f"edit_plan:{p['plan_key']}")
    b.button(text="Orqaga", callback_data="admin_main")
    b.adjust(1)
    return b.as_markup()

def video_type_kb(ex_key: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Aylana video (tavsiya)", callback_data=f"vtype:video_note:{ex_key}")
    b.button(text="Oddiy video",            callback_data=f"vtype:video:{ex_key}")
    b.adjust(1)
    return b.as_markup()

def back_kb(cb: str = "main_menu") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Orqaga", callback_data=cb)
    return b.as_markup()

def settings_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="Mening ratsionim",   callback_data="my_nutrition")
    b.button(text="Premium xizmatlar",  callback_data="premium_info")
    b.button(text="Mening progressim",  callback_data="my_progress")
    b.adjust(1)
    return b.as_markup()
