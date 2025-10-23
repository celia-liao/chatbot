#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超簡化版模型預熱腳本
直接使用相對路徑導入
"""

import os
import sys
import time
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 切換到專案根目錄
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)

# 添加 mybot 到 Python 路徑
sys.path.insert(0, 'mybot')

print(f"🔍 工作目錄: {os.getcwd()}")
print(f"🐍 Python 路徑: {sys.path[:3]}")

def simple_ollama_warmup():
    """簡化版 Ollama 預熱"""
    print("🔥 簡化版 Ollama 模型預熱...")
    
    try:
        import ollama
        from chatbot_ollama import chat_with_pet
        
        model_name = os.getenv('OLLAMA_MODEL', 'qwen:7b')
        print(f"📦 模型名稱: {model_name}")
        
        # 直接嘗試預熱，不檢查模型列表
        print("🚀 開始預熱模型...")
        start_time = time.time()
        
        system_prompt = "你是一隻可愛的狗狗，用簡單的話回覆。"
        test_input = "你好"
        
        print("📤 發送測試請求...")
        response = chat_with_pet(
            system_prompt=system_prompt,
            user_input=test_input,
            model=model_name
        )
        
        end_time = time.time()
        warmup_time = end_time - start_time
        
        print(f"✅ Ollama 模型預熱完成")
        print(f"⏱️ 預熱時間: {warmup_time:.2f} 秒")
        print(f"🤖 測試回覆: {response[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama 模型預熱失敗: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始超簡化版模型預熱...")
    print("=" * 50)
    
    ai_mode = os.getenv('AI_MODE', 'ollama')
    print(f"🤖 AI 模式: {ai_mode}")
    
    if ai_mode == 'ollama':
        success = simple_ollama_warmup()
    else:
        print("⚠️ 此腳本僅支援 Ollama 模式")
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 模型預熱完成！")
        print("💡 現在聊天時等待時間會大幅減少")
    else:
        print("❌ 模型預熱失敗")
        print("💡 請檢查 Ollama 服務是否正常運行")
        print("   檢查指令: ollama list")
        print("   重啟服務: sudo systemctl restart ollama")

if __name__ == "__main__":
    main()
