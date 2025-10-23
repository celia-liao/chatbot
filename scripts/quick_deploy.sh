#!/bin/bash
# ============================================
# 快速部署腳本 - 包含模型預熱
# ============================================

set -e

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 檢查是否在正確的目錄
if [ ! -f "mybot/app.py" ] && [ ! -f "../mybot/app.py" ]; then
    echo "❌ 請在專案根目錄執行此腳本"
    echo "💡 正確的執行方式："
    echo "   cd /home/ruru1211-chatbot/htdocs/chatbot.ruru1211.xyz/chatbot/"
    echo "   ./scripts/quick_deploy.sh"
    exit 1
fi

# 如果在 scripts 目錄中執行，切換到上層目錄
if [ -f "../mybot/app.py" ]; then
    cd ..
fi

log_info "🚀 開始快速部署..."

# 1. 停止現有服務
log_info "🛑 停止現有服務..."
sudo systemctl stop line-bot.service 2>/dev/null || true

# 2. 安裝依賴
log_info "📦 安裝依賴..."
pip install -r mybot/requirements.txt

# 3. 預熱模型
log_info "🔥 預熱 AI 模型..."
python3 scripts/warmup_models.py
if [ $? -ne 0 ]; then
    log_warning "模型預熱失敗，但繼續部署"
fi

# 4. 啟動服務
log_info "🔄 啟動服務..."
sudo systemctl start line-bot.service

# 5. 檢查狀態
sleep 3
if systemctl is-active --quiet line-bot.service; then
    log_success "✅ 服務啟動成功"
    log_info "📊 監控日誌: sudo journalctl -u line-bot.service -f"
else
    log_warning "❌ 服務啟動失敗，檢查日誌:"
    sudo journalctl -u line-bot.service --since "1 minute ago"
fi

log_success "🎉 部署完成！"
