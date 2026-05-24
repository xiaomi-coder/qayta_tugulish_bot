# ═══════════════════════════════════════
# 30 KUNLIK OVQAT VA MASHQ MA'LUMOTLARI
# ═══════════════════════════════════════

MEALS_DATA = {
    "nonushta": {
        "time": "07:30", "name": "Nonushta", "icon": "🌅",
        "cal": 420, "protein": 38,
        "foods": ["Tuxum oqsilasi — 4 ta", "Suli bo'tqasi — 80g", "Banana — 1 ta", "Yashil choy"],
        "recipe": (
            "1️⃣ Tuxum oqlarini sariqdan ajratingda, teflonli tavada yog'siz qovuring\n"
            "2️⃣ Suli bo'tqasini 300ml sut yoki suv bilan 5 daqiqa qaynatib pishiring\n"
            "3️⃣ Tuz va ziravorlar (ixtiyoriy) soling\n"
            "4️⃣ Banana bilan birga iste'mol qiling\n"
            "5️⃣ Yashil choy iching — metabolizmni tezlashtiradi"
        )
    },
    "ikkinchi_nonushta": {
        "time": "10:30", "name": "2-Nonushta", "icon": "🥜",
        "cal": 310, "protein": 28,
        "foods": ["Grechka — 60g", "Tvorog 0% — 150g", "Olma — 1 ta", "Asal — 1 ch.q."],
        "recipe": (
            "1️⃣ Grechkani 2 marta suv bilan yuving\n"
            "2️⃣ 1:2 nisbatda suv quyib, qoqqa qaynatib pishiring (15 daqiqa)\n"
            "3️⃣ Tvorogni asal bilan aralashtiring\n"
            "4️⃣ Ikkalasini bir vaqtda iste'mol qiling\n"
            "5️⃣ Olmani keyin yeng"
        )
    },
    "tushlik": {
        "time": "13:00", "name": "Tushlik", "icon": "🍗",
        "cal": 550, "protein": 52,
        "foods": ["Tovuq ko'kragi — 200g", "Guruch — 100g", "Sabzavot salati", "Zeytun yog'i — 1 ch.q.", "Limon"],
        "recipe": (
            "1️⃣ Tovuqni tuz, qalampir, sarımsaq bilan ziravorlang\n"
            "2️⃣ 180°C da 25 daqiqa pishiring yoki tavada qovuring\n"
            "3️⃣ Guruchni yuving, ikki barobar suv bilan 20 daqiqa qaynatib pishiring\n"
            "4️⃣ Pomidor, bodring, karam tug'rab salat qiling\n"
            "5️⃣ Zeytun yog'i va limon shirasi sepib, surtib qo'ying"
        )
    },
    "kechki_oldi": {
        "time": "16:30", "name": "Kechki oldi", "icon": "🥗",
        "cal": 380, "protein": 35,
        "foods": ["Tuna konservasi — 100g", "Buterbrod non — 1 bo'lak", "Kefir 1% — 250ml", "Ko'k sabzavotlar"],
        "recipe": (
            "1️⃣ Tunani non ustiga bir tekis joylashtiring\n"
            "2️⃣ Ko'k sabzavot (ismaloq, ukrop) qo'shing\n"
            "3️⃣ Kefirni alohida iching\n"
            "4️⃣ Mashqdan 1 soat oldin iste'mol qiling\n"
            "5️⃣ Kefir hazm qilishni yaxshilaydi"
        )
    },
    "kechki": {
        "time": "19:30", "name": "Kechki ovqat", "icon": "🌙",
        "cal": 340, "protein": 42,
        "foods": ["Qizil baliq (losos) — 150g", "Brokkoli — 200g", "Zeytun yog'i — 1 ch.q.", "Limon"],
        "recipe": (
            "1️⃣ Baliqni tuz va limon bilan 30 daqiqa marinlang\n"
            "2️⃣ Tavada har tomondan 6 daqiqadan qovuring\n"
            "3️⃣ Brokkolini bug'da 8 daqiqa pishiring (C vitamin saqlanadi)\n"
            "4️⃣ Zeytun yog'i sepib, issiq holatda yeng\n"
            "5️⃣ Kechqurun og'ir ovqatlardan saqlaning"
        )
    },
}

# ── Har kunning ovqat rejasi
def get_day_meals(day: int) -> list[dict]:
    meals = [
        MEALS_DATA["nonushta"],
        MEALS_DATA["ikkinchi_nonushta"],
        MEALS_DATA["tushlik"],
        MEALS_DATA["kechki_oldi"],
    ]
    # Har 5 kunda kechki ovqat qo'shiladi
    if day % 5 == 0:
        meals.append(MEALS_DATA["kechki"])
    return meals


# ═══════════════════════════════════════
# MASHQLAR MA'LUMOTLARI
# ═══════════════════════════════════════

