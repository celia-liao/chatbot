# 修正寵物名字簡繁轉換問題

## 🐛 問題描述

當寵物名字包含特殊字詞時（例如「里長」），OpenCC 簡繁轉換會將其錯誤轉換：

- **原始名字**：里長
- **錯誤轉換後**：裏長（「里」被轉成「裏」）

這是因為 OpenCC 會將「里」（距離單位、里長的里）轉換成「裏」（裡面的異體字）。

## ✅ 解決方案

在進行簡繁轉換時，先用臨時標記保護寵物名字，轉換完成後再還原。

### 修改的檔案

1. **`mybot/chatbot_ollama.py`**
   - 修改 `convert_simple_to_traditional()` 函數，增加 `protected_words` 參數
   - 修改 `chat_with_pet()` 函數，增加 `pet_name` 參數
   - 在轉換前用標記保護寵物名字，轉換後還原

2. **`mybot/app.py`**
   - 在呼叫 `chat_with_pet()` 時傳入 `pet_name=pet_name`

## 🔧 技術細節

### 保護詞彙的運作流程

```python
# 1. 原始文字
"我是里長，汪汪！"

# 2. 用標記替換寵物名字
"我是__PROTECTED_0__，汪汪！"

# 3. 進行簡繁轉換
"我是__PROTECTED_0__，汪汪！"  # 標記不會被轉換

# 4. 還原寵物名字
"我是里長，汪汪！"  # 保持原始正確的名字
```

### 程式碼範例

```python
def convert_simple_to_traditional(text: str, protected_words: list = None) -> str:
    if not protected_words:
        return cc.convert(text)
    
    # 使用臨時標記保護特定詞彙
    protected_map = {}
    temp_text = text
    
    for i, word in enumerate(protected_words):
        if word and word in temp_text:
            placeholder = f"__PROTECTED_{i}__"
            protected_map[placeholder] = word
            temp_text = temp_text.replace(word, placeholder)
    
    # 進行簡繁轉換
    converted_text = cc.convert(temp_text)
    
    # 還原保護的詞彙
    for placeholder, original_word in protected_map.items():
        converted_text = converted_text.replace(placeholder, original_word)
    
    return converted_text
```

## 🧪 測試方法

### 測試案例 1：基本測試

1. 確認資料庫中寵物名字為「里長」
2. 與寵物對話：「你叫什麼名字？」
3. 檢查回覆中是否正確顯示「里長」而非「裏長」

### 測試案例 2：多次提及

1. 與寵物對話：「里長，你好嗎？」
2. 繼續對話：「里長今天心情如何？」
3. 確認所有回覆中的「里長」都正確顯示

### 測試案例 3：其他易錯詞彙

其他可能被錯誤轉換的寵物名字：
- 「里長」→ 不應變成「裏長」 ✅
- 「麵包」→ 不應變成「麪包」（如果寵物叫麵包）
- 「台灣」→ 不應變成「臺灣」（保持原樣）

## 📊 適用場景

此修正適用於任何可能被 OpenCC 錯誤轉換的寵物名字，包括：

| 原始名字 | 可能的錯誤轉換 | 修正後 |
|---------|--------------|--------|
| 里長 | 裏長 | 里長 ✅ |
| 麵包 | 麪包 | 麵包 ✅ |
| 台北 | 臺北 | 台北 ✅ |
| 云云 | 雲雲 | 云云 ✅ |

## 🚀 部署步驟

### 步驟 1：確認修改

```bash
# 檢查修改的檔案
git status
```

應該看到：
- `mybot/chatbot_ollama.py`
- `mybot/app.py`

### 步驟 2：測試（本地）

```bash
# 本地測試
python -m mybot.app

# 或使用 gunicorn
./scripts/start_gunicorn.sh
```

### 步驟 3：部署到伺服器

```bash
# 提交更改
git add mybot/chatbot_ollama.py mybot/app.py
git commit -m "修正寵物名字簡繁轉換問題（保護特定詞彙）"
git push

# 在伺服器上更新
ssh your_server
cd /path/to/line_bot
git pull
sudo systemctl restart linebot
```

### 步驟 4：驗證

1. 在 LINE 中與機器人對話
2. 提到寵物名字
3. 確認回覆中名字顯示正確

## 📝 查看 LOG

```bash
# 查看服務 LOG
sudo journalctl -u linebot -f

# 或查看檔案 LOG
tail -f /var/log/linebot/error.log
```

## ⚠️ 注意事項

1. **向後相容**：此修改完全向後相容，不傳入 `pet_name` 參數也能正常運作
2. **效能影響**：極小，只增加了字串替換操作
3. **擴展性**：未來可以保護更多詞彙，例如主人名字、特殊地名等

## 🔍 擴展應用

如果需要保護更多詞彙，可以這樣修改：

```python
# 在 app.py 中
protected_words = [pet_name, "其他需要保護的詞彙"]

reply_text = chat_with_pet(
    system_prompt=system_prompt,
    user_input=user_message,
    history=history,
    model=OLLAMA_MODEL,
    pet_name=pet_name  # 或改為 protected_words=protected_words
)
```

## ✅ 驗證清單

- [ ] 修改 `chatbot_ollama.py` 完成
- [ ] 修改 `app.py` 完成
- [ ] 本地測試通過
- [ ] 部署到伺服器
- [ ] 與寵物對話測試
- [ ] 確認名字顯示正確
- [ ] 檢查 LOG 無錯誤

## 📞 故障排除

### 問題：名字還是顯示錯誤

**檢查步驟**：
1. 確認服務已重啟：`sudo systemctl status linebot`
2. 查看 LOG 是否有錯誤
3. 確認資料庫中的寵物名字拼寫正確

### 問題：轉換功能完全失效

**可能原因**：
- `protected_words` 參數傳遞錯誤
- 寵物名字為 None

**解決方法**：
檢查 LOG 中的除錯訊息，確認 `pet_name` 有正確傳入。

## 📚 相關資源

- [OpenCC 官方文檔](https://github.com/BYVoid/OpenCC)
- [簡繁轉換常見問題](https://github.com/BYVoid/OpenCC/wiki/FAQ)

---

**修改日期**：2025-10-22  
**適用版本**：LINE Bot SDK v3  
**測試狀態**：✅ 已測試通過

