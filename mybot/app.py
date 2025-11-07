# app.py
# ============================================
# 寵物聊天機器人 - LINE Bot 版本 (SDK v3)
# ============================================
# 功能：透過 LINE Messaging API 與虛擬寵物對話
# 特色：多使用者支援、對話歷史管理、特殊指令
# 使用 LINE Bot SDK v3
# ============================================

import os
import logging
import uuid
import random
import requests
from datetime import datetime, date
from dotenv import load_dotenv
from flask import Flask, request, abort, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont

# LINE Bot SDK v3
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    ImageMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# 載入環境變數（從 .env 檔案）
load_dotenv()

# ============================================
# Logging 設定
# ============================================

# 確保 logs 目錄存在
os.makedirs('logs', exist_ok=True)

# 設定 logging 格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 輸出到控制台
        logging.FileHandler('logs/app.log', encoding='utf-8')  # 輸出到檔案
    ]
)

# 建立 logger
logger = logging.getLogger('pet_chatbot')

# 支援兩種運行方式：
# 1. 作為套件運行（CloudPanel 部署）：from mybot.xxx import
# 2. 作為獨立腳本運行（本地開發）：from xxx import
try:
    from mybot.db_utils import (
        get_pet_profile, 
        get_pet_id_by_line_user,
        save_chat_message,
        get_chat_history,
        clear_chat_history,
        get_all_bound_users,
        get_daily_fortune_card,
        save_daily_fortune_card,
        create_daily_fortune_cards_table
    )
    from mybot.personalities import pet_personality_templates
    from mybot.chatbot_ollama import build_system_prompt, chat_with_pet as chat_with_pet_ollama
    from mybot.chatbot_api import build_system_prompt as build_system_prompt_api, chat_with_pet as chat_with_pet_api
    from mybot.fortune_card import generate_fortune_card as fortune_card_generate
    from mybot.line_handlers import handle_text_message as line_handle_text_message
except ImportError:
    from db_utils import (
        get_pet_profile, 
        get_pet_id_by_line_user,
        save_chat_message,
        get_chat_history,
        clear_chat_history,
        get_all_bound_users,
        get_daily_fortune_card,
        save_daily_fortune_card,
        create_daily_fortune_cards_table
    )
    from personalities import pet_personality_templates
    from chatbot_ollama import build_system_prompt, chat_with_pet as chat_with_pet_ollama
    from chatbot_api import build_system_prompt as build_system_prompt_api, chat_with_pet as chat_with_pet_api
    from fortune_card import generate_fortune_card as fortune_card_generate
    from line_handlers import handle_text_message as line_handle_text_message

# ============================================
# Flask 應用程式初始化
# ============================================

app = Flask(__name__)

# 從環境變數讀取 LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# 從環境變數讀取 API 基礎 URL
try:
    from mybot.config import BASE_URL, EXTERNAL_URL
except ImportError:
    from config import BASE_URL, EXTERNAL_URL

# 記錄 URL 配置（用於調試）
logger.info(f"🌐 BASE_URL (API): {BASE_URL}")
logger.info(f"🌐 EXTERNAL_URL (圖片): {EXTERNAL_URL}")

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

# 記錄 AI 模式設定
logger.info(f"🤖 AI 模式設定: {AI_MODE}")
if AI_MODE == 'api':
    logger.info(f"🌐 使用 API 模式 - 模型: {QWEN_MODEL}")
    logger.info(f"🔑 API Key 狀態: {'已設定' if os.getenv('QWEN_API_KEY') and os.getenv('QWEN_API_KEY') != 'your_qwen_api_key' else '未設定'}")
else:
    logger.info(f"🏠 使用本地 Ollama 模式 - 模型: {OLLAMA_MODEL}")
    logger.info("💡 提示: 如需切換到 API 模式，請設定 AI_MODE=api 和 QWEN_API_KEY")

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

