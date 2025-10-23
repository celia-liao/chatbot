#!/bin/bash
# ============================================
# LINE Bot 部署腳本（在伺服器上執行）
# ============================================
# 使用方式：在伺服器上直接執行此腳本
# bash /home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/scripts/deploy_to_server.sh
# ============================================

set -e  # 遇到錯誤立即停止

# 設定顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===== 部署設定 =====
PROJECT_DIR="/home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/chatbot"
SERVICE_NAME="line-bot.service"

echo "======================================"
echo "🚀 LINE Bot 部署腳本（伺服器版）"
echo "======================================"

# 函數：印出訊息
print_step() {
    echo -e "${BLUE}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ===== 步驟 1: 檢查專案目錄 =====
print_step "檢查專案目錄..."
if [ ! -d "${PROJECT_DIR}" ]; then
    print_error "專案目錄不存在：${PROJECT_DIR}"
    exit 1
fi
print_success "專案目錄確認"

# ===== 步驟 2: 切換到專案目錄 =====
cd ${PROJECT_DIR}
print_success "已切換到專案目錄"

# ===== 步驟 3: 備份 .env 檔案（如果存在）=====
if [ -f ".env" ]; then
    print_step "備份 .env 檔案..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    print_success ".env 已備份"
fi

# ===== 步驟 4: 拉取最新程式碼 =====
print_step "從 Git 拉取最新程式碼..."

# 檢查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    print_warning "偵測到未提交的更改，暫存中..."
    git stash
    HAS_STASH=true
else
    HAS_STASH=false
fi

# 拉取最新程式碼
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_step "當前分支：${CURRENT_BRANCH}"

git pull origin ${CURRENT_BRANCH}
print_success "程式碼已更新"

# 恢復暫存的更改（如果有）
if [ "$HAS_STASH" = true ]; then
    print_step "恢復暫存的更改..."
    git stash pop || print_warning "無法自動恢復暫存，請手動檢查"
fi

# ===== 步驟 5: 檢查虛擬環境 =====
print_step "檢查虛擬環境..."
if [ ! -d "venv" ]; then
    print_warning "虛擬環境不存在，建立中..."
    python3 -m venv venv
    print_success "虛擬環境已建立"
fi

# ===== 步驟 6: 安裝/更新依賴 =====
print_step "更新依賴套件..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r mybot/requirements.txt -q
pip install gunicorn -q
print_success "依賴套件已更新"

# ===== 步驟 7: 檢查 .env 檔案 =====
print_step "檢查 .env 檔案..."
if [ ! -f ".env" ]; then
    print_warning ".env 檔案不存在"
    if [ -f "docs/env_template.txt" ]; then
        print_step "建立 .env 範本..."
        cp docs/env_template.txt .env
        print_warning "請編輯 .env 檔案並填入正確的設定："
        echo "  nano ${PROJECT_DIR}/.env"
        echo ""
        echo "填入後執行："
        echo "  sudo systemctl restart ${SERVICE_NAME}"
        exit 0
    else
        print_error ".env 範本不存在，無法建立"
        exit 1
    fi
else
    print_success ".env 檔案存在"
fi

# ===== 步驟 8: 建立日誌目錄 =====
LOG_DIR="/home/ruru1211-chatbot/logs"
if [ ! -d "${LOG_DIR}" ]; then
    print_step "建立日誌目錄..."
    mkdir -p ${LOG_DIR}
    print_success "日誌目錄已建立"
fi

# ===== 步驟 9: 預熱 AI 模型 =====
print_step "預熱 AI 模型..."
if [ -f "scripts/warmup_models.py" ]; then
    python3 scripts/warmup_models.py
    print_success "模型預熱完成"
else
    print_warning "模型預熱腳本不存在，跳過預熱"
fi

# ===== 步驟 10: 檢查並重啟服務 =====
print_step "檢查服務狀態..."
if systemctl is-active --quiet ${SERVICE_NAME}; then
    print_step "重啟 ${SERVICE_NAME}..."
    sudo systemctl restart ${SERVICE_NAME}
    sleep 3
    
    # 檢查服務是否成功啟動
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_success "服務重啟成功"
        echo ""
        sudo systemctl status ${SERVICE_NAME} --no-pager -l
    else
        print_error "服務重啟失敗"
        echo ""
        echo "查看錯誤日誌："
        echo "  sudo journalctl -u ${SERVICE_NAME} -n 50"
        exit 1
    fi
else
    print_warning "${SERVICE_NAME} 未運行"
    echo ""
    echo "如果尚未設定 systemd service，請執行："
    echo "  sudo bash ${PROJECT_DIR}/scripts/setup_systemd.sh"
fi

# ===== 步驟 10: 測試服務 =====
print_step "測試服務..."
sleep 2

# 測試本地端點
if curl -s -f http://127.0.0.1:8090/healthz > /dev/null 2>&1; then
    print_success "本地 Health Check 通過"
else
    print_warning "本地 Health Check 未通過"
fi

# 測試遠端端點
if curl -s -f https://chatbot.ruru1211.xyz/line/healthz > /dev/null 2>&1; then
    print_success "遠端 Health Check 通過"
else
    print_warning "遠端 Health Check 未通過（檢查 Nginx 設定）"
fi

echo ""
echo "======================================"
echo "🎉 部署完成！"
echo "======================================"
echo ""
echo "檢查清單："
echo "  ✅ 程式碼已更新"
echo "  ✅ 依賴已安裝"
echo "  ✅ 服務已重啟"
echo ""
echo "常用指令："
echo "  查看服務狀態：sudo systemctl status ${SERVICE_NAME}"
echo "  查看即時日誌：sudo journalctl -u ${SERVICE_NAME} -f"
echo "  查看錯誤日誌：tail -f ${LOG_DIR}/error.log"
echo "  測試健康檢查：curl http://127.0.0.1:8090/healthz"
echo ""
echo "如有問題，請檢查日誌。"
echo ""