EXERCISE_SETS = [
    # SET 1 — Oyoq kuni
    [
        {"name": "Squat", "sets": "4×12", "icon": "🦵", "muscle": "Son, dumba",
         "desc": "Oyoqlar yelka kengligida, tizzalar oyoq barmoqlaridan tashqariga chiqmasin. Belni to'g'ri saqlang. Sekin tushing (3s), tez ko'taring (1s)."},
        {"name": "Romanian Deadlift", "sets": "3×10", "icon": "💪", "muscle": "Orqa son, dumba",
         "desc": "Gantelni qo'lda ushlab, belni to'g'ri saqlagan holda oldinga eging. Orqa son cho'zilishini his qiling. Sekin qayting."},
        {"name": "Leg Press", "sets": "4×15", "icon": "⚡", "muscle": "Kvadritseps",
         "desc": "Oyoqlar balandroq — dumba ko'proq ishlaydi. Tizzalar 90° burchakkacha buking. Oyoq uchlarida ko'tarmang."},
        {"name": "Calf Raise", "sets": "4×20", "icon": "🏃", "muscle": "Ikra",
         "desc": "Oyoq uchida ko'taring, 2 soniya yuqorida ushlab turing. Sekin tushing. Baland platformada bajarsangiz amplituda kengayadi."},
    ],
    # SET 2 — Ko'krak/Triseps kuni
    [
        {"name": "Bench Press", "sets": "4×10", "icon": "💥", "muscle": "Ko'krak, triseps",
         "desc": "Ko'krakga tegguncha tushing, to'liq ko'taring. Yelkalar orqada va pastda bo'lsin. Tirsak 45° burchakda."},
        {"name": "Incline Dumbbell Press", "sets": "3×12", "icon": "📐", "muscle": "Yuqori ko'krak",
         "desc": "30-45° burchakda yoting. Ko'krak cho'zilishini his qiling. Gantelli yaqinlashtirganingizda nafas chiqaring."},
        {"name": "Tricep Pushdown", "sets": "4×15", "icon": "🔽", "muscle": "Triseps",
         "desc": "Tirsak yon tomonda, faqat bilak harakatlansin. Pastga itarganingizda qo'lni to'liq cho'zing. Sekin qayting."},
        {"name": "Shoulder Press", "sets": "3×12", "icon": "🦾", "muscle": "Yelka",
         "desc": "Bar quloqqa qadar tushing, to'liq ko'taring. Bel yo'zini bukmang. Yengil og'irlikdan boshlang."},
    ],
    # SET 3 — Orqa/Biseps kuni
    [
        {"name": "Pull-up", "sets": "4×8", "icon": "⬆️", "muscle": "Keng orqa, biseps",
         "desc": "Iyakni shtangadan yuqoriga ko'taring. Sekin tushing. Boshlab qiyin bo'lsa, rezinka yordamida bajaring."},
        {"name": "Bent-over Row", "sets": "4×10", "icon": "🏋️", "muscle": "Orqa o'rta",
         "desc": "45° egiling, tirsak qovurg'aga torting. Orqa to'g'ri va barqaror bo'lsin. Yelkani yuqoriga ko'tarmang."},
        {"name": "Bicep Curl", "sets": "3×15", "icon": "💪", "muscle": "Biseps",
         "desc": "Tirsak yon tomonda qimirlamasin, faqat bilak ko'tarilsin. Sekin tushiring — bu ham kuch. Cheating qilmang."},
        {"name": "Face Pull", "sets": "3×15", "icon": "🎯", "muscle": "Orqa yelka, trapetsiya",
         "desc": "Ko'z darajasida torting, tirsak yuqorida bo'lsin. Yelkani orqaga tortish kerak. Posturani yaxshilaydi."},
    ],
]

def get_day_exercises(day: int) -> list[dict]:
    return EXERCISE_SETS[(day - 1) % 3]


# ═══════════════════════════════════════
# KUNLIK MASLAHATLAR
# ═══════════════════════════════════════
DAILY_TIPS = [
    "💡 Har mashqdan keyin 10 daqiqa cho'zilish qiling — bu travmadan himoya qiladi",
    "💡 Uyquga ketishdan 2 soat oldin ovqat emang — tana yog' yoqadi",
    "💡 Har kuni bir xil vaqtda uyg'oning — bioritm tartibga tushadi",
    "💡 Mushaklar dam olish vaqtida o'sadi, demak uyqu muhim!",
    "💡 Progress surat oling — 2 haftada bir. Ko'rinmas o'zgarishlar borligini ko'rasiz",
    "💡 Suv iching! Har 1kg vazn uchun 30ml suv kerak",
    "💡 Mashq oldidan 30 daqiqa engil uglevod — energiya beradi",
    "💡 Og'riq va toliqish farqi: og'riq to'xtash belgisi, toliqish — davom etish belgisi",
    "💡 Kaloriya hisoblang — hatto sog'lom ovqat ko'p yeyilsa ham ortiqcha bo'ladi",
    "💡 Har kuni 7-9 soat uxlang — o'sish gormoni asosan tunda ishlab chiqariladi",
]

def get_day_tip(day: int) -> str:
    return DAILY_TIPS[(day - 1) % len(DAILY_TIPS)]


# ═══════════════════════════════════════
# MOTIVATSION GAPLAR
# ═══════════════════════════════════════
MOTIVATIONS = [
    "🔥 Bugun og'ir bo'lsa ham — ertaga yengilroq bo'ladi. Davom et!",
    "⚡ Har bir qadam seni maqsadga yaqinlashtiradi. To'xtama!",
    "💪 Semizlikdan ozginlikka — bu safar emas, bu yangi hayot!",
    "🧠 Kuchli tana kuchli fikrdan boshlanadi. Sen kuchlisin!",
    "🏆 30 kunlik challendj — bir umrlik o'zgarish!",
    "👑 Farrux aytadi: Har kuni bir qadam oldinga!",
    "🌟 Bugun bajargan mashqing — ertangi sog'liqing!",
    "✨ O'zingga ishon — natija o'z-o'zidan keladi!",
    "🚀 Hech kim seni to'xtata olmaydi — faqat o'zing!",
    "💥 Bugungi og'riq — ertangi g'urur!",
    "🎯 Maqsad aniq bo'lsa, yo'l topiladi!",
    "🌅 Har yangi kun — yangi imkoniyat!",
]

def get_motivation(day: int) -> str:
    return MOTIVATIONS[(day - 1) % len(MOTIVATIONS)]
