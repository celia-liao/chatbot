# line_handlers.py
# ============================================
# LINE Bot 事件處理相關功能
# ============================================

import logging
import requests
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    ImageMessage,
    FlexMessage,
    FlexContainer
)

# 導入情緒檢測模組
try:
    from mybot.modules.emotion_detector import detect_emotion
except ImportError:
    from modules.emotion_detector import detect_emotion

logger = logging.getLogger('pet_chatbot')


def _handle_my_id_command(user_id, pet_id):
    """處理「我的ID」指令"""
    if pet_id:
        return f"""🆔 你的使用者資訊

LINE User ID:
{user_id}

✅ 你已經設定好寵物了，可以直接聊天喔～"""
    else:
        return f"""🆔 你的使用者資訊

LINE User ID:
{user_id}

⚠️ 你還沒有設定專屬寵物喔！

請將上面的 User ID 複製後，提供給客服人員進行設定。設定完成後就可以開始和你的虛擬寵物聊天囉！

📞 需要協助請聯絡客服"""


def _handle_clear_command(user_id, pet_id, clear_chat_history_func):
    """處理「清除」指令"""
    clear_chat_history_func(user_id, pet_id)
    return "嗚！我忘記之前的對話了，我們重新開始吧！"


def _handle_help_command():
    """處理「說明」指令"""
    return """🐕 寵物聊天機器人使用說明

• 直接傳送訊息，我會像寵物一樣回覆你
• 輸入「清除」可以重置對話記錄
• 輸入「說明」查看此訊息
• 輸入「我的ID」查看你的使用者ID
• 輸入「愛寵小語」獲取專屬小語
• 輸入「占卜」或「/fortune」生成占卜卡

快來跟我聊天吧！～"""


def _handle_fortune_command(user_id, pet_id, generate_fortune_card_func, configuration):
    """
    處理占卜卡指令
    
    返回:
        tuple: (should_return, reply_text) - should_return=True 表示已處理完畢，不需要繼續處理
    """
    try:
        logger.info(f"🔮 用戶 {user_id} 請求占卜卡")
        
        fortune_card_url = generate_fortune_card_func(pet_id)
        
        if fortune_card_url:
            logger.info(f"✅ 占卜卡生成成功，URL: {fortune_card_url}")
            
            image_message = ImageMessage(
                original_content_url=fortune_card_url,
                preview_image_url=fortune_card_url
            )
            
            logger.info(f"📤 準備發送圖片到 LINE，URL: {fortune_card_url}")
            
            try:
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.push_message(
                        PushMessageRequest(
                            to=user_id,
                            messages=[image_message]
                        )
                    )
                logger.info(f"✅ 使用 push_message 成功發送圖片")
                return True, None  # 已處理，不需要文字回覆
            except Exception as e2:
                logger.error(f"❌ push_message 也失敗: {e2}")
                return False, f"嗚...圖片發送失敗：{str(e2)}"
        else:
            logger.error(f"❌ 占卜卡生成失敗，返回 URL 為 None")
            return False, "嗚...占卜卡生成失敗了，請稍後再試～"
    
    except Exception as e:
        logger.error(f"❌ 占卜卡功能失敗: {e}", exc_info=True)
        return False, f"嗚...占卜過程中發生錯誤：{str(e)}"