# 獲取基礎目錄路徑（相對於 app.py 的位置）
def _get_base_dir():
    """
    獲取專案根目錄的絕對路徑
    
    說明:
        - 如果 app.py 在 mybot/ 目錄下，返回上一層目錄（專案根目錄）
        - 專案根目錄應該包含 assets/ 資料夾
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 如果當前目錄是 mybot，返回上一層
    if os.path.basename(current_dir) == 'mybot':
        return os.path.dirname(current_dir)
    # 否則返回當前目錄
    return current_dir

def _get_output_dir():
    """獲取 output 目錄的絕對路徑"""
    return os.path.join(_get_base_dir(), "output")

def generate_fortune_card(pet_id: int) -> str:
    """
    生成寵物占卜卡（包裝函數，調用 fortune_card 模組）
    
    參數:
        pet_id (int): 寵物 ID
    
    返回:
        str: 生成的占卜卡圖片外部 URL，如果失敗則返回 None
    """
    return fortune_card_generate(
        pet_id=pet_id,
        BASE_URL=BASE_URL,
        EXTERNAL_URL=EXTERNAL_URL,
        get_daily_fortune_card_func=get_daily_fortune_card,
        save_daily_fortune_card_func=save_daily_fortune_card
    )


def get_pet_system_prompt(pet_id=None):
    """
    取得寵物的系統提示詞
    
    參數:
        pet_id (int, optional): 寵物 ID，如果不提供則使用環境變數的 PET_ID
    
    返回:
        tuple: (system_prompt, pet_name, web_slug) 或 (None, None, None) 如果載入失敗
    
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
            return None, None, None
        
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
        
        return system_prompt, pet_profile["name"], pet_profile.get("web_slug")
    except Exception as e:
        app.logger.error(f"載入寵物資料失敗: {e}")
        return None, None, None


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


@app.route("/output/<filename>")
@app.route("/line/output/<filename>")  # 支援 Nginx 轉發的路徑
def serve_output_file(filename):
    """
    提供 output 目錄中的靜態文件（占卜卡圖片）
    
    參數:
        filename: 文件名稱
    
    返回:
        Flask Response: 圖片文件或 404 錯誤
    
    說明:
        讓 LINE Bot 可以通過 URL 訪問生成的占卜卡圖片
    """
    try:
        from flask import send_from_directory
        output_dir = _get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        
        # 安全性檢查：確保文件名不包含路徑跳轉字符
        if '..' in filename or '/' in filename or '\\' in filename:
            app.logger.warning(f"❌ 嘗試訪問非法文件: {filename}")
            abort(404)
        
        # 檢查文件是否存在
        file_path = os.path.join(output_dir, filename)
        if not os.path.exists(file_path):
            app.logger.warning(f"❌ 文件不存在: {file_path}")
            abort(404)
        
        # 發送文件
        app.logger.info(f"📤 提供文件: {filename}, 路徑: {file_path}")
        response = send_from_directory(output_dir, filename, mimetype='image/png')
        # 確保正確的 Content-Type 和 Cache-Control
        response.headers['Content-Type'] = 'image/png'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    except Exception as e:
        app.logger.error(f"❌ 提供文件失敗: {e}")
        abort(404)


@app.route("/webhook", methods=['GET', 'POST'])
def callback():
    """
    LINE Webhook 回調路由
    
    說明:
        接收來自 LINE Platform 的事件
        驗證簽名並轉發給 handler 處理
        處理 LINE 的驗證請求和實際事件
    """
    try:
        # 處理 GET 請求（LINE 驗證或 ngrok 檢查）
        if request.method == 'GET':
            app.logger.info("✅ 收到 GET 請求（LINE webhook 驗證或 ngrok 檢查）")
            return 'OK', 200
        
        # 處理 POST 請求（LINE 的實際 webhook）
        app.logger.info("📨 收到 POST webhook 請求")
        
        # 取得 X-Line-Signature header
        signature = request.headers.get('X-Line-Signature')
        
        # 取得 request body
        body = request.get_data(as_text=True)
        
        # LINE 驗證請求可能是空 body，需要特殊處理
        if not body or len(body) == 0:
            app.logger.info("📨 收到空 body（可能是 LINE 驗證請求）")
            if signature:
                # 有簽名但空 body，可能是驗證請求，返回 OK
                app.logger.info("✅ 驗證請求通過")
                return 'OK', 200
            else:
                # 無簽名無 body，可能是測試請求
                app.logger.info("✅ 測試請求，返回 OK")
                return 'OK', 200
        
        # 有 body 的請求需要驗證簽名
        if not signature:
            app.logger.error("❌ 缺少 X-Line-Signature header（有 body 但無簽名）")
            # 為了調試，記錄請求信息但不 abort
            app.logger.error(f"❌ Request headers: {dict(request.headers)}")
            app.logger.error(f"❌ Body 長度: {len(body)}")
            # 返回 200 以避免 LINE 重試（但記錄錯誤）
            return 'OK', 200
        
        app.logger.info(f"📦 Webhook body 長度: {len(body)} 字符")
        app.logger.info(f"📦 Body 前 100 字符: {body[:100]}")
        
        # 驗證簽名並處理事件
        try:
            handler.handle(body, signature)
            app.logger.info("✅ Webhook 處理完成")
        except InvalidSignatureError as e:
            app.logger.error(f"❌ 簽名驗證失敗！請檢查 LINE_CHANNEL_SECRET 是否正確: {e}")
            # 簽名驗證失敗時也返回 200，避免 LINE 重試
            # 但記錄錯誤以便排查
            return 'OK', 200
        except Exception as e:
            app.logger.error(f"❌ 處理 webhook 時發生錯誤: {e}", exc_info=True)
            # 發生其他錯誤時也返回 200，避免 LINE 重試
            # 但記錄完整錯誤信息
            return 'OK', 200
        
        return 'OK', 200
        
    except Exception as e:
        # 捕獲所有未預期的異常，確保始終返回 200
        app.logger.error(f"❌ Webhook 處理發生未預期錯誤: {e}", exc_info=True)
        return 'OK', 200


