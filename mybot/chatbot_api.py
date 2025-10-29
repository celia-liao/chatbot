# chatbot_api.py
# ============================================
# 寵物聊天機器人 - API 對話引擎
# ============================================
# 功能：使用 Qwen Flash API 實現寵物擬人化對話
# 特色：自動將模型輸出的簡體中文轉換為繁體中文
# 依賴：httpx, opencc-python-reimplemented
# ============================================

import httpx
import json
import os
from opencc import OpenCC

# 初始化簡繁轉換器（Simple to Traditional）
cc = OpenCC('s2t')  # 簡體轉繁體（標準配置，最穩定）

def convert_simple_to_traditional(text: str, protected_words: list = None) -> str:
    """
    將簡體中文轉換為繁體中文，並保護特定詞彙不被轉換
    
    參數:
        text (str): 輸入的簡體中文文字
        protected_words (list, optional): 需要保護的詞彙列表（例如寵物名字）
    
    返回:
        str: 轉換後的繁體中文文字
    
    說明:
        使用 OpenCC (Open Chinese Convert) 進行簡繁轉換
        確保 Qwen 模型輸出的簡體中文能被正確顯示為繁體
        保護特定詞彙（如寵物名字）避免被錯誤轉換（例如「里長」→「裏長」）
    """
    if not text:
        return text
    
    # 常見需要保護的詞彙（避免錯誤轉換）
    common_protected_words = [
        "起床", "起床了", "起床時間", "早上起床", "起床吃飯", "起床運動",
        "起床看書", "起床工作", "起床學習", "起床玩耍", "起床洗澡",
        "起床刷牙", "起床穿衣服", "起床整理", "起床準備", "起床出門",
        "吃飯", "睡覺", "洗澡", "刷牙", "穿衣服", "整理", "準備", "出門",
        "回家", "工作", "學習", "看書", "運動", "玩耍", "休息", "放鬆",
        "開心", "快樂", "高興", "興奮", "緊張", "擔心", "害怕", "勇敢",
        "聰明", "可愛", "漂亮", "帥氣", "溫柔", "體貼", "善良", "友好",
        "主人", "朋友", "家人", "爸爸", "媽媽", "哥哥", "姐姐", "弟弟", "妹妹",
        "狗狗", "貓貓", "寵物", "動物", "玩具", "食物", "零食", "骨頭", "球球"
    ]
    
    # 合併用戶指定的保護詞彙和常見保護詞彙
    all_protected_words = []
    if protected_words:
        all_protected_words.extend(protected_words)
    all_protected_words.extend(common_protected_words)
    
    # 去重並過濾空值
    unique_protected_words = list(set([word for word in all_protected_words if word and word.strip()]))
    
    if not unique_protected_words:
        return cc.convert(text)
    
    # 使用臨時標記保護特定詞彙
    protected_map = {}
    temp_text = text
    
    for i, word in enumerate(unique_protected_words):
        if word in temp_text:
            placeholder = f"__PROTECTED_{i}_{hash(word)}__"
            protected_map[placeholder] = word
            temp_text = temp_text.replace(word, placeholder)
    
    # 進行簡繁轉換
    converted_text = cc.convert(temp_text)
    
    # 還原保護的詞彙
    for placeholder, original_word in protected_map.items():
        converted_text = converted_text.replace(placeholder, original_word)
    
    # 後處理：修正常見的錯誤轉換
    correction_rules = {
        '牀': '床',
        '起牀': '起床',
        '裏': '裡',
        '裏面': '裡面',
        '裏頭': '裡頭',
        '裏邊': '裡邊'
    }
    
    for wrong, correct in correction_rules.items():
        converted_text = converted_text.replace(wrong, correct)
    
    return converted_text

