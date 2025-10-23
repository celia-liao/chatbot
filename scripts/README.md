# LINE Bot 腳本說明文檔

本目錄包含 LINE Bot 專案的核心腳本，專注於部署和模型預熱功能。

## 📁 腳本結構

### 🚀 部署腳本

#### `deploy_to_server.sh`
**用途**: 完整的部署腳本，包含所有部署流程
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

#### `setup_systemd.sh`
**用途**: 設定 systemd 服務，讓 LINE Bot 開機自動啟動
**功能**:
- 創建 systemd 服務檔案
- 設定服務權限
- 啟用開機自啟
**使用方式**: `sudo ./scripts/setup_systemd.sh`

### 🔥 模型預熱腳本

#### `warmup_models.py`
**用途**: 預熱 AI 模型，減少聊天等待時間
**功能**:
- 自動檢測 AI 模式（Ollama）
- 預先載入模型
- 測試模型回應
- 簡化版錯誤處理
**使用方式**: `python3 scripts/warmup_models.py`

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

### 檢查服務狀態
```bash
sudo systemctl status line-bot.service
sudo journalctl -u line-bot.service -f
```

### 檢查 Ollama 服務
```bash
ollama list
sudo systemctl status ollama
```

## 📋 腳本執行權限

確保所有腳本都有執行權限：
```bash
chmod +x scripts/*.sh
```

## 🔍 日誌檔案位置

- **應用程式日誌**: `logs/app.log`
- **系統服務日誌**: `sudo journalctl -u line-bot.service`
- **Ollama 日誌**: `sudo journalctl -u ollama`

## 💡 使用建議

1. **首次部署**: 使用 `deploy_to_server.sh`
2. **日常更新**: 使用 `quick_deploy.sh`
3. **模型預熱**: 部署後執行 `warmup_models.py` 可大幅減少聊天等待時間

## 🆘 常見問題

### 模型預熱失敗
- 檢查 Ollama 服務: `sudo systemctl status ollama`
- 重啟 Ollama: `sudo systemctl restart ollama`
- 檢查模型: `ollama list`

### 服務無法啟動
- 檢查日誌: `sudo journalctl -u line-bot.service`
- 檢查權限和配置
- 確認環境變數設定

### 部署失敗
- 檢查網路連接
- 確認依賴安裝: `pip install -r mybot/requirements.txt`
- 檢查資料庫連接