# app.py
# ============================================
# 寵物聊天機器人 - LINE Bot 版本 (SDK v3)
# ============================================
# 功能：透過 LINE Messaging API 與虛擬寵物對話
# 特色：多使用者支援、對話歷史管理、特殊指令
# 使用 LINE Bot SDK v3
# ============================================

import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, abort, jsonify

# LINE Bot SDK v3
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# 載入環境變數（從 .env 檔案）
load_dotenv()

# 支援兩種運行方式：
# 1. 作為套件運行（CloudPanel 部署）：from mybot.xxx import
# 2. 作為獨立腳本運行（本地開發）：from xxx import
try:
    from mybot.db_utils import (
        get_pet_profile, 
        get_pet_id_by_line_user,
        save_chat_message,
        get_chat_history,
        clear_chat_history
    )
    from mybot.personalities import pet_personality_templates
    from mybot.chatbot_ollama import build_system_prompt, chat_with_pet as chat_with_pet_ollama
    from mybot.chatbot_api import build_system_prompt as build_system_prompt_api, chat_with_pet as chat_with_pet_api
except ImportError:
    from db_utils import (
        get_pet_profile, 
        get_pet_id_by_line_user,
        save_chat_message,
        get_chat_history,
        clear_chat_history
    )
    from personalities import pet_personality_templates
    from chatbot_ollama import build_system_prompt, chat_with_pet as chat_with_pet_ollama
    from chatbot_api import build_system_prompt as build_system_prompt_api, chat_with_pet as chat_with_pet_api

# ============================================
# Flask 應用程式初始化
# ============================================

app = Flask(__name__)

# 從環境變數讀取 LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# 檢查 LINE Bot 憑證是否已設定
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("⚠️  警告：LINE Bot 憑證未設定！")
    print("請在 .env 檔案中設定：")
    print("  LINE_CHANNEL_ACCESS_TOKEN=你的token")
    print("  LINE_CHANNEL_SECRET=你的secret")

# 初始化 LINE Bot API (SDK v3)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 寵物設定（從環境變數讀取，預設為 1）
PET_ID = int(os.getenv('PET_ID', 1))

# AI 模式設定
AI_MODE = os.getenv('AI_MODE', 'ollama')  # 預設使用 Ollama
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen:7b')
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-flash')

# ============================================
# 對話記錄已改用資料庫儲存
# ============================================
# 不再使用記憶體存儲對話歷史，改為使用資料庫 chat_history 資料表
# 優點：
# 1. 持久化儲存，服務重啟後不會丟失對話
# 2. 不同寵物的對話自動分離（透過 line_user_id + pet_id 組合）
# 3. 可以在多個服務實例間共享對話歷史
# ============================================

# ============================================
# 核心功能函數
# ============================================

def get_pet_system_prompt(pet_id=None):
    """
    取得寵物的系統提示詞
    
    參數:
        pet_id (int, optional): 寵物 ID，如果不提供則使用環境變數的 PET_ID
    
    返回:
        tuple: (system_prompt, pet_name) 或 (None, None) 如果載入失敗
    
    說明:
        從資料庫載入寵物資料並建立系統提示詞
        此函數會被多個使用者共用
        根據 AI_MODE 選擇使用 Ollama 或 API 版本
    """
    try:
        # 如果沒有指定 pet_id，使用環境變數的預設值
        if pet_id is None:
            pet_id = PET_ID
            
        pet_profile = get_pet_profile(pet_id)
        
        if not pet_profile:
            return None, None
        
        # 根據 AI_MODE 選擇對應的 build_system_prompt 函數
        if AI_MODE == 'api':
            system_prompt = build_system_prompt_api(
                pet_name=pet_profile["name"],
                breed=pet_profile["breed"],
                persona=pet_personality_templates[pet_profile["persona_key"]],
                life_data=pet_profile["lifeData"],
                cover_slogan=pet_profile["cover_slogan"],
                letter=pet_profile["letter"]
            )
        else:  # 預設使用 Ollama
            system_prompt = build_system_prompt(
                pet_name=pet_profile["name"],
                breed=pet_profile["breed"],
                persona=pet_personality_templates[pet_profile["persona_key"]],
                life_data=pet_profile["lifeData"],
                cover_slogan=pet_profile["cover_slogan"],
                letter=pet_profile["letter"]
            )
        
        return system_prompt, pet_profile["name"]
    except Exception as e:
        app.logger.error(f"載入寵物資料失敗: {e}")
        return None, None


# ============================================
# Flask 路由處理
# ============================================

@app.route("/")
def home():
    """
    首頁路由
    
    返回:
        str: 簡單的狀態訊息
    
    說明:
        用於檢查服務是否正常運行
    """
    return "🐕 寵物聊天機器人 LINE Bot 正在運行中！"


