# emotion_detector_light.py
# ============================================
# 輕量版情緒辨識模組（適合實際系統應用）
# ============================================
# 功能：先用關鍵詞判斷 → 若無命中再用 LLM → 回傳對應情緒
# 依賴：ollama, opencc-python-reimplemented
# ============================================

import json
import logging
import re
import ollama
from opencc import OpenCC

logger = logging.getLogger('pet_chatbot')
cc_t2s = OpenCC('t2s')  # 繁體轉簡體


class EmotionDetector:
    """
    中文情緒辨識器
    支援 8 類情緒：
        正向：amusement, awe, contentment, excitement
        負向：anger, disgust, fear, sad
    """

    EMOTION_KEYWORDS = {
        "amusement": ["好笑", "開心", "可愛", "好玩", "幽默", "笑死", "爆笑", "搞笑", "快樂", "樂", "喜"],
        "awe": ["驚訝", "震撼", "厲害", "佩服", "太棒了", "讚嘆", "不可思議", "驚艷", "震驚"],
        "contentment": ["放鬆", "舒服", "平靜", "滿足", "愜意", "安心", "悠閒", "自在", "安穩"],
        "excitement": ["超開心", "超快樂", "興奮", "激動", "期待", "迫不及待", "熱血", "嗨爆", "爽爆", "high"],
        "anger": ["生氣", "氣死", "煩", "怒", "不爽", "靠北", "火大", "氣炸"],
        "disgust": ["噁心", "討厭", "厭惡", "反感", "噁爛"],
        "fear": ["害怕", "恐懼", "擔心", "緊張", "不安", "焦慮", "慌張"],
        "sad": ["難過", "悲傷", "傷心", "失落", "孤單", "寂寞", "低落", "沮喪", "心痛", "心碎"]
    }

    EMOTION_IMAGE_MAP = {
        "amusement": "https://chatbot.crittersmem.com/images/amusement.webp",
        "awe": "https://chatbot.crittersmem.com/images/awe.webp",
        "contentment": "https://chatbot.crittersmem.com/images/contentment.webp",
        "excitement": "https://chatbot.crittersmem.com/images/excitement.webp",
        "anger": "https://chatbot.crittersmem.com/images/anger.webp",
        "disgust": "https://chatbot.crittersmem.com/images/disgust.webp",
        "fear": "https://chatbot.crittersmem.com/images/fear.webp",
        "sad": "https://chatbot.crittersmem.com/images/sad.webp"
    }

    def __init__(self, model: str = "qwen:7b", use_llm: bool = True):
        self.model = model
        self.use_llm = use_llm
        self.system_prompt = (
            "你是一個中文情緒分析助手，只能從下列八種情緒中選出一種："
            "amusement, awe, contentment, excitement, anger, disgust, fear, sad。\n"
            "請以 JSON 格式輸出，例如：{\"emotion\": \"excitement\"}"
        )

    # -----------------------
    # 1️⃣ 關鍵詞快速判斷
    # -----------------------
    def _detect_by_keywords(self, text: str) -> str:
        text_s = cc_t2s.convert(text)
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for k in keywords:
                keyword_s = cc_t2s.convert(k)
                if k in text_s or keyword_s in text_s:
                    logger.info(f"[Keyword Match] {k} → {emotion}")
                    return emotion
        return None

    # -----------------------
    # 2️⃣ LLM 判斷（可選）
    # -----------------------
    def _detect_by_llm(self, text: str) -> str:
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"句子：{cc_t2s.convert(text)}"}
            ]
            res = ollama.chat(model=self.model, messages=messages)
            reply = res["message"]["content"].strip()
            match = re.search(r'"emotion"\s*:\s*"(\w+)"', reply)
            if match:
                emotion = match.group(1)
                if emotion in self.EMOTION_KEYWORDS.keys():
                    logger.info(f"[LLM] {text} → {emotion}")
                    return emotion
        except Exception as e:
            logger.warning(f"LLM 判斷失敗: {e}")
        return None

    # -----------------------
    # 3️⃣ 主函式：綜合判斷
    # -----------------------
    def detect_emotion(self, text: str) -> dict:
        if not text or not text.strip():
            return {"emotion": "contentment", "image": self.EMOTION_IMAGE_MAP["contentment"]}

        # Step 1: 詞典比對
        emotion = self._detect_by_keywords(text)
        # Step 2: 若無結果且允許 LLM
        if not emotion and self.use_llm:
            emotion = self._detect_by_llm(text)
        # Step 3: 都沒結果
        if not emotion:
            emotion = "contentment"

        return {
            "emotion": emotion,
            "image": self.EMOTION_IMAGE_MAP.get(emotion, ""),
        }


# -----------------------
# 全域便捷呼叫函式
# -----------------------
_detector_instance = None


def detect_emotion(text: str, model: str = "qwen:7b", use_llm: bool = True):
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = EmotionDetector(model=model, use_llm=use_llm)
    return _detector_instance.detect_emotion(text)
