# modules/emotion_detector.py
# ============================================
# 情緒辨識模組
# ============================================
# 功能：使用本地 LLM 分析中文文字的情緒
# 依賴：ollama, opencc-python-reimplemented
# ============================================

import json
import logging
import re
import ollama
from opencc import OpenCC

logger = logging.getLogger('pet_chatbot')

# 初始化簡繁轉換器（Traditional to Simple）
# 用於將輸入文字統一轉換為簡體，提高模型理解準確度
cc_t2s = OpenCC('t2s')  # 繁體轉簡體


class EmotionDetector:
    """
    情緒分析器類別
    
    使用本地 LLM (Ollama) 分析中文文字的情緒類別
    支援 8 種情緒分類：amusement, awe, contentment, excitement (正向);
                       anger, disgust, fear, sad (負向)
    """
    
    def __init__(self, model: str = "qwen:7b", temperature: float = 0.3):
        """
        初始化情緒分析器
        
        參數:
            model (str): Ollama 模型名稱，預設為 "qwen:7b"
            temperature (float): 模型溫度參數，預設為 0.3（較穩定）
        """
        self.model = model
        self.temperature = temperature
        
        # 定義系統提示詞
        self.system_prompt = """你是一個情緒分析助手，負責判斷文字情緒。
可用的情緒類別：
正向情緒：amusement, awe, contentment, excitement
負向情緒：anger, disgust, fear, sad

請分析輸入文字的情緒類別，並依據語氣判斷其正向或負向。
回覆格式：
{
    "emotion": "<emotion>",
    "confidence": <0~1之間的數值>,
    "polarity": "<positive或negative>"
}
請勿輸出除JSON以外的內容。"""
        
        logger.info(f"EmotionDetector 初始化完成，使用模型: {model}")
    
    def _extract_json_from_response(self, text: str) -> dict:
        """
        從模型回應中提取 JSON 格式
        
        參數:
            text (str): 模型原始回應
        
        返回:
            dict: 解析後的 JSON 字典，若解析失敗則返回 None
        """
        if not text:
            return None
        
        # 定義情緒映射表（處理模型可能返回的變體）
        emotion_mapping = {
            "positive": "contentment",  # 通用正向情緒
            "negative": "sad",          # 通用負向情緒
            "happy": "excitement",
            "happiness": "excitement",
            "joy": "excitement",
            "sadness": "sad",
            "disappointed": "sad",
            "disappointment": "sad",
            "disgusting": "disgust",
            "scared": "fear",
            "scary": "fear",
            "angry": "anger",
            "amused": "amusement",
            "excited": "excitement",
            "content": "contentment",
            "satisfied": "contentment",
            "satisfaction": "contentment",
            "amazed": "awe",
            "surprised": "awe",
            "wonder": "awe"
        }
        
        # 嘗試直接解析 JSON
        try:
            # 移除可能的 markdown 代碼塊標記
            text = text.strip()
            if text.startswith('```'):
                # 移除 ```json 或 ``` 標記
                text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
                text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
            
            # 嘗試解析 JSON
            result = json.loads(text.strip())
            
            # 驗證必要欄位
            if all(key in result for key in ['emotion', 'confidence', 'polarity']):
                # 映射情緒名稱
                emotion = result['emotion'].lower()
                if emotion in emotion_mapping:
                    result['emotion'] = emotion_mapping[emotion]
                return result
        except json.JSONDecodeError:
            # 如果直接解析失敗，嘗試提取 JSON 物件
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    if all(key in result for key in ['emotion', 'confidence', 'polarity']):
                        # 映射情緒名稱
                        emotion = result['emotion'].lower()
                        if emotion in emotion_mapping:
                            result['emotion'] = emotion_mapping[emotion]
                        return result
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def detect_emotion(self, text: str) -> dict:
        """
        分析文字情緒
        
        參數:
            text (str): 輸入的中文文字
        
        返回:
            dict: 情緒分析結果，格式如下：
                {
                    "emotion": str,      # 情緒類別（amusement, awe, contentment, excitement, anger, disgust, fear, sad）
                    "confidence": float, # 信心度（0.0-1.0）
                    "polarity": str      # 情緒極性（"positive" 或 "negative"）
                }
        
        說明:
            使用本地 LLM 模型分析文字情緒
            若模型回應無效或解析失敗，則返回預設值（contentment, 0.5, positive）
        """
        if not text or not text.strip():
            return {
                "emotion": "contentment",
                "confidence": 0.5,
                "polarity": "positive"
            }
        
        try:
            # 將繁體中文轉換為簡體，提高模型理解準確度
            text_simplified = cc_t2s.convert(text.strip())
            
            # 構建訊息
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"請分析以下文字的情緒：\n{text_simplified}"}
            ]
            
            # 呼叫 Ollama API
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature
                }
            )
            
            # 取得回應內容
            reply = response["message"]["content"]
            
            # 解析 JSON
            result = self._extract_json_from_response(reply)
            
            if result:
                # 驗證情緒類別是否有效
                valid_emotions = [
                    "amusement", "awe", "contentment", "excitement",
                    "anger", "disgust", "fear", "sad"
                ]
                
                emotion = result["emotion"].lower()
                
                # 如果情緒不在有效列表中，嘗試映射或根據極性選擇預設值
                if emotion not in valid_emotions:
                    # 根據 polarity 選擇最接近的情緒
                    polarity_hint = result.get("polarity", "").lower()
                    if "positive" in polarity_hint or polarity_hint == "true":
                        emotion = "contentment"  # 預設正向情緒
                    elif "negative" in polarity_hint or polarity_hint == "false":
                        emotion = "sad"  # 預設負向情緒
                    else:
                        emotion = "contentment"  # 完全無法判斷時使用預設
                
                # 確保 confidence 在 0-1 範圍內
                confidence = float(result.get("confidence", 0.5))
                confidence = max(0.0, min(1.0, confidence))
                
                # 確保 polarity 正確
                polarity = result.get("polarity", "").lower()
                if polarity not in ["positive", "negative"]:
                    # 處理布林值或中文
                    if polarity in ["true", "正向", "積極"]:
                        polarity = "positive"
                    elif polarity in ["false", "負向", "消極"]:
                        polarity = "negative"
                    else:
                        # 根據情緒類別自動判斷極性
                        if emotion in ["amusement", "awe", "contentment", "excitement"]:
                            polarity = "positive"
                        else:
                            polarity = "negative"
                
                return {
                    "emotion": emotion,
                    "confidence": confidence,
                    "polarity": polarity
                }
            
            # 如果解析失敗，返回預設值
            logger.warning(f"無法解析情緒分析結果，使用預設值。原始回應: {reply}")
            return {
                "emotion": "contentment",
                "confidence": 0.5,
                "polarity": "positive"
            }
            
        except Exception as e:
            logger.error(f"情緒分析過程中發生錯誤: {str(e)}", exc_info=True)
            return {
                "emotion": "contentment",
                "confidence": 0.5,
                "polarity": "positive"
            }


