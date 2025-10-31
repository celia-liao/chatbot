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
from datetime import datetime
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

def generate_fortune_card(pet_id: int) -> str:
    """
    生成寵物占卜卡
    
    參數:
        pet_id (int): 寵物 ID
    
    返回:
        str: 生成的占卜卡圖片外部 URL，如果失敗則返回 None
    
    功能:
        1. 呼叫 A 專案 API 獲取寵物資料
        2. 下載寵物頭像圖片
        3. 從本地隨機選擇背景圖片
        4. 合成占卜卡（頭像貼在指定位置）
        5. 添加文字（寵物名稱 + "今天好運旺旺！"）
        6. 保存到 output 目錄
        7. 返回外部 URL
    """
    try:
        # 1. 確保 output 目錄存在
        output_dir = './output'
        os.makedirs(output_dir, exist_ok=True)
        
        # 2. 呼叫 A 專案 API 獲取寵物資料
        api_url = f"https://test.ruru1211.xyz/api/fortune-card/random?pet_id={pet_id}"
        app.logger.info(f"🔮 調用占卜卡 API: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        # 確保使用 UTF-8 編碼解析 JSON
        response.encoding = 'utf-8'
        data = response.json()
        
        if not data.get('success', False):
            app.logger.error(f"❌ API 返回失敗: {data}")
            return None
        
        fortune_data = data.get('data', {})
        pet_name = fortune_data.get('pet_name', '')
        pet_image_url = fortune_data.get('pet_image', '')
        cover_image_url = fortune_data.get('cover_image', '')
        
        if not pet_name or not pet_image_url:
            app.logger.error(f"❌ API 數據不完整: {fortune_data}")
            return None
        
        # 確保 pet_name 是正確的字串格式
        if isinstance(pet_name, bytes):
            pet_name = pet_name.decode('utf-8')
        pet_name = str(pet_name).strip()
        
        app.logger.info(f"✅ 獲取寵物資料成功: {pet_name} (編碼: {type(pet_name)}), 頭像: {pet_image_url}")
        
        # 3. 下載寵物頭像圖片
        pet_image_response = requests.get(pet_image_url, timeout=10)
        pet_image_response.raise_for_status()
        
        # 保存臨時頭像文件
        temp_pet_path = f'/tmp/pet_{uuid.uuid4()}.png'
        with open(temp_pet_path, 'wb') as f:
            f.write(pet_image_response.content)
        
        # 3. 處理寵物頭像 - 調整為較小尺寸放在圓框內
        pet_image = Image.open(temp_pet_path).convert('RGBA')
        
        # 創建背景層（600x1000，透明背景）
        pet_image_bg = Image.new('RGBA', (600, 1000), (255, 255, 255, 0))
        
        # 將寵物頭像調整為較小尺寸（約 280x280，適合圓框顯示）
        # 保持寬高比，使用 fit 模式
        target_size = 280
        pet_ratio = pet_image.width / pet_image.height
        
        if pet_ratio >= 1:
            # 圖片較寬或正方形，以寬度為準
            new_width = target_size
            new_height = int(target_size / pet_ratio)
        else:
            # 圖片較高，以高度為準
            new_height = target_size
            new_width = int(target_size * pet_ratio)
        
        resized_pet = pet_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 將寵物頭像放在背景中心位置（圓框通常在卡片中上部）
        x_offset = (600 - new_width) // 2
        y_offset = 240  # 垂直位置，與原本的圓框位置對齊
        
        pet_image_bg.paste(resized_pet, (x_offset, y_offset), resized_pet)
        
        app.logger.info(f"✅ 寵物頭像處理完成: 原始尺寸 {pet_image.size}, 調整後 {resized_pet.size}, 位置 ({x_offset}, {y_offset})")
        
        # 4. 處理 cover_image - 作為覆蓋層
        if cover_image_url:
            # 如果有 API 提供的覆蓋圖片，使用它
            cover_response = requests.get(cover_image_url, timeout=10)
            cover_response.raise_for_status()
            
            temp_bg_path = f'/tmp/bg_{uuid.uuid4()}.png'
            with open(temp_bg_path, 'wb') as f:
                f.write(cover_response.content)
            
            cover_image = Image.open(temp_bg_path).convert('RGBA')
            # 調整覆蓋圖片大小為 600x1000
            cover_image = cover_image.resize((600, 1000), Image.Resampling.LANCZOS)
            
            # 清理臨時文件
            os.remove(temp_bg_path)
        else:
            # 從本地隨機選擇覆蓋圖片
            bg_dir = './assets/images/fortune_bg'
            if not os.path.exists(bg_dir):
                app.logger.error(f"❌ 覆蓋圖片目錄不存在: {bg_dir}")
                os.remove(temp_pet_path)
                return None
            
            bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not bg_files:
                app.logger.error(f"❌ 覆蓋圖片目錄為空: {bg_dir}")
                os.remove(temp_pet_path)
                return None
            
            # 隨機選擇一張覆蓋圖片
            random_bg = random.choice(bg_files)
            bg_path = os.path.join(bg_dir, random_bg)
            app.logger.info(f"🎲 隨機選擇覆蓋圖片: {random_bg}")
            
            cover_image = Image.open(bg_path).convert('RGBA')
            # 調整覆蓋圖片大小為 600x1000
            cover_image = cover_image.resize((600, 1000), Image.Resampling.LANCZOS)
        
        app.logger.info(f"✅ 覆蓋圖片處理完成: {cover_image.size}, 模式: {cover_image.mode}")
        
        # 檢查 cover_image 是否有透明度（檢查 alpha 通道）
        has_transparency = False
        if cover_image.mode == 'RGBA':
            # 檢查是否有透明像素
            alpha_channel = cover_image.split()[3]
            has_transparency = any(pixel < 255 for pixel in alpha_channel.getdata())
            app.logger.info(f"🔍 cover_image 透明度檢測: {has_transparency}")
        
        # 5. 合成占卜卡
        # 層級順序（從下到上）：
        #   1. pet_image（寵物頭像，作為背景，放大到 600x1000）
        #   2. cover_image（覆蓋圖片，疊加在寵物頭像上）
        #   3. 文字（寵物名稱）
        
        # ===== 底圖位置調整參數 =====
        cover_x = 0  # 底圖水平位置（0 = 最左邊，正數 = 往右移，負數 = 往左移）
        cover_y = -10  # 底圖垂直位置（0 = 最上邊，正數 = 往下移，負數 = 往上移）
        # ===== 調整說明 =====
        # - 如果底圖需要往右移動 10 像素：cover_x = 10
        # - 如果底圖需要往下移動 20 像素：cover_y = 20
        # - 如果底圖需要往左移動 5 像素：cover_x = -5
        # - 如果底圖需要往上移動 15 像素：cover_y = -15
        
        # 創建一個新的 RGBA 圖片作為合成層
        composite_image = Image.new('RGBA', (600, 1000))
        
        # 第一層：貼上寵物頭像作為背景
        composite_image.paste(pet_image_bg, (0, 0))
        app.logger.info(f"✅ 第一層：寵物頭像背景已貼上")
        
        # 第二層：疊加覆蓋圖片（cover_image）
        # 使用 paste 配合 mask 參數（第三個參數傳入 cover_image）
        # 這樣 cover_image 的透明區域（圓框內）會顯示下層的寵物頭像
        cover_position = (cover_x, cover_y)
        if cover_image.mode == 'RGBA':
            # 使用 alpha 通道作為 mask，透明區域會保留下層內容
            composite_image.paste(cover_image, cover_position, cover_image)
            app.logger.info(f"✅ 第二層：覆蓋圖片已疊加（使用 RGBA alpha 通道），位置: {cover_position}")
        else:
            # 如果沒有 alpha 通道，直接貼上（會完全覆蓋）
            composite_image.paste(cover_image, cover_position)
            app.logger.warning(f"⚠️ 覆蓋圖片沒有 alpha 通道，會完全覆蓋寵物頭像，位置: {cover_position}")
        
        app.logger.info(f"✅ 圖片合成完成（寵物頭像在下，覆蓋圖片在上，透明區域顯示寵物）")
        
        # 6. 添加文字（寵物名稱）
        draw = ImageDraw.Draw(composite_image)
        
        # 載入字型（支援中文的字型）
        font = None
        font_size = 32  # 字體大小（可調整：建議範圍 20-36）
        
        # 優先順序：1. assets 專案字型 2. macOS 系統字型 3. Linux 系統字型 4. 預設字型
        font_paths = [
            './assets/fonts/粗線體.TTF',              # 專案自訂字型（優先）
            './assets/fonts/粗線體.ttf',              # 專案自訂字型（小寫）
            './assets/fonts/NotoSansTC-Regular.ttf', # 專案預設字型
            '/System/Library/Fonts/STHeiti Medium.ttc', # macOS 中文字型（黑體）
            '/System/Library/Fonts/Hiragino Sans GB.ttc', # macOS 中文字型（冬青黑體）
            '/System/Library/Fonts/STHeiti Light.ttc', # macOS 中文字型（細黑體）
            '/Library/Fonts/PingFang.ttc',              # macOS 中文字型（如果存在）
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Linux 中文字型
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # Linux Noto 字型
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    # 處理不同字型格式
                    font_path_lower = font_path.lower()
                    if font_path_lower.endswith('.ttc'):
                        # TTC 字型文件需要指定字型索引（通常是 0）
                        font = ImageFont.truetype(font_path, font_size, index=0)
                    elif font_path_lower.endswith(('.ttf', '.otf')):
                        # TTF 或 OTF 字型文件
                        font = ImageFont.truetype(font_path, font_size)
                    else:
                        # 嘗試載入（可能是其他格式）
                        font = ImageFont.truetype(font_path, font_size)
                    app.logger.info(f"✅ 載入字型成功: {font_path}, 大小: {font_size}")
                    break
                except Exception as e:
                    app.logger.warning(f"⚠️ 載入字型失敗 {font_path}: {e}")
                    continue
        
        # 如果所有字型都無法載入，使用預設字型（會顯示亂碼）
        if font is None:
            app.logger.error(f"❌ 無法載入任何中文字型，中文可能顯示為方塊")
            app.logger.error(f"💡 請將 NotoSansTC-Regular.ttf 放在 ./assets/fonts/ 目錄")
            font = ImageFont.load_default()
            font_size = 16  # 預設字型較小
        
        # 準備文字內容（確保是 UTF-8 字串）
        text_content = str(pet_name)
        # 確保文字是正確的 Unicode 字串
        if isinstance(text_content, bytes):
            text_content = text_content.decode('utf-8')
        
        app.logger.info(f"🔍 準備繪製文字（垂直排列）: '{text_content}' (類型: {type(text_content)}, 長度: {len(text_content)})")
        
        # ============================================
        # 文字位置調整參數（可在此調整）
        # ============================================
        # 圖片尺寸：寬 600px，高 1000px
        # 座標系統：(0, 0) 在左上角
        # 
        # text_x_offset: 水平偏移（正數向右，負數向左）
        #   - 0 = 水平置中
        #   - 正值 = 向右移動
        #   - 負值 = 向左移動
        #
        # text_y_base: 垂直基準位置（從底部開始計算）
        #   - 900 = 距離底部 100px
        #   - 增大 = 向上移動
        #   - 減小 = 向下移動
        #
        # char_spacing: 字符間距調整（乘以字高）
        #   - 1.0 = 正常間距
        #   - 1.2 = 增加 20% 間距
        #   - 0.8 = 減少 20% 間距
        # ============================================
        text_x_offset = 88     # 水平偏移（單位：像素）- 正值向右，負值向左
        text_y_base = 437      # 垂直基準位置（距離頂部，單位：像素）
        char_spacing = 1.0      # 字符間距倍數
        
        # 垂直排列文字（每個字符垂直向下排列）
        try:
            # 計算第一個字符的寬度以確定水平位置（置中）
            first_char = text_content[0] if text_content else ''
            if first_char:
                char_bbox = draw.textbbox((0, 0), first_char, font=font)
                char_width = char_bbox[2] - char_bbox[0]
                text_x = (600 - char_width) // 2 + text_x_offset  # 應用水平偏移
            else:
                text_x = 300 + text_x_offset  # 預設置中 + 偏移
            
            # 計算每個字符的高度（用於垂直間距）
            sample_char = '字' if text_content else 'A'
            char_bbox = draw.textbbox((0, 0), sample_char, font=font)
            char_height = char_bbox[3] - char_bbox[1]
            char_height_adjusted = int(char_height * char_spacing)  # 應用字符間距
            
            # 計算垂直文字的總高度，從基準位置向上排列
            total_height = len(text_content) * char_height_adjusted
            start_y = text_y_base - total_height  # 從基準位置向上排列
            
            # 逐個字符垂直繪製
            current_y = start_y
            for i, char in enumerate(text_content):
                # 繪製單個字符（垂直排列）- 白色文字
                draw.text((text_x, current_y), char, fill=(255, 255, 255, 255), font=font)
                # 下一個字符向下移動（使用調整後的間距）
                current_y += char_height_adjusted
            
            app.logger.info(f"✅ 垂直文字繪製完成: '{text_content}' 起始位置: ({text_x}, {start_y}), 字符數: {len(text_content)}")
        except Exception as e:
            app.logger.error(f"❌ 垂直文字繪製失敗: {e}")
            # 嘗試使用水平方式作為備用
            try:
                text_bbox = draw.textbbox((0, 0), text_content, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = (600 - text_width) // 2
                draw.text((text_x, 900), text_content, fill=(255, 255, 255, 255), font=font)  # 白色文字
                app.logger.info(f"✅ 使用水平備用方式繪製文字成功")
            except Exception as e2:
                app.logger.error(f"❌ 備用文字繪製也失敗: {e2}")
        
        # 7. 轉換回 RGB 模式並保存
        final_image = composite_image.convert('RGB')
        
        # 生成唯一的文件名
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(output_dir, filename)
        final_image.save(output_path, 'PNG')
        app.logger.info(f"✅ 占卜卡保存成功: {output_path}")
        
        # 清理臨時文件
        os.remove(temp_pet_path)
        
        # 8. 返回外部 URL
        # 注意：URL 需要使用 /line/output/ 前綴，因為 Nginx 配置了 /line 路由
        external_url = f"https://chatbot.ruru1211.xyz/line/output/{filename}"
        app.logger.info(f"🔗 生成的外部 URL: {external_url}")
        return external_url
        
    except Exception as e:
        app.logger.error(f"❌ 生成占卜卡失敗: {e}", exc_info=True)
        # 清理可能存在的臨時文件
        try:
            if 'temp_pet_path' in locals():
                if os.path.exists(temp_pet_path):
                    os.remove(temp_pet_path)
            if 'temp_bg_path' in locals():
                if os.path.exists(temp_bg_path):
                    os.remove(temp_bg_path)
        except:
            pass
        return None


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
        output_dir = os.path.abspath('./output')
        
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
        app.logger.info(f"📤 提供文件: {filename}")
        return send_from_directory(output_dir, filename, mimetype='image/png')
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
• 輸入「愛寵小語」獲取專屬小語
• 輸入「占卜」或「/fortune」生成占卜卡

快來跟我聊天吧！～"""
                # 寵物占卜卡功能
                # 調用 API 生成占卜卡圖片
                elif user_message.lower() in ['毛孩占卜', '/fortune']:
                    try:
                        app.logger.info(f"🔮 用戶 {user_id} 請求占卜卡")
                        
                        # 生成占卜卡
                        fortune_card_url = generate_fortune_card(pet_id)
                        
                        if fortune_card_url:
                            app.logger.info(f"✅ 占卜卡生成成功，URL: {fortune_card_url}")
                            
                            # 使用 ImageMessage 回傳圖片
                            image_message = ImageMessage(
                                original_content_url=fortune_card_url,
                                preview_image_url=fortune_card_url
                            )
                            
                            app.logger.info(f"📤 準備發送圖片到 LINE，URL: {fortune_card_url}")
                            
                            try:
                                    with ApiClient(configuration) as api_client:
                                        line_bot_api = MessagingApi(api_client)
                                        line_bot_api.push_message(
                                            PushMessageRequest(
                                                to=user_id,
                                                messages=[image_message]
                                            )
                                        )
                                    app.logger.info(f"✅ 使用 push_message 成功發送圖片")
                            except Exception as e2:
                                    app.logger.error(f"❌ push_message 也失敗: {e2}")
                                    reply_text = f"嗚...圖片發送失敗：{str(e2)}"
                                    # 不 return，繼續執行後續的文字回覆邏輯
                            
                            # 存入資料庫
                            return
                        else:
                            app.logger.error(f"❌ 占卜卡生成失敗，返回 URL 為 None")
                            reply_text = "嗚...占卜卡生成失敗了，請稍後再試～"
                            
                    except Exception as e:
                        app.logger.error(f"❌ 占卜卡功能失敗: {e}", exc_info=True)
                        reply_text = f"嗚...占卜過程中發生錯誤：{str(e)}"
                

                
                # 愛寵小語功能
                # 調用 API: https://test.ruru1211.xyz/api/pet-whisper/random?pet_id={pet_id}
                # 回覆圖片和文字
                elif user_message.lower() in ['愛寵小語', '小語', '寵物小語']:
                    try:
                        import requests
                        from linebot.v3.messaging import FlexMessage, FlexContainer

                        api_url = f"https://test.ruru1211.xyz/api/pet-whisper/random?pet_id={pet_id}"
                        app.logger.info(f"🔍 調用愛寵小語 API: {api_url}")
                        
                        response = requests.get(api_url, timeout=10)
                        response.raise_for_status()
                        data = response.json()
                        
                        if data.get('success', False):
                            whisper_data = data.get('data', {})
                            whisper_info = whisper_data.get('whisper', {})
                            whisper_text = whisper_info.get('content', '')
                            whisper_image = whisper_data.get('pet_image', '')
                            
                            app.logger.info(f"✅ 獲取愛寵小語成功: {whisper_text[:50]}...")
                            
                            if whisper_image and whisper_text:
                                # 建立 FlexMessage
                                flex_message = FlexMessage(
                                    alt_text="愛寵小語",
                                    contents=FlexContainer.from_dict({
                                        "type": "bubble",
                                        "body": {
                                            "type": "box",
                                            "layout": "vertical",
                                            "contents": [
                                                {
                                                    "type": "image",
                                                    "url": whisper_image,
                                                    "size": "full",
                                                    "aspectMode": "cover",
                                                    "aspectRatio": "1:1"
                                                },
                                                 {
                                                     "type": "text",
                                                     "text": f"{pet_name}：\n\n{whisper_text}",
                                                     "wrap": True,
                                                     "size": "md",
                                                     "margin": "md"
                                                 }
                                            ]
                                        }
                                    })
                                )

                                try:
                                    with ApiClient(configuration) as api_client:
                                        line_bot_api = MessagingApi(api_client)
                                        line_bot_api.reply_message_with_http_info(
                                            ReplyMessageRequest(
                                                reply_token=event.reply_token,
                                                messages=[flex_message]
                                            )
                                        )
                                except Exception as e:
                                    # reply_token 已失效，用 push_message 補救
                                    app.logger.warning(f"reply_token 失效，改用 push_message: {e}")
                                    with ApiClient(configuration) as api_client:
                                        line_bot_api = MessagingApi(api_client)
                                        line_bot_api.push_message(
                                            to=user_id,
                                            messages=[flex_message]
                                        )

                                return

                            elif whisper_text:
                                reply_text = f"{pet_name}：\n\n{whisper_text}"
                            else:
                                reply_text = "嗚...暫時沒有小語可以分享呢～"
                        else:
                            reply_text = "嗚...現在沒有小語可以分享呢～"

                    except Exception as e:
                        app.logger.error(f"❌ 愛寵小語 API 調用失敗: {e}")
                        reply_text = "嗚...現在無法獲取小語，請稍後再試～"

                else:
                    # 一般對話 - 從資料庫讀取對話歷史
                    history = get_chat_history(user_id, pet_id, limit=8)
                    
                    # 先儲存使用者的訊息
                    save_chat_message(user_id, pet_id, 'user', user_message)
                    
                    # 根據 AI_MODE 選擇對應的 chat_with_pet 函數
                    logger.info(f"💬 處理對話 - 用戶: {user_id}, 模式: {AI_MODE}")
                    logger.info(f"📝 輸入訊息: {user_message}")
                    
                    if AI_MODE == 'api':
                        logger.info(f"🌐 使用 API 模式 - 模型: {QWEN_MODEL}")
                        reply_text = chat_with_pet_api(
                            system_prompt=system_prompt,
                            user_input=user_message,
                            history=history,
                            model=QWEN_MODEL,
                            pet_name=pet_name
                        )
                        logger.info("✅ API 模式回應完成")
                    else:  # 預設使用 Ollama
                        logger.info(f"🏠 使用 Ollama 模式 - 模型: {OLLAMA_MODEL}")
                        reply_text = chat_with_pet_ollama(
                            system_prompt=system_prompt,
                            user_input=user_message,
                            history=history,
                            model=OLLAMA_MODEL,
                            pet_name=pet_name
                        )
                        logger.info("✅ Ollama 模式回應完成")
                    
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
