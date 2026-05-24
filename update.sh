#!/bin/bash
# Botni yangilash skripti (VPS da ishlatish)
# Ishlatish: bash update.sh

BOT_DIR="/opt/qayta_tugulish_bot"
SERVICE_NAME="qayta_tugulish_bot"

echo "🔄 Bot yangilanmoqda..."

cd $BOT_DIR
git pull origin main
source venv/bin/activate
pip install -q -r requirements.txt

systemctl restart $SERVICE_NAME
sleep 2
systemctl status $SERVICE_NAME --no-pager

echo "✅ Yangilandi!"