def _build_emotion_context(emotion_result: dict, pet_name: str) -> str:
    """
    根據情緒分析結果建立上下文提示詞
    
    參數:
        emotion_result (dict): 情緒分析結果，包含 emotion, confidence, polarity
        pet_name (str): 寵物名字
    
    返回:
        str: 情緒上下文提示詞
    """
    if not emotion_result:
        return ""
    
    emotion = emotion_result.get('emotion', 'contentment')
    polarity = emotion_result.get('polarity', 'positive')
    confidence = emotion_result.get('confidence', 0.5)
    
    # 情緒描述映射
    emotion_descriptions = {
        'amusement': '開心和有趣',
        'awe': '感到驚嘆和震撼',
        'contentment': '滿足和安心',
        'excitement': '興奮和期待',
        'anger': '生氣和憤怒',
        'disgust': '感到厭惡和反感',
        'fear': '害怕和擔心',
        'sad': '難過和沮喪'
    }
    
    emotion_desc = emotion_descriptions.get(emotion, '情緒平靜')
    
    # 根據情緒強度調整描述
    if confidence >= 0.8:
        intensity_desc = "非常" if polarity == "positive" else "相當"
    elif confidence >= 0.6:
        intensity_desc = "有點" if polarity == "positive" else "稍微"
    else:
        intensity_desc = "略微"
    
    context = f"主人現在{intensity_desc}{emotion_desc}（情緒：{emotion}，信心度：{confidence:.1%}）"
    
    return context


