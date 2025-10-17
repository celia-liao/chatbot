#!/bin/bash
# ============================================
# LINE Bot 啟動腳本（使用 Gunicorn）
# ============================================

# 設定顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================"
echo "🐕 LINE Bot 啟動腳本"
echo "======================================"

# 取得腳本所在目錄的上層目錄（專案根目錄）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}專案目錄：${NC}$PROJECT_DIR"

# 切換到專案目錄
cd "$PROJECT_DIR" || exit 1

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 虛擬環境不存在！${NC}"
    echo "請先執行：python3 -m venv venv"
    exit 1
fi

# 啟動虛擬環境
echo -e "${YELLOW}啟動虛擬環境...${NC}"
source venv/bin/activate

# 檢查 .env 檔案
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 檔案不存在！${NC}"
    echo "請複製 .env.example 並填入正確的設定："
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# 載入環境變數
export $(grep -v '^#' .env | xargs)

# 設定預設 Port
PORT=${PORT:-8090}

echo -e "${YELLOW}檢查依賴套件...${NC}"
if ! command -v gunicorn &> /dev/null; then
    echo -e "${RED}❌ Gunicorn 未安裝！${NC}"
    echo "正在安裝 gunicorn..."
    pip install gunicorn
fi

# 建立日誌目錄
LOG_DIR="$PROJECT_DIR/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}建立日誌目錄：${NC}$LOG_DIR"
    mkdir -p "$LOG_DIR"
fi

# 啟動 Gunicorn
echo -e "${GREEN}✅ 啟動 Gunicorn...${NC}"
echo -e "${YELLOW}綁定地址：${NC}127.0.0.1:$PORT"
echo -e "${YELLOW}日誌目錄：${NC}$LOG_DIR"
echo ""
echo "按 Ctrl+C 停止服務"
echo "======================================"
echo ""

exec gunicorn \
  --bind 127.0.0.1:$PORT \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --access-logfile "$LOG_DIR/access.log" \
  --error-logfile "$LOG_DIR/error.log" \
  --log-level info \
  --chdir "$PROJECT_DIR" \
  mybot.app:app