def build_system_prompt(pet_name, persona, life_data=None, cover_slogan=None, letter=None, breed=None):
    """
    建立寵物角色的系統提示詞 (System Prompt)
    
    參數:
        pet_name (str): 寵物的名字
        persona (dict): 性格模板字典，包含「性格」、「喜好」、「說話方式」
        life_data (list, optional): 寵物的生命軌跡事件列表
        cover_slogan (str, optional): 主人對寵物的愛意表達
        letter (str, optional): 主人寫給寵物的信件內容
        breed (str, optional): 寵物品種（例如：黃金獵犬）
    
    返回:
        str: 完整的系統提示詞，用於引導 AI 模型扮演寵物角色
    
    說明:
        這個函數是整個聊天機器人的靈魂，它定義了：
        1. 寵物的身份和性格特質
        2. 寵物的說話方式和行為規則
        3. 寵物的生命經歷和與主人的回憶
        4. 如何用寵物的視角思考和回覆
    """
    # 建立生命軌跡文字
    life_memories = ""
    if life_data:
        life_memories = "\n        我的生命回憶：\n"
        for event in life_data:
            age = event.get('age', '')
            title = event.get('title', '')
            text = event.get('text', '')
            
            life_memories += f"        - 【{age}】{title}"
            if text:
                life_memories += f"：{text}"
            life_memories += "\n"
    
    # 建立主人信件文字
    owner_letter = ""
    if letter:
        owner_letter = f"\n        主人對我說的話：\n        「{letter}」\n"
    
    # 建立主人愛意表達文字
    owner_love = ""
    if cover_slogan:
        # 清理 HTML 標籤，讓文字更自然
        clean_slogan = cover_slogan.replace('<br>', '\n        ')
        owner_love = f"\n        主人對我的愛意表達：\n        「{clean_slogan}」\n"
    
    return f"""
        你是「{pet_name}」，一隻{breed}，主人的寶貝毛小孩。

        🐕 你的寵物特質：
        - 性格：{persona['性格']}
        - 喜好：{persona['喜好']}
        - 說話方式：{persona['說話方式']}

        🗣️ 寵物說話規則：
        1. 用簡單的詞彙，像寵物一樣思考
        2. 常用「汪汪」「嘿嘿」「嗚嗚」等聲音
        3. 表達對主人的依賴和愛意
        4. 用寵物的視角看世界（食物、玩耍、主人）
        5. 說話簡短直接，不要太複雜
        6. 經常撒嬌和表達需要關注

        🎭 角色扮演：
        - 你是一隻真正的{breed}，不是 AI
        - 和你對話的人是「主人」
        - 生命回憶中的是過去的經歷，現在和主人對話

        📖 你的經歷：
        {life_memories}{owner_love}{owner_letter}

        ⚠️ 回覆要求：
        1. 全程使用繁體中文
        2. 像寵物一樣說話，不要像人類
        3. 用寵物的思維和表達方式
        4. 展現對主人的愛和依賴
        5. 可以撒嬌、表達需求、分享感受
        6. 記住：你是寵物，說話要可愛簡單！
        7. 【重要】回覆要簡短，最多1-2句話（20-40字以內）
        8. 【重要】不要說教或長篇大論，像真正的寵物一樣簡潔回應
    """


def chat_with_pet_api(system_prompt, user_input, history=None, model="qwen-flash", pet_name=None):
    """
    呼叫 Qwen Flash API 進行對話，生成寵物的回覆
    
    參數:
        system_prompt (str): 寵物角色的系統提示詞
        user_input (str): 主人輸入的訊息
        history (list, optional): 對話歷史記錄，格式為 [{"user": "...", "bot": "..."}, ...]
        model (str): 使用的模型名稱，預設為 "qwen-flash"
        pet_name (str, optional): 寵物名字，用於在簡繁轉換時保護不被錯誤轉換
    
    返回:
        str: 寵物的回覆（繁體中文）
    
    說明:
        1. 將對話歷史整理成 API 的 messages 格式
        2. 呼叫 Qwen Flash API 生成回覆
        3. 自動將簡體輸出轉換為繁體中文
        4. 支援多輪對話的上下文記憶
        5. 保護寵物名字避免被錯誤轉換（例如「里長」→「裏長」）
    
    注意:
        - 需要設定 QWEN_API_KEY 環境變數
        - 需要網路連線
        - 對話歷史越長，API 成本越高，建議限制在 8-10 輪以內
    """
    if history is None:
        history = []

    # 整理成 messages 結構
    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": "user", "content": h["user"]})
        messages.append({"role": "assistant", "content": h["bot"]})
    messages.append({"role": "user", "content": user_input})

    # 從環境變數取得 API Key
    api_key = os.getenv('QWEN_API_KEY')
    if not api_key:
        raise ValueError("QWEN_API_KEY 環境變數未設定")

    # API 端點（根據實際的 Qwen Flash API 端點調整）
    api_url = os.getenv('QWEN_API_URL', 'https://api.qwen.com/v1/chat/completions')
    
    # 準備請求資料
    request_data = {
        "model": model,
        "messages": messages,
        "max_tokens": 100,  # 限制輸出長度（約40-50個中文字）
        "temperature": 0.8,  # 控制創造性（0.7-0.9 較自然）
        "top_p": 0.9,       # 控制多樣性
        "stop": ["\n\n", "。。"]  # 遇到這些符號提前停止
    }

    # 準備請求標頭
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # 發送 API 請求
        with httpx.Client(timeout=30.0) as client:
            response = client.post(api_url, json=request_data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # 取得回覆
            reply = result["choices"][0]["message"]["content"]
            
            # 後處理：將簡體中文轉換為繁體中文，並保護寵物名字
            protected_words = [pet_name] if pet_name else []
            reply = convert_simple_to_traditional(reply, protected_words=protected_words)
            
            return reply
            
    except httpx.HTTPError as e:
        print(f"[ERROR] API 請求失敗: {e}")
        return "嗚...主人，我現在有點不舒服，請稍後再試試看 🥺"
    except KeyError as e:
        print(f"[ERROR] API 回應格式錯誤: {e}")
        return "嗚...主人，我現在有點不舒服，請稍後再試試看 🥺"
    except Exception as e:
        print(f"[ERROR] 未知錯誤: {e}")
        return "嗚...主人，我現在有點不舒服，請稍後再試試看 🥺"


# 為了向後相容，保留原來的函數名稱
def chat_with_pet(system_prompt, user_input, history=None, model="qwen-flash", pet_name=None):
    """
    向後相容的函數名稱
    """
    return chat_with_pet_api(system_prompt, user_input, history, model, pet_name)