def _handle_whisper_command(user_id, pet_id, pet_name, BASE_URL, configuration, event):
    """
    處理「愛寵小語」指令
    
    返回:
        tuple: (should_return, reply_text) - should_return=True 表示已處理完畢
    """
    try:
        api_url = f"{BASE_URL}/api/pet-whisper/random?pet_id={pet_id}"
        logger.info(f"🔍 調用愛寵小語 API: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success', False):
            whisper_data = data.get('data', {})
            whisper_info = whisper_data.get('whisper', {})
            whisper_text = whisper_info.get('content', '')
            whisper_image = whisper_data.get('pet_image', '')
            
            logger.info(f"✅ 獲取愛寵小語成功: {whisper_text[:50]}...")
            
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
                    return True, None  # 已處理
                except Exception as e:
                    # reply_token 已失效，用 push_message 補救
                    logger.warning(f"reply_token 失效，改用 push_message: {e}")
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.push_message(
                            PushMessageRequest(
                                to=user_id,
                                messages=[flex_message]
                            )
                        )
                    return True, None  # 已處理
            
            elif whisper_text:
                return False, f"{pet_name}：\n\n{whisper_text}"
            else:
                return False, "嗚...暫時沒有小語可以分享呢～"
        else:
            return False, "嗚...現在沒有小語可以分享呢～"
    
    except Exception as e:
        logger.error(f"❌ 愛寵小語 API 調用失敗: {e}")
        return False, "嗚...現在無法獲取小語，請稍後再試～"


def handle_text_message(event, get_pet_id_by_line_user_func, get_pet_system_prompt_func,
                       clear_chat_history_func, save_chat_message_func, get_chat_history_func,
                       chat_with_pet_api_func, chat_with_pet_ollama_func, generate_fortune_card_func,
                       BASE_URL, AI_MODE, QWEN_MODEL, OLLAMA_MODEL, configuration):
    """
    處理文字訊息事件（主函數）
    
    參數:
        event: LINE MessageEvent 物件
        ... (其他依賴函數和配置)
    
    返回:
        None (直接處理 LINE 回覆)
    """
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    
    logger.info(f"使用者 {user_id} 說：{user_message}")
    
    try:
        # 檢查使用者是否已設定寵物
        pet_id = get_pet_id_by_line_user_func(user_id)
        logger.info(f"使用者 {user_id} 綁定的 pet_id: {pet_id}")
        
        reply_text = None
        should_return = False
        
        # 處理特殊指令
        user_message_lower = user_message.lower()
        
        # 「我的ID」指令
        if user_message_lower in ['我的id', '我的ID', 'myid', 'my id', 'userid', 'user id']:
            reply_text = _handle_my_id_command(user_id, pet_id)
        
        # 未設定寵物
        elif not pet_id:
            reply_text = """👋 哈囉！歡迎使用寵物聊天機器人！

⚠️ 你還沒有設定專屬寵物喔！

請先在聊天視窗輸入「我的ID」，系統會顯示你的 LINE User ID。

將該 ID 複製後提供給客服人員進行設定，設定完成後就可以開始聊天囉！"""
        
        # 已設定寵物，處理其他指令
        else:
            system_prompt, pet_name = get_pet_system_prompt_func(pet_id)
            logger.info(f"載入寵物資料 - pet_id: {pet_id}, pet_name: {pet_name}")
            
            if not system_prompt:
                reply_text = "嗚...主人，我現在記不起來自己是誰了 😢\n請稍後再試試看"
            else:
                # 「清除」指令
                if user_message_lower in ['clear', '清除', '重置']:
                    reply_text = _handle_clear_command(user_id, pet_id, clear_chat_history_func)
                
                # 「說明」指令
                elif user_message_lower in ['help', '幫助', '說明']:
                    reply_text = _handle_help_command()
                
                # 「占卜」指令
                elif user_message_lower in ['毛孩占卜', '/fortune']:
                    should_return, reply_text = _handle_fortune_command(
                        user_id, pet_id, generate_fortune_card_func, configuration
                    )
                    if should_return:
                        return  # 已處理完畢，不需要文字回覆
                
                # 「愛寵小語」指令
                elif user_message_lower in ['愛寵小語', '小語', '寵物小語']:
                    should_return, reply_text = _handle_whisper_command(
                        user_id, pet_id, pet_name, BASE_URL, configuration, event
                    )
                    if should_return:
                        return  # 已處理完畢
                
                # 一般對話
                else:
                    # 1️⃣ 情緒辨識模組
                    logger.info(f"🎭 開始情緒分析 - 用戶: {user_id}")
                    emotion_result = detect_emotion(user_message)
                    logger.info(f"✅ 情緒分析結果: {emotion_result}")
                    
                    # 根據情緒生成上下文提示
                    emotion_context = _build_emotion_context(emotion_result, pet_name)
                    
                    # 將情緒上下文加入 system_prompt
                    enhanced_system_prompt = system_prompt
                    if emotion_context:
                        enhanced_system_prompt = f"{system_prompt}\n\n        💭 主人現在的情緒狀態：\n        {emotion_context}\n        - 請根據主人的情緒狀態調整你的回應方式\n        - 如果主人情緒低落，要溫柔安慰\n        - 如果主人情緒正向，可以更活潑開心地回應\n"
                    
                    history = get_chat_history_func(user_id, pet_id, limit=8)
                    save_chat_message_func(user_id, pet_id, 'user', user_message)
                    
                    logger.info(f"💬 處理對話 - 用戶: {user_id}, 模式: {AI_MODE}")
                    logger.info(f"📝 輸入訊息: {user_message}")
                    logger.info(f"🎭 情緒: {emotion_result['emotion']} ({emotion_result['polarity']}, 信心度: {emotion_result['confidence']:.2f})")
                    
                    if AI_MODE == 'api':
                        logger.info(f"🌐 使用 API 模式 - 模型: {QWEN_MODEL}")
                        reply_text = chat_with_pet_api_func(
                            system_prompt=enhanced_system_prompt,
                            user_input=user_message,
                            history=history,
                            model=QWEN_MODEL,
                            pet_name=pet_name
                        )
                        logger.info("✅ API 模式回應完成")
                    else:
                        logger.info(f"🏠 使用 Ollama 模式 - 模型: {OLLAMA_MODEL}")
                        reply_text = chat_with_pet_ollama_func(
                            system_prompt=enhanced_system_prompt,
                            user_input=user_message,
                            history=history,
                            model=OLLAMA_MODEL,
                            pet_name=pet_name
                        )
                        logger.info("✅ Ollama 模式回應完成")
                    
                    save_chat_message_func(user_id, pet_id, 'assistant', reply_text)
        
        # 回覆訊息
        if reply_text:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )
            
            logger.info(f"回覆使用者 {user_id}：{reply_text}")
    
    except Exception as e:
        logger.error(f"處理訊息時發生錯誤: {e}", exc_info=True)
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

