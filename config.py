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

# ── Kanal
CHANNEL = os.getenv("CHANNEL", "@farruxradjabov")

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
