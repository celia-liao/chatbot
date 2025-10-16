# 🚀 快速啟動指南

## 📋 前置準備檢查清單

在啟動之前，請確認你已完成：

- [ ] 安裝 Python 3.8+
- [ ] 安裝 MySQL 資料庫
- [ ] 安裝並啟動 Ollama
- [ ] 下載 Qwen 7B 模型：`ollama pull qwen:7b`
- [ ] 建立 LINE Bot Channel 並取得憑證
- [ ] 準備好資料庫及寵物資料

## ⚡ 三步驟快速啟動

### 步驟 1：設定環境變數

編輯 `.env` 檔案，填入你的資訊：

```bash
# LINE Bot 憑證
LINE_CHANNEL_ACCESS_TOKEN=你的token
LINE_CHANNEL_SECRET=你的secret

# 資料庫設定
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=你的密碼
DB_NAME=你的資料庫名稱

# 寵物設定
PET_ID=1
```

### 步驟 2：啟動應用

```bash
# 啟動虛擬環境
source venv/bin/activate

# 執行應用
python app.py
```

你應該會看到：

```
==================================================
🐕 寵物聊天機器人 - LINE Bot (SDK v3)
==================================================

📋 環境設定檢查：
✅ LINE Channel Access Token 已設定
✅ LINE Channel Secret 已設定
✅ 寵物資料已載入：嚕比

🤖 使用的 AI 模型：qwen:7b
🐕 寵物 ID：1

🚀 啟動 Flask 伺服器於埠號 8000...
```

### 步驟 3：設定 Webhook

在**另一個終端機視窗**執行：

```bash
ngrok http 8000
```

複製 ngrok 提供的 HTTPS 網址，然後：

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇你的 Channel → Messaging API
3. 設定 Webhook URL：`https://你的ngrok網址.ngrok.io/webhook`
4. 啟用 "Use webhook"
5. 點擊 "Verify" 驗證

## ✅ 測試確認

### 測試 1：檢查服務運行

```bash
curl http://localhost:8000/
# 應該回傳：🐕 寵物聊天機器人 LINE Bot 正在運行中！
```

### 測試 2：檢查寵物資料

```bash
curl http://localhost:8000/test
# 應該回傳：✅ 寵物聊天機器人已就緒！寵物名稱：嚕比
```

### 測試 3：掃描 QR Code 加入好友

在 LINE Developers Console 掃描 QR Code，然後傳送訊息測試！

## 🎯 基本使用

傳送訊息給 Bot：

- **一般對話**：直接輸入任何訊息，寵物會回覆
- **清除歷史**：輸入 `清除` 或 `clear`
- **查看說明**：輸入 `說明` 或 `help`

## 🐛 常見問題

### Q1: Bot 沒有回覆？

檢查以下項目：
1. Flask 是否正常運行？
2. ngrok 是否正常運行？
3. Webhook URL 是否設定正確？
4. LINE Console 中是否啟用了 webhook？

### Q2: 無法載入寵物資料？

檢查：
1. MySQL 是否運行？
2. 資料庫連線設定是否正確？
3. 資料庫中是否有對應 PET_ID 的資料？

### Q3: Ollama 連接失敗？

檢查：
1. Ollama 服務是否運行：`ollama list`
2. 是否已下載模型：`ollama pull qwen:7b`

## 📝 重要提醒

1. **ngrok 網址會變**：每次重啟 ngrok 都需要更新 LINE Webhook URL
2. **資料庫連線**：確保 MySQL 服務持續運行
3. **Ollama 服務**：確保 Ollama 服務持續運行
4. **虛擬環境**：每次使用前記得啟動虛擬環境

## 🎉 成功！

如果一切順利，你現在應該可以在 LINE 上與你的虛擬寵物聊天了！

有問題嗎？查看完整的 [README.md](README.md) 了解更多細節。

