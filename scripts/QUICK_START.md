# 🚀 LINE Bot 快速開始指南

## 📋 核心指令

### 部署相關
```bash
# 完整部署（推薦首次使用）
./scripts/deploy_to_server.sh

# 快速部署（日常更新）
./scripts/quick_deploy.sh

# 設定開機自啟
sudo ./scripts/setup_systemd.sh
```

### 模型預熱
```bash
# 預熱模型（減少聊天等待時間）
python3 scripts/simple_warmup.py
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

1. **模型預熱失敗** → 檢查 Ollama 服務: `sudo systemctl status ollama`
2. **服務無法啟動** → 檢查日誌: `sudo journalctl -u line-bot.service`
3. **部署失敗** → 檢查依賴: `pip install -r mybot/requirements.txt`

## 📁 簡化後的腳本結構

```
scripts/
├── deploy_to_server.sh    # 完整部署腳本
├── quick_deploy.sh        # 快速部署腳本
├── setup_systemd.sh       # 服務設定腳本
├── simple_warmup.py       # 模型預熱腳本
├── README.md              # 詳細說明
└── QUICK_START.md         # 快速開始指南
```

## 💡 最佳實踐

1. **首次部署**: 使用 `deploy_to_server.sh`
2. **日常更新**: 使用 `quick_deploy.sh`
3. **部署後**: 執行 `warmup_models.py` 預熱模型
4. **遇到問題**: 檢查服務日誌和 Ollama 狀態

## 🎯 一鍵部署

```bash
# 完整流程
sudo ./scripts/setup_systemd.sh
./scripts/deploy_to_server.sh
python3 scripts/simple_warmup.py
```