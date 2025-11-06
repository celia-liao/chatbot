# fortune_card.py
# ============================================
# 占卜卡生成相關功能
# ============================================

import os
import uuid
import random
import requests
import logging
from datetime import date
from PIL import Image, ImageDraw, ImageFont

# 獲取 logger
logger = logging.getLogger('pet_chatbot')

# 占卜卡配置常量
FORTUNE_CARD_CONFIG = {
    'CARD_WIDTH': 600,
    'CARD_HEIGHT': 1000,
    'PET_TARGET_SIZE': 280,
    'PET_Y_OFFSET': 250,
    'COVER_X': 0,
    'COVER_Y': 0,
    'FONT_SIZE': 32,
    'FONT_SIZE_FALLBACK': 16,
    'TEXT_X_OFFSET': 88,
    'TEXT_Y_BASE': 437,
    'CHAR_SPACING': 1.0,
    'TEXT_Y_FALLBACK': 900,
}


def _get_base_dir():
    """獲取應用程式基礎目錄的絕對路徑"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_output_dir():
    """獲取 output 目錄的絕對路徑"""
    base_dir = _get_base_dir()
    mybot_dir = os.path.join(base_dir, 'mybot')
    return os.path.join(mybot_dir, "output")


def _get_assets_dir():
    """獲取 assets 目錄的絕對路徑"""
    base_dir = _get_base_dir()
    return os.path.join(base_dir, "assets")


def _check_existing_fortune_card(pet_id, today, get_daily_fortune_card_func, EXTERNAL_URL):
    """
    檢查當日是否已生成占卜卡
    
    返回:
        str: 如果存在則返回 URL，否則返回 None
    """
    logger.info(f"🔍 [檢查占卜卡] 開始檢查: pet_id={pet_id}, date={today}")
    existing_filename = get_daily_fortune_card_func(pet_id, today)
    
    if existing_filename:
        logger.info(f"✅ [檢查占卜卡] 資料庫中找到記錄: filename={existing_filename}")
        output_dir = _get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        existing_path = os.path.join(output_dir, existing_filename)
        logger.info(f"🔍 [檢查占卜卡] 檢查文件是否存在: {existing_path}")
        
        if os.path.exists(existing_path):
            external_url = f"{EXTERNAL_URL}/line/output/{existing_filename}"
            logger.info(f"♻️  [檢查占卜卡] 使用當日已生成的占卜卡: pet_id={pet_id}, date={today}, filename={existing_filename}")
            logger.info(f"🔗 [檢查占卜卡] 生成的 URL: {external_url}")
            return external_url
        else:
            logger.warning(f"⚠️  [檢查占卜卡] 資料庫記錄的文件不存在: {existing_filename}, 路徑: {existing_path}")
            logger.warning(f"⚠️  [檢查占卜卡] 將重新生成新的占卜卡")
    else:
        logger.info(f"ℹ️  [檢查占卜卡] 資料庫中未找到當日記錄: pet_id={pet_id}, date={today}")
    
    return None


def _fetch_fortune_data(pet_id, BASE_URL):
    """
    從 API 獲取占卜卡數據
    
    返回:
        tuple: (pet_name, pet_image_url, cover_image_url) 或 (None, None, None)
    """
    api_url = f"{BASE_URL}/api/fortune-card/random?pet_id={pet_id}"
    logger.info(f"🔮 調用占卜卡 API (當日首次生成): {api_url}")
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        data = response.json()
        
        if not data.get('success', False):
            logger.error(f"❌ API 返回失敗: {data}")
            return None, None, None
        
        fortune_data = data.get('data', {})
        pet_name = fortune_data.get('pet_name', '')
        pet_image_url = fortune_data.get('pet_image', '')
        cover_image_url = fortune_data.get('cover_image', '')
        
        if not pet_name or not pet_image_url:
            logger.error(f"❌ API 數據不完整: {fortune_data}")
            return None, None, None
        
        # 確保 pet_name 是正確的字串格式
        if isinstance(pet_name, bytes):
            pet_name = pet_name.decode('utf-8')
        pet_name = str(pet_name).strip()
        
        logger.info(f"✅ 獲取寵物資料成功: {pet_name}, 頭像: {pet_image_url}")
        return pet_name, pet_image_url, cover_image_url
    
    except Exception as e:
        logger.error(f"❌ 獲取占卜卡數據失敗: {e}")
        return None, None, None


def _download_pet_image(pet_image_url):
    """
    下載寵物頭像圖片
    
    返回:
        str: 臨時文件路徑，失敗返回 None
    """
    try:
        pet_image_response = requests.get(pet_image_url, timeout=10)
        pet_image_response.raise_for_status()
        
        temp_pet_path = f'/tmp/pet_{uuid.uuid4()}.png'
        with open(temp_pet_path, 'wb') as f:
            f.write(pet_image_response.content)
        
        return temp_pet_path
    except Exception as e:
        logger.error(f"❌ 下載寵物頭像失敗: {e}")
        return None


def _process_pet_image(temp_pet_path):
    """
    處理寵物頭像，調整尺寸並放在背景上
    
    返回:
        Image: 處理後的寵物頭像背景圖
    """
    pet_image = Image.open(temp_pet_path).convert('RGBA')
    
    # 創建背景層
    pet_image_bg = Image.new('RGBA', (FORTUNE_CARD_CONFIG['CARD_WIDTH'], FORTUNE_CARD_CONFIG['CARD_HEIGHT']), (255, 255, 255, 0))
    
    # 調整尺寸
    target_size = FORTUNE_CARD_CONFIG['PET_TARGET_SIZE']
    pet_ratio = pet_image.width / pet_image.height
    
    if pet_ratio >= 1:
        new_width = target_size
        new_height = int(target_size / pet_ratio)
    else:
        new_height = target_size
        new_width = int(target_size * pet_ratio)
    
    resized_pet = pet_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 計算位置
    x_offset = (FORTUNE_CARD_CONFIG['CARD_WIDTH'] - new_width) // 2
    y_offset = FORTUNE_CARD_CONFIG['PET_Y_OFFSET']
    
    pet_image_bg.paste(resized_pet, (x_offset, y_offset), resized_pet)
    
    logger.info(f"✅ 寵物頭像處理完成: 原始尺寸 {pet_image.size}, 調整後 {resized_pet.size}, 位置 ({x_offset}, {y_offset})")
    
    return pet_image_bg


def _load_cover_image(cover_image_url):
    """
    加載覆蓋圖片（從 API 或本地）
    
    返回:
        Image: 覆蓋圖片，失敗返回 None
    """
    try:
        if cover_image_url:
            # 從 API 下載
            cover_response = requests.get(cover_image_url, timeout=10)
            cover_response.raise_for_status()
            
            temp_bg_path = f'/tmp/bg_{uuid.uuid4()}.png'
            with open(temp_bg_path, 'wb') as f:
                f.write(cover_response.content)
            
            cover_image = Image.open(temp_bg_path).convert('RGBA')
            cover_image = cover_image.resize((FORTUNE_CARD_CONFIG['CARD_WIDTH'], FORTUNE_CARD_CONFIG['CARD_HEIGHT']), Image.Resampling.LANCZOS)
            
            os.remove(temp_bg_path)
            return cover_image
        else:
            # 從本地隨機選擇
            assets_dir = _get_assets_dir()
            bg_dir = os.path.join(assets_dir, "images", "fortune_bg")
            
            if not os.path.exists(bg_dir):
                logger.error(f"❌ 覆蓋圖片目錄不存在: {bg_dir}")
                return None
            
            bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not bg_files:
                logger.error(f"❌ 覆蓋圖片目錄為空: {bg_dir}")
                return None
            
            random_bg = random.choice(bg_files)
            bg_path = os.path.join(bg_dir, random_bg)
            logger.info(f"🎲 隨機選擇覆蓋圖片: {random_bg}")
            
            cover_image = Image.open(bg_path).convert('RGBA')
            cover_image = cover_image.resize((FORTUNE_CARD_CONFIG['CARD_WIDTH'], FORTUNE_CARD_CONFIG['CARD_HEIGHT']), Image.Resampling.LANCZOS)
            
            return cover_image
    
    except Exception as e:
        logger.error(f"❌ 加載覆蓋圖片失敗: {e}")
        return None


def _load_font():
    """
    載入字型
    
    返回:
        tuple: (font, font_size) 或 (None, fallback_size)
    """
    font_size = FORTUNE_CARD_CONFIG['FONT_SIZE']
    assets_dir = _get_assets_dir()
    
    font_paths = [
        os.path.join(assets_dir, 'fonts', '粗線體.TTF'),
        os.path.join(assets_dir, 'fonts', '粗線體.ttf'),
        os.path.join(assets_dir, 'fonts', 'NotoSansTC-Regular.ttf'),
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/Library/Fonts/PingFang.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_path_lower = font_path.lower()
                if font_path_lower.endswith('.ttc'):
                    font = ImageFont.truetype(font_path, font_size, index=0)
                elif font_path_lower.endswith(('.ttf', '.otf')):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.truetype(font_path, font_size)
                
                logger.info(f"✅ 載入字型成功: {font_path}, 大小: {font_size}")
                return font, font_size
            except Exception as e:
                logger.warning(f"⚠️ 載入字型失敗 {font_path}: {e}")
                continue
    
    # 如果所有字型都無法載入，使用預設字型
    logger.error(f"❌ 無法載入任何中文字型，中文可能顯示為方塊")
    fonts_dir = os.path.join(assets_dir, 'fonts')
    logger.error(f"💡 請將 NotoSansTC-Regular.ttf 放在 {fonts_dir} 目錄")
    font = ImageFont.load_default()
    font_size = FORTUNE_CARD_CONFIG['FONT_SIZE_FALLBACK']
    
    return font, font_size


def _draw_text(draw, text_content, font, font_size):
    """
    在圖片上繪製垂直排列的文字
    
    參數:
        draw: ImageDraw 對象
        text_content: 要繪製的文字
        font: 字型對象
        font_size: 字體大小
    """
    # 確保文字是正確的 Unicode 字串
    if isinstance(text_content, bytes):
        text_content = text_content.decode('utf-8')
    text_content = str(text_content).strip()
    
    logger.info(f"🔍 準備繪製文字（垂直排列）: '{text_content}'")
    
    text_x_offset = FORTUNE_CARD_CONFIG['TEXT_X_OFFSET']
    text_y_base = FORTUNE_CARD_CONFIG['TEXT_Y_BASE']
    char_spacing = FORTUNE_CARD_CONFIG['CHAR_SPACING']
    
    try:
        # 計算第一個字符的寬度以確定水平位置
        first_char = text_content[0] if text_content else ''
        if first_char:
            char_bbox = draw.textbbox((0, 0), first_char, font=font)
            char_width = char_bbox[2] - char_bbox[0]
            text_x = (FORTUNE_CARD_CONFIG['CARD_WIDTH'] - char_width) // 2 + text_x_offset
        else:
            text_x = FORTUNE_CARD_CONFIG['CARD_WIDTH'] // 2 + text_x_offset
        
        # 計算每個字符的高度
        sample_char = '字' if text_content else 'A'
        char_bbox = draw.textbbox((0, 0), sample_char, font=font)
        char_height = char_bbox[3] - char_bbox[1]
        char_height_adjusted = int(char_height * char_spacing)
        
        # 計算垂直文字的總高度
        total_height = len(text_content) * char_height_adjusted
        start_y = text_y_base - total_height
        
        # 逐個字符垂直繪製
        current_y = start_y
        for char in text_content:
            draw.text((text_x, current_y), char, fill=(255, 255, 255, 255), font=font)
            current_y += char_height_adjusted
        
        logger.info(f"✅ 垂直文字繪製完成: '{text_content}' 起始位置: ({text_x}, {start_y})")
    
    except Exception as e:
        logger.error(f"❌ 垂直文字繪製失敗: {e}")
        # 嘗試使用水平方式作為備用
        try:
            text_bbox = draw.textbbox((0, 0), text_content, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (FORTUNE_CARD_CONFIG['CARD_WIDTH'] - text_width) // 2
            draw.text((text_x, FORTUNE_CARD_CONFIG['TEXT_Y_FALLBACK']), text_content, fill=(255, 255, 255, 255), font=font)
            logger.info(f"✅ 使用水平備用方式繪製文字成功")
        except Exception as e2:
            logger.error(f"❌ 備用文字繪製也失敗: {e2}")


def _composite_images(pet_image_bg, cover_image):
    """
    合成占卜卡圖片
    
    返回:
        Image: 合成後的圖片
    """
    composite_image = Image.new('RGBA', (FORTUNE_CARD_CONFIG['CARD_WIDTH'], FORTUNE_CARD_CONFIG['CARD_HEIGHT']))
    
    # 第一層：貼上寵物頭像作為背景
    composite_image.paste(pet_image_bg, (0, 0))
    logger.info(f"✅ 第一層：寵物頭像背景已貼上")
    
    # 第二層：疊加覆蓋圖片
    cover_x = FORTUNE_CARD_CONFIG['COVER_X']
    cover_y = FORTUNE_CARD_CONFIG['COVER_Y']
    cover_position = (cover_x, cover_y)
    
    if cover_image.mode == 'RGBA':
        composite_image.paste(cover_image, cover_position, cover_image)
        logger.info(f"✅ 第二層：覆蓋圖片已疊加（使用 RGBA alpha 通道），位置: {cover_position}")
    else:
        composite_image.paste(cover_image, cover_position)
        logger.warning(f"⚠️ 覆蓋圖片沒有 alpha 通道，會完全覆蓋寵物頭像，位置: {cover_position}")
    
    logger.info(f"✅ 圖片合成完成（寵物頭像在下，覆蓋圖片在上，透明區域顯示寵物）")
    
    return composite_image


def generate_fortune_card(pet_id, BASE_URL, EXTERNAL_URL, get_daily_fortune_card_func, save_daily_fortune_card_func):
    """
    生成寵物占卜卡（主函數）
    
    參數:
        pet_id: 寵物 ID
        BASE_URL: API 基礎 URL
        EXTERNAL_URL: 外部訪問 URL
        get_daily_fortune_card_func: 獲取每日占卜卡函數
        save_daily_fortune_card_func: 保存每日占卜卡函數
    
    返回:
        str: 生成的占卜卡圖片外部 URL，如果失敗則返回 None
    """
    temp_pet_path = None
    
    try:
        # 0. 檢查當日是否已生成占卜卡
        today = date.today().strftime('%Y-%m-%d')
        logger.info(f"📅 [生成占卜卡] 開始處理: pet_id={pet_id}, date={today}")
        
        existing_url = _check_existing_fortune_card(pet_id, today, get_daily_fortune_card_func, EXTERNAL_URL)
        if existing_url:
            logger.info(f"✅ [生成占卜卡] 返回已存在的占卜卡: {existing_url}")
            return existing_url
        
        logger.info(f"📝 [生成占卜卡] 當日尚未生成，開始生成新的占卜卡: pet_id={pet_id}, date={today}")
        
        # 1. 確保 output 目錄存在
        output_dir = _get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        
        # 2. 獲取占卜卡數據
        pet_name, pet_image_url, cover_image_url = _fetch_fortune_data(pet_id, BASE_URL)
        if not pet_name or not pet_image_url:
            return None
        
        # 3. 下載寵物頭像
        temp_pet_path = _download_pet_image(pet_image_url)
        if not temp_pet_path:
            return None
        
        # 4. 處理寵物頭像
        pet_image_bg = _process_pet_image(temp_pet_path)
        
        # 5. 加載覆蓋圖片
        cover_image = _load_cover_image(cover_image_url)
        if not cover_image:
            os.remove(temp_pet_path)
            return None
        
        logger.info(f"✅ 覆蓋圖片處理完成: {cover_image.size}, 模式: {cover_image.mode}")
        
        # 6. 合成圖片
        composite_image = _composite_images(pet_image_bg, cover_image)
        
        # 7. 添加文字
        draw = ImageDraw.Draw(composite_image)
        font, font_size = _load_font()
        _draw_text(draw, pet_name, font, font_size)
        
        # 8. 轉換回 RGB 模式並保存
        final_image = composite_image.convert('RGB')
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(output_dir, filename)
        final_image.save(output_path, 'PNG')
        logger.info(f"✅ 占卜卡保存成功: {output_path}")
        
        # 9. 清理臨時文件
        if temp_pet_path and os.path.exists(temp_pet_path):
            os.remove(temp_pet_path)
        
        # 10. 保存到資料庫
        logger.info(f"💾 [保存資料庫] 準備保存: pet_id={pet_id}, date={today}, filename={filename}")
        save_success = save_daily_fortune_card_func(pet_id, filename, today)
        if save_success:
            logger.info(f"✅ [保存資料庫] 保存成功: pet_id={pet_id}, date={today}, filename={filename}")
            # 立即驗證保存是否成功
            verify_filename = get_daily_fortune_card_func(pet_id, today)
            if verify_filename == filename:
                logger.info(f"✅ [保存資料庫] 驗證成功: 資料庫記錄與保存的文件名一致")
            else:
                logger.error(f"❌ [保存資料庫] 驗證失敗: 期望={filename}, 實際={verify_filename}")
                logger.error(f"❌ [保存資料庫] 這可能導致每次調用都生成新的占卜卡！")
        else:
            logger.error(f"❌ [保存資料庫] 保存失敗: pet_id={pet_id}, date={today}, filename={filename}")
            logger.error(f"❌ [保存資料庫] 這可能導致每次調用都生成新的占卜卡！")
        
        # 11. 返回外部 URL
        external_url = f"{EXTERNAL_URL}/line/output/{filename}"
        logger.info(f"🔗 [生成占卜卡] 完成，返回 URL: {external_url}")
        return external_url
    
    except Exception as e:
        logger.error(f"❌ 生成占卜卡失敗: {e}", exc_info=True)
        # 清理臨時文件
        if temp_pet_path and os.path.exists(temp_pet_path):
            try:
                os.remove(temp_pet_path)
            except:
                pass
        return None