@app.route("/webhook", methods=['GET', 'POST'])
def callback():
    """
    LINE Webhook 回調路由
    
    說明:
        接收來自 LINE Platform 的事件
        驗證簽名並轉發給 handler 處理
        處理 ngrok 免費版的 GET 請求
    """
    # 處理 GET 請求（ngrok 免費版會先發送 GET 請求）
    if request.method == 'GET':
        app.logger.info("收到 GET 請求（可能是 ngrok 免費版檢查）")
        return 'OK', 200
    
    # 處理 POST 請求（LINE 的實際 webhook）
    # 取得 X-Line-Signature header
    signature = request.headers.get('X-Line-Signature')
    
    if not signature:
        app.logger.error("缺少 X-Line-Signature header")
        abort(400)
    
    # 取得 request body
    body = request.get_data(as_text=True)
    app.logger.info(f"收到 webhook 請求: {body}")
    
    # 驗證簽名並處理事件
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("簽名驗證失敗！請檢查 LINE_CHANNEL_SECRET 是否正確")
        abort(400)
    except Exception as e:
        app.logger.error(f"處理 webhook 時發生錯誤: {e}")
        abort(500)
    
    return 'OK', 200


@app.route("/test")
def test():
    """
    測試端點
    
    返回:
        str: 測試結果訊息
    
    說明:
        用於測試寵物資料是否正常載入
    """
    system_prompt, pet_name = get_pet_system_prompt()
    if system_prompt and pet_name:
        return f"✅ 寵物聊天機器人已就緒！寵物名稱：{pet_name}"
    else:
        return "❌ 無法載入寵物資料，請檢查資料庫連線"


@app.route("/healthz")
def healthz():
    """
    健康檢查端點
    
    返回:
        JSON: 服務狀態
    
    說明:
        用於 systemd、Nginx 或監控工具檢查服務是否正常
        檢查項目：LINE Bot 憑證、資料庫連線、Ollama 連線
    """
    status = {
        "status": "healthy",
        "service": "LINE Bot - Pet Chatbot",
        "timestamp": datetime.now().isoformat()
    }
    
    checks = {}
    
    # 檢查 LINE Bot 憑證
    checks["line_credentials"] = bool(
        LINE_CHANNEL_ACCESS_TOKEN and 
        LINE_CHANNEL_SECRET and
        LINE_CHANNEL_ACCESS_TOKEN != 'your_channel_access_token'
    )
    
    # 檢查寵物資料載入
    system_prompt, pet_name = get_pet_system_prompt()
    checks["pet_data"] = bool(system_prompt and pet_name)
    if pet_name:
        status["pet_name"] = pet_name
    
    # 檢查 Ollama 連線（可選）
    try:
        import ollama
        ollama.list()
        checks["ollama_connection"] = True
    except Exception as e:
        checks["ollama_connection"] = False
        app.logger.warning(f"Ollama 連線檢查失敗: {e}")
    
    # 判斷整體狀態
    all_healthy = all(checks.values())
    
    status["checks"] = checks
    status["status"] = "healthy" if all_healthy else "degraded"
    
    http_status = 200 if all_healthy else 503
    
    return jsonify(status), http_status


# ============================================
# LINE Bot 事件處理 (SDK v3)
# ============================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """
    處理文字訊息事件
    
    參數:
        event: LINE MessageEvent 物件
    
    說明:
        1. 取得使用者 ID 和訊息內容
        2. 檢查使用者是否已設定寵物
        3. 呼叫 process_user_message() 生成回覆
        4. 使用 reply_message 回覆給使用者
        5. 記錄對話日誌
    """
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    
    # 記錄收到的訊息
    app.logger.info(f"使用者 {user_id} 說：{user_message}")
    
    try:
        # === 步驟 1: 檢查使用者是否已在 pets 表中設定 ===
        pet_id = get_pet_id_by_line_user(user_id)
        
        # 記錄查詢到的 pet_id
        app.logger.info(f"使用者 {user_id} 綁定的 pet_id: {pet_id}")
        
        # 特殊處理「我的ID」指令
        if user_message.lower() in ['我的id', '我的ID', 'myid', 'my id', 'userid', 'user id']:
            if pet_id:
                # 已設定寵物的使用者
                reply_text = f"""🆔 你的使用者資訊

LINE User ID:
{user_id}

✅ 你已經設定好寵物了，可以直接聊天喔～"""
            else:
                # 未設定寵物的使用者
                reply_text = f"""🆔 你的使用者資訊

LINE User ID:
{user_id}

⚠️ 你還沒有設定專屬寵物喔！

請將上面的 User ID 複製後，提供給客服人員進行設定。設定完成後就可以開始和你的虛擬寵物聊天囉！

📞 需要協助請聯絡客服"""
        
        elif not pet_id:
            # === 使用者尚未設定寵物 ===
            reply_text = """👋 哈囉！歡迎使用寵物聊天機器人！

⚠️ 你還沒有設定專屬寵物喔！

請先在聊天視窗輸入「我的ID」，系統會顯示你的 LINE User ID。

