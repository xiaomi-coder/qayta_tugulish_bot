import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ── Admin Telegram IDlar (vergul bilan)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]

# ── Database
DB_PATH = "bot_database.db"

# ── To'lov rekvizitlari (admin sozlaydi)
PAYMENT_CARD     = os.getenv("PAYMENT_CARD",  "8600 1234 5678 9012")
PAYMENT_PAYME    = os.getenv("PAYMENT_PAYME", "+998901234567")
PAYMENT_CLICK    = os.getenv("PAYMENT_CLICK", "https://my.click.uz/services/pay?service_id=12345")

# ── Narxlar (so'm)
PRICE_30_DAY   = int(os.getenv("PRICE_30_DAY",   "149000"))
PRICE_3_MONTH  = int(os.getenv("PRICE_3_MONTH",  "349000"))

# ── LAUNCH LOCK: bot vaqtincha yopiq (faqat ro'yxatdan o'tish + to'lov ochiq)
# Kontent (mashqlar, ratsion) dushanbadan ochiladi. Ochish uchun .env da LAUNCH_LOCKED=0 qo'ying.
LAUNCH_LOCKED    = os.getenv("LAUNCH_LOCKED", "1") == "1"
LAUNCH_DATE_TEXT = os.getenv("LAUNCH_DATE_TEXT", "dushanba")

# ── Kanal
CHANNEL = os.getenv("CHANNEL", "@QaytaTugulishBot")

# ── Obuna shart bo'lgan kanal (bo'sh qolsa tekshirilmaydi)
MUST_JOIN_CHANNEL = os.getenv("MUST_JOIN_CHANNEL", "@farruxrajabov94")

# ── Vazn bo'yicha ratsion ranji
def get_plan_by_weight(weight: float) -> str:
    if weight < 100:
        return "standard"
    elif weight < 150:
        return "plan_100_150"
    elif weight < 200:
        return "plan_150_200"
    else:
        return "plan_200_plus"

PLAN_NAMES = {
    "standard":      "⚪ Standart (100 kg gacha)",
    "plan_100_150":  "🟡 Plan A (100-150 kg)",
    "plan_150_200":  "🟠 Plan B (150-200 kg)",
    "plan_200_plus": "🔴 Plan C (200+ kg)",
}

# ── WLCM (Paylov) integratsiya
WLCM_API_KEY      = os.getenv("WLCM_API_KEY", "")
WLCM_API_SECRET   = os.getenv("WLCM_API_SECRET", "")
WLCM_BASE_URL     = os.getenv("WLCM_BASE_URL", "https://sandbox.wlcm.uz")
WLCM_WEBHOOK_PORT = int(os.getenv("WLCM_WEBHOOK_PORT", "8080"))
WLCM_RETURN_URL   = os.getenv("WLCM_RETURN_URL", "https://t.me/QaytaTugulishBot")

def wlcm_enabled() -> bool:
    return bool(WLCM_API_KEY and WLCM_API_SECRET)

# ── Ratsion plan rasmlari uchun kategoriyalar
RATION_PLAN_KEYS = {
    "plan_80_plus":  "💪 80+ kg",
    "plan_90_110":   "🔥 90-110 kg",
    "plan_110_plus": "⚡ 110+ kg",
    "child_9_13":    "👦 9-13 yosh",
}

def get_ration_plan_key(weight: float, age_group: str = "adult") -> str:
    """Foydalanuvchining ratsion plan kalitini qaytaradi"""
    if age_group == "child":
        return "child_9_13"
    if weight < 90:
        return "plan_80_plus"
    elif weight <= 110:
        return "plan_90_110"
    else:
        return "plan_110_plus"
