#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型預熱腳本
在部署時預先載入 AI 模型，減少聊天時的等待時間
"""

import os
import sys
import time
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加 mybot 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mybot'))

def warmup_ollama_model():
    """預熱 Ollama 模型"""
    print("🔥 預熱 Ollama 模型...")
    
    try:
        import ollama
        from mybot.chatbot_ollama import chat_with_pet, build_system_prompt
        
        model_name = os.getenv('OLLAMA_MODEL', 'qwen:7b')
        print(f"📦 模型名稱: {model_name}")
        
        # 檢查模型是否存在
        try:
            models = ollama.list()
            model_exists = any(model['name'] == model_name for model in models['models'])
            
            if not model_exists:
                print(f"❌ 模型 {model_name} 不存在，嘗試下載...")
                ollama.pull(model_name)
                print(f"✅ 模型 {model_name} 下載完成")
            else:
                print(f"✅ 模型 {model_name} 已存在")
                
        except Exception as e:
            print(f"⚠️ 無法檢查模型列表: {e}")
        
        # 預熱模型 - 發送一個簡單的請求
        print("🚀 開始預熱模型...")
        start_time = time.time()
        
        system_prompt = "你是一隻可愛的狗狗，用簡單的話回覆。"
        test_input = "你好"
        
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
        return False

def warmup_api_model():
    """預熱 API 模型"""
    print("🔥 預熱 API 模型...")
    
    try:
        from mybot.chatbot_api import chat_with_pet_api
        
        model_name = os.getenv('QWEN_MODEL', 'qwen-flash')
        api_key = os.getenv('QWEN_API_KEY')
        api_url = os.getenv('QWEN_API_URL', 'https://api.qwen.com/v1/chat/completions')
        
        print(f"📦 模型名稱: {model_name}")
        print(f"🌐 API URL: {api_url}")
        print(f"🔑 API Key: {'已設定' if api_key else '❌ 未設定'}")
        
        if not api_key:
            print("❌ API Key 未設定，無法預熱 API 模型")
            return False
        
        # 預熱 API - 發送一個簡單的請求
        print("🚀 開始預熱 API 模型...")
        start_time = time.time()
        
        system_prompt = "你是一隻可愛的狗狗，用簡單的話回覆。"
        test_input = "你好"
        
        response = chat_with_pet_api(
            system_prompt=system_prompt,
            user_input=test_input,
            model=model_name
        )
        
        end_time = time.time()
        warmup_time = end_time - start_time
        
        print(f"✅ API 模型預熱完成")
        print(f"⏱️ 預熱時間: {warmup_time:.2f} 秒")
        print(f"🤖 測試回覆: {response[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API 模型預熱失敗: {e}")
        return False

def check_ollama_service():
    """檢查 Ollama 服務狀態"""
    print("🔍 檢查 Ollama 服務...")
    
    try:
        import ollama
        
        # 嘗試列出模型
        models = ollama.list()
        print(f"✅ Ollama 服務正常，已載入 {len(models['models'])} 個模型")
        
        for model in models['models']:
            print(f"   - {model['name']} ({model['size']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama 服務異常: {e}")
        return False

def check_api_connection():
    """檢查 API 連接"""
    print("🔍 檢查 API 連接...")
    
    try:
        import httpx
        
        api_url = os.getenv('QWEN_API_URL', 'https://api.qwen.com/v1/chat/completions')
        
        with httpx.Client(timeout=10) as client:
            response = client.get(api_url)
            print(f"✅ API 連接正常，狀態碼: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"❌ API 連接異常: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始模型預熱...")
    print("=" * 50)
    
    ai_mode = os.getenv('AI_MODE', 'ollama')
    print(f"🤖 AI 模式: {ai_mode}")
    
    success = False
    
    if ai_mode == 'api':
        print("\n🌐 使用 API 模式")
        
        # 檢查 API 連接
        if check_api_connection():
            # 預熱 API 模型
            success = warmup_api_model()
        else:
            print("❌ API 連接失敗，無法預熱")
            
    else:
        print("\n🏠 使用 Ollama 模式")
        
        # 檢查 Ollama 服務
        if check_ollama_service():
            # 預熱 Ollama 模型
            success = warmup_ollama_model()
        else:
            print("❌ Ollama 服務異常，無法預熱")
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 模型預熱完成！")
        print("💡 現在聊天時等待時間會大幅減少")
    else:
        print("❌ 模型預熱失敗")
        print("💡 請檢查 AI 模式設定和相關服務")
    
    return success

if __name__ == "__main__":
    main()
