#!/bin/bash
# ============================================
# Systemd Service 設定腳本
# ============================================
# 此腳本需要以 root 或 sudo 權限執行
# ============================================

set -e

# 設定顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 檢查是否為 root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 請使用 sudo 執行此腳本${NC}"
    echo "執行方式：sudo bash $0"
    exit 1
fi

echo "======================================"
echo "⚙️  Systemd Service 設定"
echo "======================================"

# ===== 設定變數 =====
SERVICE_USER="ruru1211-chatbot"
PROJECT_DIR="/home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/chatbot"
SERVICE_NAME="line-bot.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"

echo -e "${YELLOW}使用者：${NC}${SERVICE_USER}"
echo -e "${YELLOW}專案目錄：${NC}${PROJECT_DIR}"
echo -e "${YELLOW}Service 檔案：${NC}${SERVICE_FILE}"
echo ""

# ===== 檢查專案目錄 =====
if [ ! -d "${PROJECT_DIR}" ]; then
    echo -e "${RED}❌ 專案目錄不存在：${PROJECT_DIR}${NC}"
    exit 1
fi

# ===== 檢查使用者 =====
if ! id "${SERVICE_USER}" &>/dev/null; then
    echo -e "${RED}❌ 使用者不存在：${SERVICE_USER}${NC}"
    exit 1
fi

# ===== 檢查虛擬環境 =====
if [ ! -d "${PROJECT_DIR}/venv" ]; then
    echo -e "${YELLOW}⚠️  虛擬環境不存在，建立中...${NC}"
    sudo -u ${SERVICE_USER} python3 -m venv ${PROJECT_DIR}/venv
    sudo -u ${SERVICE_USER} ${PROJECT_DIR}/venv/bin/pip install -r ${PROJECT_DIR}/mybot/requirements.txt
    sudo -u ${SERVICE_USER} ${PROJECT_DIR}/venv/bin/pip install gunicorn
fi

# ===== 建立日誌目錄 =====
LOG_DIR="/home/ruru1211-chatbot/logs"
if [ ! -d "${LOG_DIR}" ]; then
    echo -e "${YELLOW}建立日誌目錄...${NC}"
    mkdir -p ${LOG_DIR}
    chown ${SERVICE_USER}:${SERVICE_USER} ${LOG_DIR}
fi

# ===== 建立 Systemd Service 檔案 =====
echo -e "${YELLOW}建立 Systemd Service 檔案...${NC}"

cat > ${SERVICE_FILE} << 'EOF'
[Unit]
Description=LINE Bot - Pet Chatbot Service
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=notify
User=ruru1211-chatbot
Group=ruru1211-chatbot
WorkingDirectory=/home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/chatbot

# 環境變數
Environment="PATH=/home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/chatbot/venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/chatbot/.env

# Gunicorn 啟動指令
ExecStart=/home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/chatbot/venv/bin/gunicorn \
  --bind 127.0.0.1:8090 \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --access-logfile /home/ruru1211-chatbot/logs/access.log \
  --error-logfile /home/ruru1211-chatbot/logs/error.log \
  --log-level info \
  mybot.app:app

# 重啟策略
Restart=always
RestartSec=10

# 安全性設定
NoNewPrivileges=true
PrivateTmp=true

# 日誌輸出
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service 檔案已建立${NC}"

# ===== 重新載入 Systemd =====
echo -e "${YELLOW}重新載入 Systemd...${NC}"
systemctl daemon-reload

# ===== 啟用服務 =====
echo -e "${YELLOW}啟用服務（開機自動啟動）...${NC}"
systemctl enable ${SERVICE_NAME}

# ===== 檢查 .env 檔案 =====
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    echo -e "${YELLOW}⚠️  .env 檔案不存在${NC}"
    echo "請建立 .env 檔案並填入必要的環境變數"
    echo "  1. 複製範例檔案：cp ${PROJECT_DIR}/.env.example ${PROJECT_DIR}/.env"
    echo "  2. 編輯設定：nano ${PROJECT_DIR}/.env"
    echo "  3. 啟動服務：systemctl start ${SERVICE_NAME}"
    exit 0
fi

# ===== 詢問是否立即啟動 =====
echo ""
read -p "是否立即啟動服務？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}啟動服務...${NC}"
    systemctl start ${SERVICE_NAME}
    
    sleep 2
    
    echo ""
    echo -e "${GREEN}✅ 服務狀態：${NC}"
    systemctl status ${SERVICE_NAME} --no-pager
fi

echo ""
echo "======================================"
echo "✅ Systemd Service 設定完成！"
echo "======================================"
echo ""
echo "常用指令："
echo "  啟動服務：sudo systemctl start ${SERVICE_NAME}"
echo "  停止服務：sudo systemctl stop ${SERVICE_NAME}"
echo "  重啟服務：sudo systemctl restart ${SERVICE_NAME}"
echo "  查看狀態：sudo systemctl status ${SERVICE_NAME}"
echo "  查看日誌：sudo journalctl -u ${SERVICE_NAME} -f"
echo ""