# 建立全域實例（預設使用 qwen:7b 模型）
_detector_instance = None


def detect_emotion(text: str, model: str = "qwen:7b", temperature: float = 0.3) -> dict:
    """
    分析文字情緒（便捷函式）
    
    參數:
        text (str): 輸入的中文文字
        model (str, optional): Ollama 模型名稱，預設為 "qwen:7b"
        temperature (float, optional): 模型溫度參數，預設為 0.3
    
    返回:
        dict: 情緒分析結果，格式如下：
            {
                "emotion": str,      # 情緒類別
                "confidence": float, # 信心度（0.0-1.0）
                "polarity": str      # 情緒極性（"positive" 或 "negative"）
            }
    
    說明:
        這是模組級別的便捷函式，內部使用 EmotionDetector 類別
        首次呼叫時會建立 EmotionDetector 實例並快取
    """
    global _detector_instance
    
    # 如果實例不存在或模型參數變更，重新建立實例
    if _detector_instance is None or _detector_instance.model != model or _detector_instance.temperature != temperature:
        _detector_instance = EmotionDetector(model=model, temperature=temperature)
    
    return _detector_instance.detect_emotion(text)


# 測試範例
if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 測試案例
    test_cases = [
        "今天好開心喔！",
        "真的有點害怕明天的考試",
        "看到這片美景，我感到非常震撼",
        "這個味道讓我覺得很噁心",
        "終於完成了，心情真好",
        "我對這個結果感到非常失望和難過"
    ]
    
    print("=" * 60)
    print("情緒分析測試")
    print("=" * 60)
    
    for test_text in test_cases:
        result = detect_emotion(test_text)
        print(f"\n輸入: {test_text}")
        print(f"輸出: {result}")
        print(f"  情緒: {result['emotion']}")
        print(f"  信心度: {result['confidence']:.2f}")
        print(f"  極性: {result['polarity']}")

