# 🐕 寵物聊天機器人 - LINE Bot

一個透過 LINE Messaging API 與虛擬寵物對話的智能聊天機器人，使用 Ollama + Qwen 模型實現寵物擬人化對話。

## ✨ 功能特色

- 🎭 **擬人化對話**：寵物會用可愛的語氣和主人聊天
- 💾 **記憶功能**：記住每個使用者的對話內容（8-10 輪）
- 📖 **生命故事**：從資料庫讀取寵物的生命軌跡和回憶
- 🎨 **多種性格**：支援陽光型、吃貨型、傲嬌型、隨和型、宅宅型
- 🇹🇼 **繁體中文**：自動將模型輸出轉換為繁體中文
- 👥 **多使用者支援**：每個 LINE 使用者都有獨立的對話歷史
- 🔄 **LINE SDK v3**：使用最新版本的 LINE Bot SDK

## 🚀 快速開始

### 1. 環境需求

- Python 3.8+
- MySQL 資料庫
- [Ollama](https://ollama.ai) 與 `qwen:7b` 模型
- LINE Bot 帳號

### 2. 安裝依賴

```bash
# 進入專案目錄
cd line_bot

# 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安裝 Python 套件
pip install -r requirements.txt

# 安裝 Ollama 模型
ollama pull qwen:7b
```

### 3. 設定環境變數

編輯 `.env` 檔案，填入你的設定：

```env
# LINE Bot 憑證（必須）
LINE_CHANNEL_ACCESS_TOKEN=你的_channel_access_token
LINE_CHANNEL_SECRET=你的_channel_secret

# 資料庫設定（必須）
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=lbblacktech-laravel

# 寵物設定（可選）
PET_ID=1
OLLAMA_MODEL=qwen:7b

# Flask 設定（可選）
PORT=8000
```

### 4. 啟動應用

```bash
python app.py
```

### 5. 使用 ngrok 暴露到公網

開啟新的終端機視窗：

```bash
ngrok http 8000
```

複製 ngrok 提供的 HTTPS 網址（例如：`https://abc123.ngrok.io`）

### 6. 設定 LINE Webhook

1. 回到 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇你的 Channel
3. 前往 **Messaging API** 頁面
4. 在 **Webhook settings** 中：
   - 設定 Webhook URL：`https://你的ngrok網址.ngrok.io/webhook`
   - 啟用 **Use webhook**
   - 點擊 **Verify** 測試連線（應該顯示成功）

### 7. 開始使用

1. 掃描 QR Code 加入 Bot 好友
2. 開始與寵物聊天！

## 💬 使用範例

### 基本對話

```
使用者: 嚕比，你好嗎？
寵物: 汪汪～主人！我很好呀！看到你我超開心的！嘿嘿～

使用者: 今天想做什麼？
寵物: 想和主人一起去公園玩！可以嗎可以嗎？汪～
```

### 特殊指令

| 指令 | 功能 |
|------|------|
| `清除` 或 `clear` 或 `重置` | 清除對話歷史 |
| `說明` 或 `help` 或 `幫助` | 顯示使用說明 |

## 📁 專案結構

```
line_bot/
├── app.py                     # 主程式（LINE Bot 應用）⭐
├── chatbot_ollama.py          # 對話引擎
├── db_utils.py                # 資料庫工具
├── config.py                  # 資料庫配置
├── personalities.py           # 性格模板
├── requirements.txt           # Python 套件清單
├── .env                       # 環境變數
├── .gitignore                 # Git 忽略規則
├── README.md                  # 本說明文件
└── venv/                      # 虛擬環境
```

## 🎨 性格類型

在 `personalities.py` 中定義了 5 種寵物性格：

- **陽光型 (sunny)**：活潑開朗，喜歡戶外活動
- **吃貨型 (foodie)**：對食物充滿熱情，常常撒嬌求吃
- **傲嬌型 (tsundere)**：外冷內熱，偶爾逗主人
- **隨和型 (easygoing)**：溫柔穩重，陪伴型（預設）
- **宅宅型 (otaku)**：喜歡待在家裡，黏人

## 🗄️ 資料庫結構

專案需要以下三個資料表：

### pets 表
```sql
- pet_id (主鍵)
- pet_name (寵物名字)
- slogan (主人的愛意表達)
```

### timeline_events 表
```sql
- pet_id (外鍵)
- age (年齡/時期)
- event_title (事件標題)
- event_description (事件描述)
- is_visible (是否顯示)
- display_order (顯示順序)
```

### letters 表
```sql
- pet_id (外鍵)
- letter_content (信件內容)
```

## 🔧 進階設定

### 更改寵物 ID

在 `.env` 檔案中設定：

```env
PET_ID=2  # 改為你想要的寵物 ID
```

### 更改 AI 模型

在 `.env` 檔案中設定：

```env
OLLAMA_MODEL=llama2  # 改為其他 Ollama 模型
```

### 調整對話歷史長度

編輯 `app.py`，找到 `process_user_message()` 函數：

```python
# 限制歷史記錄長度
if len(user_chat_history[user_id]) > 10:  # 最大歷史輪數
    user_chat_history[user_id] = user_chat_history[user_id][-8:]  # 保留輪數
```

## 🐛 故障排除

### 問題 1：LINE Bot 沒有回覆

**檢查清單：**
```bash
# 1. Flask 是否運行？
curl http://localhost:8000/

# 2. ngrok 是否運行？
curl https://你的ngrok網址.ngrok.io/

# 3. Ollama 是否運行？
ollama list

# 4. 資料庫是否連接？
curl http://localhost:8000/test
```

### 問題 2：簽名驗證失敗

```
錯誤: Invalid signature
```

**解決方法：**
- 確認 `.env` 中的 `LINE_CHANNEL_SECRET` 與 LINE Console 完全一致
- 重新啟動 Flask 應用

### 問題 3：無法載入寵物資料

```
❌ 無法載入寵物資料
```

**解決方法：**
1. 確認 MySQL 服務正在運行
2. 檢查 `.env` 中的資料庫設定是否正確
3. 確認資料庫中有對應 `pet_id` 的資料
4. 查看 Flask 日誌了解詳細錯誤

### 問題 4：Ollama 連接失敗

```
錯誤: Connection refused
```

**解決方法：**
1. 確認 Ollama 服務正在運行：`ollama list`
2. 確認已下載 qwen:7b 模型：`ollama pull qwen:7b`
3. 檢查 Ollama 是否運行在預設埠口（11434）

### 問題 5：Port 5000 已被占用

在 macOS 上，AirPlay Receiver 預設使用 port 5000。

**解決方法：**
- 在 `.env` 中將 `PORT` 改為 8000
- 或關閉 AirPlay Receiver：系統偏好設定 → 一般 → AirDrop 與接力

## 📊 API 端點

### 公開端點

- `GET /` - 健康檢查
- `GET /test` - 測試寵物資料載入
- `POST /webhook` - LINE Webhook 回調

## 🚀 生產環境部署

### 建議事項

1. **使用固定網址**
   - 申請網域並設定 DNS
   - 使用 SSL 憑證（Let's Encrypt）

2. **使用 Gunicorn 運行 Flask**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. **使用 Redis 儲存對話歷史**
   - 避免記憶體洩漏
   - 支援多伺服器部署

4. **設定監控與日誌**
   - 使用 logging 模組
   - 設定錯誤通知

## 📝 技術棧

- **後端框架**: Flask 3.1.2
- **LINE SDK**: line-bot-sdk 3.19.1 (v3)
- **AI 模型**: Ollama + Qwen 7B
- **資料庫**: MySQL (via PyMySQL)
- **中文處理**: OpenCC (簡繁轉換)

## 📄 授權

本專案僅供個人學習和研究使用。

## 🙏 致謝

- [Ollama](https://ollama.ai) - 本地 LLM 運行環境
- [Qwen](https://github.com/QwenLM/Qwen) - 阿里巴巴開源的中文語言模型
- [OpenCC](https://github.com/BYVoid/OpenCC) - 中文簡繁轉換工具
- [LINE Messaging API](https://developers.line.biz/) - LINE 官方 API

---

**享受與你的虛擬寵物在 LINE 上聊天的時光！🐾**