@app.route("/daily-fortune", methods=['POST'])
def daily_fortune():
    """
    每日推播占卜卡功能
    
    說明:
        1. 僅允許 localhost (127.0.0.1) 存取
        2. 從資料庫查出所有已綁定 LINE 的使用者
        3. 為每位使用者生成占卜卡並推播
    
    返回:
        JSON: {"status": "success", "count": 推播成功的使用者數量}
        或 403 Forbidden (如果非 localhost 請求)
    """
    # 檢查請求來源是否為 localhost
    # 支援 IPv4 (127.0.0.1) 和 IPv6 (::1) 的 localhost
    client_ip = request.remote_addr
    
    # 如果透過 Nginx 反向代理，檢查 X-Forwarded-For header
    forwarded_for = request.headers.get('X-Forwarded-For', '').split(',')[0].strip() if request.headers.get('X-Forwarded-For') else None
    real_ip = request.headers.get('X-Real-IP', '').strip() if request.headers.get('X-Real-IP') else None
    
    # 檢查實際來源 IP（優先順序：X-Real-IP > X-Forwarded-For > remote_addr）
    actual_ip = real_ip or forwarded_for or client_ip
    
    allowed_ips = ['127.0.0.1', '::1', 'localhost']

    if actual_ip not in allowed_ips:
        app.logger.warning(f"拒絕非本地來源: {actual_ip}")
        abort(403)
    
    app.logger.info("📅 Daily fortune job started")
    
    try:
        # 1. 獲取所有已綁定 LINE 的使用者
        bound_users = get_all_bound_users()
        
        if not bound_users:
            app.logger.info("ℹ️ 沒有已綁定 LINE 的使用者")
            return jsonify({"status": "success", "count": 0}), 200
        
        app.logger.info(f"📋 找到 {len(bound_users)} 位已綁定使用者，開始推播占卜卡")
        
        # 2. 統計變數
        success_count = 0
        failed_count = 0
        
        # 3. 遍歷每位使用者並推播占卜卡
        for user in bound_users:
            pet_id = user.get('pet_id')
            line_user_id = user.get('line_user_id')
            
            if not pet_id or not line_user_id:
                app.logger.warning(f"⚠️ 使用者資料不完整: {user}")
                failed_count += 1
                continue
            
            try:
                app.logger.info(f"🔮 為使用者推播占卜卡 - pet_id: {pet_id}, line_user_id: {line_user_id}")
                
                # 生成占卜卡
                fortune_card_url = generate_fortune_card(pet_id)
                
                if not fortune_card_url:
                    app.logger.warning(f"⚠️ 占卜卡生成失敗 - pet_id: {pet_id}, line_user_id: {line_user_id}")
                    failed_count += 1
                    continue
                
                app.logger.info(f"✅ 占卜卡生成成功 - URL: {fortune_card_url}")
                
                # 使用 LINE Messaging API 推送圖片
                image_message = ImageMessage(
                    original_content_url=fortune_card_url,
                    preview_image_url=fortune_card_url
                )
                
                try:
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.push_message(
                            PushMessageRequest(
                                to=line_user_id,
                                messages=[image_message]
                            )
                        )
                    app.logger.info(f"✅ 成功推播占卜卡給使用者 - line_user_id: {line_user_id}")
                    success_count += 1
                except Exception as push_error:
                    app.logger.error(f"❌ LINE 推播失敗 - line_user_id: {line_user_id}, 錯誤: {push_error}")
                    failed_count += 1
                    
            except Exception as e:
                app.logger.error(f"❌ 處理使用者推播時發生錯誤 - pet_id: {pet_id}, line_user_id: {line_user_id}, 錯誤: {e}", exc_info=True)
                failed_count += 1
        
        # 4. 回傳結果
        app.logger.info(f"📊 每日推播完成 - 成功: {success_count}, 失敗: {failed_count}")
        return jsonify({
            "status": "success",
            "count": success_count,
            "failed": failed_count
        }), 200
        
    except Exception as e:
        app.logger.error(f"❌ 每日推播功能發生錯誤: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================
# LINE Bot 事件處理 (SDK v3)
# ============================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """
    處理文字訊息事件（包裝函數，調用 line_handlers 模組）
    
    參數:
        event: LINE MessageEvent 物件
    """
    line_handle_text_message(
        event=event,
        get_pet_id_by_line_user_func=get_pet_id_by_line_user,
        get_pet_system_prompt_func=get_pet_system_prompt,
        clear_chat_history_func=clear_chat_history,
        save_chat_message_func=save_chat_message,
        get_chat_history_func=get_chat_history,
        chat_with_pet_api_func=chat_with_pet_api,
        chat_with_pet_ollama_func=chat_with_pet_ollama,
        generate_fortune_card_func=generate_fortune_card,
        BASE_URL=BASE_URL,
        EXTERNAL_URL=EXTERNAL_URL,
        AI_MODE=AI_MODE,
        QWEN_MODEL=QWEN_MODEL,
        OLLAMA_MODEL=OLLAMA_MODEL,
        configuration=configuration,
        base_dir=_get_base_dir()
    )


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
    system_prompt, pet_name, _ = get_pet_system_prompt()
    if system_prompt and pet_name:
        print(f"✅ 寵物資料已載入：{pet_name}")
    else:
        print("⚠️  無法載入寵物資料（請確認資料庫連線）")
    
    print(f"\n🤖 AI 模式：{AI_MODE}")
    if AI_MODE == 'api':
        print(f"🌐 使用的 API 模型：{QWEN_MODEL}")
        api_key_status = "已設定" if os.getenv('QWEN_API_KEY') and os.getenv('QWEN_API_KEY') != 'your_qwen_api_key' else "未設定"
        print(f"🔑 API Key 狀態：{api_key_status}")
        if api_key_status == "未設定":
            print("⚠️  警告：API Key 未設定，API 模式可能無法正常工作")
    else:
        print(f"🏠 使用的本地模型：{OLLAMA_MODEL}")
        print("💡 提示：如需切換到 API 模式，請設定 AI_MODE=api 和 QWEN_API_KEY")
    print(f"🐕 寵物 ID：{PET_ID}")
    
    # 記錄啟動資訊到日誌
    logger.info("🚀 寵物聊天機器人啟動完成")
    logger.info(f"🤖 AI 模式: {AI_MODE}")
    if AI_MODE == 'api':
        logger.info(f"🌐 API 模型: {QWEN_MODEL}")
        logger.info(f"🔑 API Key 狀態: {api_key_status}")
    else:
        logger.info(f"🏠 Ollama 模型: {OLLAMA_MODEL}")
    logger.info(f"🐕 寵物 ID: {PET_ID}")
    
    # 確保必要的目錄存在
    os.makedirs('output', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    logger.info("✅ 目錄檢查完成（output, logs）")
    
    # 初始化每日占卜卡資料表（如果不存在）
    try:
        create_daily_fortune_cards_table()
        logger.info("✅ 每日占卜卡資料表檢查完成")
    except Exception as e:
        logger.warning(f"⚠️  初始化每日占卜卡資料表時發生錯誤: {e}")
        logger.warning("💡 提示: 請手動執行 SQL 創建 daily_fortune_cards 表")
    
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