將該 ID 複製後提供給客服人員進行設定，設定完成後就可以開始聊天囉！"""
        
        else:
            # === 使用者已設定寵物，正常處理對話 ===
            # 修改 process_user_message 調用，傳入 pet_id
            system_prompt, pet_name = get_pet_system_prompt(pet_id)
            
            # 記錄查詢到的寵物資料
            app.logger.info(f"載入寵物資料 - pet_id: {pet_id}, pet_name: {pet_name}")
            
            if not system_prompt:
                reply_text = "嗚...主人，我現在記不起來自己是誰了 😢\n請稍後再試試看"
            else:
                # 處理特殊指令
                if user_message.lower() in ['clear', '清除', '重置']:
                    # 清除資料庫中的對話記錄
                    clear_chat_history(user_id, pet_id)
                    reply_text = "嗚！我忘記之前的對話了，我們重新開始吧！"
                    
                elif user_message.lower() in ['help', '幫助', '說明']:
                    reply_text = """🐕 寵物聊天機器人使用說明

• 直接傳送訊息，我會像寵物一樣回覆你
• 輸入「清除」可以重置對話記錄
• 輸入「說明」查看此訊息
• 輸入「我的ID」查看你的使用者ID

快來跟我聊天吧！～"""
                    
                else:
                    # 一般對話 - 從資料庫讀取對話歷史
                    history = get_chat_history(user_id, pet_id, limit=8)
                    
                    # 先儲存使用者的訊息
                    save_chat_message(user_id, pet_id, 'user', user_message)
                    
                    # 根據 AI_MODE 選擇對應的 chat_with_pet 函數
                    if AI_MODE == 'api':
                        reply_text = chat_with_pet_api(
                            system_prompt=system_prompt,
                            user_input=user_message,
                            history=history,
                            model=QWEN_MODEL,
                            pet_name=pet_name
                        )
                    else:  # 預設使用 Ollama
                        reply_text = chat_with_pet_ollama(
                            system_prompt=system_prompt,
                            user_input=user_message,
                            history=history,
                            model=OLLAMA_MODEL,
                            pet_name=pet_name
                        )
                    
                    # 儲存寵物的回覆
                    save_chat_message(user_id, pet_id, 'assistant', reply_text)
        
        # 使用 SDK v3 回覆訊息
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        
        # 記錄回覆
        app.logger.info(f"回覆使用者 {user_id}：{reply_text}")
        
    except Exception as e:
        app.logger.error(f"處理訊息時發生錯誤: {e}")
        # 發生錯誤時的備用回覆
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="嗚...主人，我現在有點不舒服 🥺")]
                    )
                )
        except:
            pass


# ============================================
# 主程式入口
# ============================================

def main():
    """
    主程式入口點
    
    功能：
        1. 顯示啟動訊息
        2. 檢查必要的環境設定
        3. 啟動 Flask 應用
    """
    print("=" * 50)
    print("🐕 寵物聊天機器人 - LINE Bot (SDK v3)")
    print("=" * 50)
    
    # 檢查環境設定
    print("\n📋 環境設定檢查：")
    
    if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_ACCESS_TOKEN != 'your_channel_access_token':
        print("✅ LINE Channel Access Token 已設定")
    else:
        print("❌ LINE Channel Access Token 未設定")
    
    if LINE_CHANNEL_SECRET and LINE_CHANNEL_SECRET != 'your_channel_secret':
        print("✅ LINE Channel Secret 已設定")
    else:
        print("❌ LINE Channel Secret 未設定")
    
    # 測試寵物資料載入
    system_prompt, pet_name = get_pet_system_prompt()
    if system_prompt and pet_name:
        print(f"✅ 寵物資料已載入：{pet_name}")
    else:
        print("⚠️  無法載入寵物資料（請確認資料庫連線）")
    
    print(f"\n🤖 AI 模式：{AI_MODE}")
    if AI_MODE == 'api':
        print(f"🌐 使用的 API 模型：{QWEN_MODEL}")
    else:
        print(f"🏠 使用的本地模型：{OLLAMA_MODEL}")
    print(f"🐕 寵物 ID：{PET_ID}")
    
    # 啟動 Flask 應用
    port = int(os.getenv('PORT', 8000))
    print(f"\n🚀 啟動 Flask 伺服器於埠號 {port}...")
    print(f"📍 首頁: http://localhost:{port}/")
    print(f"📍 Webhook: http://localhost:{port}/webhook")
    print(f"📍 測試: http://localhost:{port}/test")
    print("\n提示：")
    print("1. 使用 ngrok 將本地服務暴露到公網")
    print("   ngrok http", port)
    print("2. 在 LINE Developers Console 設定 Webhook URL:")
    print("   https://你的ngrok網址.ngrok.io/webhook")
    print("3. 開始與寵物聊天！")
    print("=" * 50)
    print()
    
    # 啟動 Flask (開發模式)
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == "__main__":
    main()
