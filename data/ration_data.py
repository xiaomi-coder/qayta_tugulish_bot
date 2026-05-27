# ════════════════════════════════════════
#   QAYTA TUG'ILISH — Kunlik Ratsion Ma'lumotlari
# ════════════════════════════════════════

# ── 90-110 kg uchun ratsion ──────────────────────────────
RATION_90_110 = {
    "title": "90-110 kg",
    "water": "4-6 litr/kun",
    "meals": [
        {
            "name": "NONUSHTA",
            "icon": "🌅",
            "time": "07:00 — 08:30",
            "foods": [
                "5 ta qaynatilgan tuxum oki",
                "2 ta tuxum sarigi",
                "50g sulli botqa (ovesyanka)",
                "1 porsiya Whey Isolate",
                "2 qoshiq zaytun yogi (protein ichiga)",
            ],
            "cal": 720,
            "protein": 56,
            "carbs": 30,
            "fat": 38,
            "note": "Proteinga zaytun yogi qoshib aralashtirib iching",
            "recipe": (
                "1. Tuxum oqlarini ajratib, qaynatib oling\n"
                "2. Sulli botqani issiq suv yoki sutda damlab qo'ying\n"
                "3. Whey Isolate proteinni suvda aralashtiring\n"
                "4. 2 qoshiq zaytun yogini protein ichiga soling\n"
                "5. Hammasi birga iste'mol qiling"
            ),
        },
        {
            "name": "TUSHLIK",
            "icon": "🍗",
            "time": "12:30 — 13:30",
            "foods": [
                "250g tovuq goshti (pishirilgan)",
                "50g grechka",
                "Bodring + pomidor salat",
                "2 qoshiq zaytun yogi (salatga)",
            ],
            "cal": 680,
            "protein": 75,
            "carbs": 32,
            "fat": 22,
            "note": "Salatga zaytun yogi solib aring",
            "recipe": (
                "1. Tovuq go'shtini tuz va ziravorlar bilan pishiring\n"
                "2. Grechkani 1:2 nisbatda suv bilan 15 daq qaynatib pishiring\n"
                "3. Bodring va pomidorni to'g'rang\n"
                "4. Salatga 2 qoshiq zaytun yogi soling\n"
                "5. Hammasi birga issiq holda iste'mol qiling"
            ),
        },
        {
            "name": "ORALIQ OVQAT",
            "icon": "🥗",
            "time": "15:30 — 16:30",
            "foods": [
                "250g tovuq goshti (pishirilgan)",
                "Yashil salat",
            ],
            "cal": 350,
            "protein": 55,
            "carbs": 5,
            "fat": 8,
            "note": "Oddiy salat bilan eyish tavsiya etiladi",
            "recipe": (
                "1. Oldindan pishirilgan tovuq go'shtini isiting\n"
                "2. Yashil salat barglarini yuvib, to'g'rang\n"
                "3. Oddiy tuzlab, zaytun yogi (ixtiyoriy) soling\n"
                "4. Tovuq bilan birga iste'mol qiling"
            ),
        },
        {
            "name": "KECHKI OVQAT",
            "icon": "🌙",
            "time": "19:00 — 20:00",
            "foods": [
                "200g gusht",
                "Yangi bodring salati",
            ],
            "cal": 300,
            "protein": 44,
            "carbs": 4,
            "fat": 8,
            "note": "Yengil va oson hazm boluvchi kechki ovqat",
            "recipe": (
                "1. Go'shtni tuz va ziravorlar bilan pishiring\n"
                "2. Bodringni yuvib, tilim-tilim kezing\n"
                "3. Engil tuzlab salat qiling\n"
                "4. Kechki ovqatda og'ir taomlardan saqlaning"
            ),
        },
        {
            "name": "YOTISHDAN OLDIN",
            "icon": "💊",
            "time": "21:30 — 22:30",
            "foods": [
                "5 ta qaynatilgan tuxum oki",
                "2 ta tuxum sarigi",
                "1 porsiya Whey Isolate",
                "5g Arginin",
            ],
            "cal": 390,
            "protein": 57,
            "carbs": 3,
            "fat": 15,
            "note": "Argininni protein ichiga solib aralashtirib iching",
            "recipe": (
                "1. Tuxumlarni qaynatib, oqini ajrating (5 ta oq, 2 ta sariq)\n"
                "2. Whey Isolate proteinni suvda aralashtiring\n"
                "3. 5g Argininni protein ichiga solib yaxshilab aralashtiring\n"
                "4. Tuxumlar va protein shake birga iste'mol qiling\n"
                "5. Bu tun davomida mushaklar tiklanishini ta'minlaydi"
            ),
        },
    ],
}

# ── 110-150 kg uchun ratsion (keyinroq qoshiladi) ──────────
RATION_110_150 = RATION_90_110   # placeholder

# ── 150+ kg uchun ratsion (keyinroq qoshiladi) ─────────────
RATION_150_PLUS = RATION_90_110  # placeholder


# ── Erkaklar uchun ──────────────────────────────────────────
def _men_ration(weight: float) -> dict:
    if weight <= 110:
        return RATION_90_110
    elif weight <= 150:
        return RATION_110_150
    else:
        return RATION_150_PLUS

# ── Ayollar uchun (kelajakda RATION_WOMEN_90_110 qoshiladi) ─
def _women_ration(weight: float) -> dict:
    r = dict(_men_ration(weight))
    r = {**r, "title": r["title"] + " (Ayol)"}
    return r

# ── Asosiy funksiyalar ───────────────────────────────────────
def get_ration_for_weight(weight: float) -> dict:
    return _men_ration(weight)

def get_ration_for_weight_gender(weight: float, gender: str = "erkak") -> dict:
    """Vazn va jinsga qarab ratsion tanlash"""
    if gender == "ayol":
        return _women_ration(weight)
    return _men_ration(weight)
