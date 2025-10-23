# 🚀 LINE Bot 快速開始指南

## 📋 常用指令

### 部署相關
```bash
# 完整部署（推薦首次使用）
./scripts/deploy_to_server.sh

# 快速部署（日常更新）
./scripts/quick_deploy.sh

# 設定開機自啟
sudo ./scripts/setup_systemd.sh
```

### 診斷相關
```bash
# 檢查資料庫
python3 scripts/test_db_connection.py

# 檢查 AI 模式
python3 scripts/check_ai_mode.py

# 測試完整流程
python3 scripts/test_message_flow.py
```

### 模型預熱
```bash
# 預熱模型（減少聊天等待時間）
python3 scripts/warmup_models.py
```

### 服務管理
```bash
# 檢查服務狀態
sudo systemctl status line-bot.service

# 重啟服務
sudo systemctl restart line-bot.service

# 查看日誌
sudo journalctl -u line-bot.service -f
```

## 🔧 故障排除

1. **資料庫問題** → 執行 `test_db_connection.py`
2. **AI 模型問題** → 執行 `check_ai_mode.py`
3. **服務無法啟動** → 檢查日誌 `journalctl -u line-bot.service`
4. **聊天等待太久** → 執行 `warmup_models.py`

## 📁 檔案結構

```
scripts/
├── deploy_to_server.sh    # 主要部署腳本
├── quick_deploy.sh        # 快速部署
├── setup_systemd.sh       # 服務設定
├── start_gunicorn.sh      # Gunicorn 啟動
├── warmup_models.py       # 模型預熱
├── check_ai_mode.py       # AI 模式檢查
├── test_db_connection.py  # 資料庫測試
├── test_message_flow.py   # 流程測試
├── debug_ai_mode.py       # AI 診斷
└── README.md              # 詳細說明
```

## 💡 最佳實踐

1. **首次部署**: 使用 `deploy_to_server.sh`
2. **日常更新**: 使用 `quick_deploy.sh`
3. **部署後**: 執行 `warmup_models.py` 預熱模型
4. **遇到問題**: 先執行對應的診斷腳本
