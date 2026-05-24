# 🔥 QAYTA TUG'ILISH — Fitness Telegram Bot

**Professional GYM Trener Farrux Rajabov'ning onlayn bot platformasi**

---

## 📋 IMKONIYATLAR

- ✅ Ro'yxatdan o'tish (ism, telefon, bo'y, vazn)
- ✅ 30-kunlik challendj (inline tugmalar ✅/❌)
- ✅ Har kun uchun ovqat retseptlari + rasmlar
- ✅ Har kun uchun mashq ko'rsatmalari
- ✅ Suv tracker (+250ml, +500ml, +750ml)
- ✅ Avtomatik eslatmalar (7 ta vaqtda)
- ✅ Admin panel (xabar, rasm yuklash, premium berish)
- ✅ Foydalanuvchi statistikasi
- ✅ Premium tizim

---

## 🚀 O'RNATISH

### 1. Talablar
```bash
Python 3.11+
pip
```

### 2. Fayllarni yuklab olish
```bash
cd qayta_tugulish_bot
```

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. .env faylini sozlash
```bash
cp .env.example .env
# .env faylini tahrirlang:
nano .env
```

**.env fayliga yozing:**
```
BOT_TOKEN=7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789
```

**Bot token olish:**
1. Telegramda @BotFather ga yozing
2. /newbot buyrug'ini bering
3. Bot nomini va username'ini kiriting
4. Token ni nusxalang

**Admin ID olish:**
1. Telegramda @userinfobot ga yozing
2. ID raqamini nusxalang

### 5. Botni ishga tushurish
```bash
python main.py
```

---

## 📁 FAYL TUZILISHI

```
qayta_tugulish_bot/
├── main.py              ← Asosiy fayl (shu ni ishga tushuring)
├── config.py            ← Sozlamalar
├── requirements.txt     ← Kutubxonalar
├── .env.example         ← Environment namuna
├── .env                 ← Sizning sozlamalaringiz (o'zingiz yaratasiz)
├── bot.log              ← Log fayl (avtomatik yaratiladi)
├── bot_database.db      ← Database (avtomatik yaratiladi)
│
├── database/
│   └── db.py            ← Database so'rovlari
│
├── handlers/
│   └── handlers.py      ← Barcha handlerlar
│
├── keyboards/
│   └── keyboards.py     ← Barcha tugmalar
│
├── data/
│   └── meals_data.py    ← Ovqat va mashq ma'lumotlari
│
└── utils/
    └── scheduler.py     ← Avtomatik xabarlar
```

---

## 👑 ADMIN BUYRUQLARI

Bot ichida:
- `/admin` — Admin panelni ochish

Admin paneldan:
- 📸 **Ovqat rasmi yuklash** — Har kun, har ovqat uchun rasm
- 📨 **Hammaga xabar** — Broadcast xabar yuborish  
- 👥 **Foydalanuvchilar** — Ro'yxat va statistika
- ✅ **Premium berish** — Foydalanuvchiga premium status

---

## 📸 OVQAT RASMI YUKLASH (Admin)

1. `/admin` → "📸 Ovqat rasmi yuklash"
2. Kun raqamini kiriting (1-30)
3. Ovqat raqamini kiriting (1-4 yoki 1-5)
4. Rasmni yuboring
5. Avtomatik saqlanadi!

Endi o'sha ovqatni bosganda **rasm + retsept** chiqadi! 🎉

---

## ⏰ AVTOMATIK ESLATMALAR

| Vaqt | Xabar |
|------|-------|
| 07:00 | ☀️ Ertalabki motivatsiya |
| 07:25 | 🌅 Nonushta eslatmasi |
| 10:25 | 🥜 2-Nonushta eslatmasi |
| 12:55 | 🍗 Tushlik eslatmasi |
| 16:25 | 🥗 Kechki oldi eslatmasi |
| 17:00 | 💪 Mashq eslatmasi |
| 10:00, 14:00, 16:00 | 💧 Suv eslatmasi |
| 21:00 | 🌙 Kunlik hisobot |

---

## 🔧 SERVER DA ISHLATISH (24/7)

### Variant 1: Screen
```bash
screen -S fitbot
python main.py
# Ctrl+A+D — fonga o'tkazish
```

### Variant 2: Systemd (tavsiya etiladi)
```bash
sudo nano /etc/systemd/system/fitbot.service
```

```ini
[Unit]
Description=Qayta Tugulish Fitness Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/qayta_tugulish_bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fitbot
sudo systemctl start fitbot
sudo systemctl status fitbot
```

---

## 🌐 HOSTING TAVSIYALARI

| Hosting | Narx | Tavsiya |
|---------|------|---------|
| **VPS (TimeWeb, Beget)** | $3-5/oy | ✅ Eng yaxshi |
| **Railway.app** | Bepul/$5 | ✅ Oson |
| **Render.com** | Bepul | ✅ Boshlash uchun |
| **Oracle Cloud** | Bepul | ✅ Doimiy bepul |

---

## 📞 YORDAM

Muammo bo'lsa: @farruxradjabov ga yozing

---

**🔥 QAYTA TUG'ILISH — Semizlikdan ozginlikka, bu yangi hayot!**
