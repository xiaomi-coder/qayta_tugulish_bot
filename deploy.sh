#!/bin/bash
# VPS ga birinchi marta o'rnatish skripti (Ubuntu 20.04/22.04)
# Ishlatish: bash deploy.sh

set -e

BOT_DIR="/opt/qayta_tugulish_bot"
SERVICE_NAME="qayta_tugulish_bot"
REPO_URL="https://github.com/xiaomi-coder/qayta_tugulish_bot.git"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  QAYTA TUG'ILISH BOT - DEPLOY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Tizimni yangilash
echo "[1/7] Tizim yangilanmoqda..."
apt-get update -q && apt-get install -y -q python3 python3-pip python3-venv git

# 2. Bot papkasini yaratish
echo "[2/7] Papka tayyorlanmoqda..."
mkdir -p $BOT_DIR
cd $BOT_DIR

# 3. Kodni clone qilish
echo "[3/7] Kod yuklanmoqda..."
if [ -d ".git" ]; then
    git pull origin main
else
    git clone $REPO_URL .
fi

# 4. Virtual environment
echo "[4/7] Python venv yaratilmoqda..."
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 5. .env fayl tekshirish
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env fayl topilmadi!"
    echo "    cp .env.example .env"
    echo "    nano .env  # BOT_TOKEN va ADMIN_IDS ni kiriting"
    echo ""
    cp .env.example .env
fi

# 6. Systemd service yaratish
echo "[5/7] Systemd service yaratilmoqda..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Qayta Tug'ilish Fitness Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=${BOT_DIR}
ExecStart=${BOT_DIR}/venv/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
EnvironmentFile=${BOT_DIR}/.env

[Install]
WantedBy=multi-user.target
EOF

# 7. Serviceni yoqish
echo "[6/7] Service yoqilmoqda..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ O'RNATISH TUGADI!"
echo ""
echo "KEYINGI QADAMLAR:"
echo "  1. nano /opt/qayta_tugulish_bot/.env"
echo "     BOT_TOKEN va ADMIN_IDS ni kiriting"
echo ""
echo "  2. systemctl start $SERVICE_NAME"
echo "     (botni ishga tushurish)"
echo ""
echo "  3. systemctl status $SERVICE_NAME"
echo "     (holat ko'rish)"
echo ""
echo "  4. journalctl -u $SERVICE_NAME -f"
echo "     (log ko'rish)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
