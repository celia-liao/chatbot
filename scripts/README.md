# LINE Bot 腳本說明文檔

本目錄包含 LINE Bot 專案的所有腳本和工具，用於部署、維護和診斷。

## 📁 腳本分類

### 🚀 部署腳本

#### `deploy_to_server.sh`
**用途**: 主要的部署腳本，包含完整的部署流程
**功能**:
- 更新程式碼
- 安裝/更新依賴
- 檢查環境配置
- 預熱 AI 模型
- 重啟服務
**使用方式**: `./scripts/deploy_to_server.sh`

#### `quick_deploy.sh`
**用途**: 快速部署腳本，簡化版部署流程
**功能**:
- 快速安裝依賴
- 預熱模型
- 重啟服務
**使用方式**: `./scripts/quick_deploy.sh`

#### `start_gunicorn.sh`
**用途**: 使用 Gunicorn 啟動 LINE Bot 服務
**功能**:
- 檢查虛擬環境
- 啟動 Gunicorn 服務
- 設定工作進程
**使用方式**: `./scripts/start_gunicorn.sh`

#### `setup_systemd.sh`
**用途**: 設定 systemd 服務，讓 LINE Bot 開機自動啟動
**功能**:
- 創建 systemd 服務檔案
- 設定服務權限
- 啟用開機自啟
**使用方式**: `sudo ./scripts/setup_systemd.sh`

### 🔧 維護腳本

#### `warmup_models.py`
**用途**: 預熱 AI 模型，減少聊天等待時間
**功能**:
- 自動檢測 AI 模式（API 或 Ollama）
- 預先載入模型
- 測試模型回應
**使用方式**: `python3 scripts/warmup_models.py`

#### `check_ai_mode.py`
**用途**: 檢查 AI 模式設定和相關配置
**功能**:
- 檢查環境變數
- 驗證 AI 模式設定
- 測試模型連接
**使用方式**: `python3 scripts/check_ai_mode.py`

### 🔍 診斷腳本

#### `test_db_connection.py`
**用途**: 測試資料庫連接和基本功能
**功能**:
- 檢查資料庫連接
- 驗證表結構
- 測試儲存功能
- 顯示現有記錄
**使用方式**: `python3 scripts/test_db_connection.py`

#### `test_message_flow.py`
**用途**: 測試完整的訊息處理流程
**功能**:
- 測試寵物 ID 查詢
- 測試訊息儲存
- 測試對話歷史讀取
- 模擬 LINE Bot 流程
**使用方式**: `python3 scripts/test_message_flow.py`

#### `debug_ai_mode.py`
**用途**: AI 模式診斷工具
**功能**:
- 檢查 AI 模式設定
- 測試模型匯入
- 驗證 AI 功能
- 檢查服務日誌
**使用方式**: `python3 scripts/debug_ai_mode.py`

## 🚀 常用部署流程

### 首次部署
```bash
# 1. 設定 systemd 服務
sudo ./scripts/setup_systemd.sh

# 2. 完整部署
./scripts/deploy_to_server.sh
```

### 日常更新
```bash
# 快速部署（推薦）
./scripts/quick_deploy.sh
```

### 手動預熱模型
```bash
python3 scripts/warmup_models.py
```

## 🔧 故障排除

### 檢查資料庫
```bash
python3 scripts/test_db_connection.py
```

### 檢查 AI 模式
```bash
python3 scripts/check_ai_mode.py
```

### 檢查完整流程
```bash
python3 scripts/test_message_flow.py
```

### 檢查服務狀態
```bash
sudo systemctl status line-bot.service
sudo journalctl -u line-bot.service -f
```

## 📋 腳本執行權限

確保所有腳本都有執行權限：
```bash
chmod +x scripts/*.sh
```

## 🔍 日誌檔案位置

- **應用程式日誌**: `logs/app.log`
- **系統服務日誌**: `sudo journalctl -u line-bot.service`
- **Gunicorn 日誌**: `logs/gunicorn.log`

## 💡 使用建議

1. **首次部署**: 使用 `deploy_to_server.sh`
2. **日常更新**: 使用 `quick_deploy.sh`
3. **故障排除**: 先執行診斷腳本找出問題
4. **模型預熱**: 部署後執行 `warmup_models.py` 可大幅減少聊天等待時間

## 🆘 常見問題

### 資料庫連接失敗
- 檢查 `.env` 檔案中的資料庫配置
- 執行 `test_db_connection.py` 診斷

### AI 模型無法載入
- 執行 `check_ai_mode.py` 檢查設定
- 執行 `warmup_models.py` 預熱模型

### 服務無法啟動
- 檢查日誌: `sudo journalctl -u line-bot.service`
- 檢查權限和配置
