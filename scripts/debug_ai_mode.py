#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 模式診斷腳本
用於檢查目前使用的 AI 模式和可能的問題
"""

import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def check_environment():
    """檢查環境變數設定"""
    print("🔍 檢查環境變數...")
    
    ai_mode = os.getenv('AI_MODE', 'ollama')
    print(f"AI_MODE: {ai_mode}")
    
    if ai_mode == 'api':
        api_key = os.getenv('QWEN_API_KEY')
        api_url = os.getenv('QWEN_API_URL', 'https://api.qwen.com/v1/chat/completions')
        model = os.getenv('QWEN_MODEL', 'qwen-flash')
        
        print(f"QWEN_API_KEY: {'已設定' if api_key else '❌ 未設定'}")
        print(f"QWEN_API_URL: {api_url}")
        print(f"QWEN_MODEL: {model}")
        
        if not api_key:
            print("❌ 錯誤：API 模式下需要設定 QWEN_API_KEY")
            return False
    else:
        ollama_model = os.getenv('OLLAMA_MODEL', 'qwen:7b')
        print(f"OLLAMA_MODEL: {ollama_model}")
    
    return True

def test_imports():
    """測試模組匯入"""
    print("\n🔍 檢查模組匯入...")
    
    try:
        # 測試 Ollama 模組
        import ollama
        print("✅ Ollama 模組匯入成功")
    except ImportError as e:
        print(f"❌ Ollama 模組匯入失敗: {e}")
    
    try:
        # 測試 API 模組
        import httpx
        print("✅ httpx 模組匯入成功")
    except ImportError as e:
        print(f"❌ httpx 模組匯入失敗: {e}")
    
    try:
        # 測試 OpenCC 模組
        from opencc import OpenCC
        print("✅ OpenCC 模組匯入成功")
    except ImportError as e:
        print(f"❌ OpenCC 模組匯入失敗: {e}")

def test_ai_functions():
    """測試 AI 功能"""
    print("\n🔍 測試 AI 功能...")
    
    ai_mode = os.getenv('AI_MODE', 'ollama')
    
    try:
        if ai_mode == 'api':
            from mybot.chatbot_api import chat_with_pet_api, build_system_prompt
            print("✅ API 模組匯入成功")
            
            # 測試簡單對話
            system_prompt = "你是一隻可愛的狗狗，用簡單的話回覆。"
            test_input = "你好"
            
            print("🧪 測試 API 對話...")
            result = chat_with_pet_api(
                system_prompt=system_prompt,
                user_input=test_input,
                model=os.getenv('QWEN_MODEL', 'qwen-flash')
            )
            print(f"✅ API 對話測試成功: {result[:50]}...")
            
        else:
            from mybot.chatbot_ollama import chat_with_pet, build_system_prompt
            print("✅ Ollama 模組匯入成功")
            
            # 測試簡單對話
            system_prompt = "你是一隻可愛的狗狗，用簡單的話回覆。"
            test_input = "你好"
            
            print("🧪 測試 Ollama 對話...")
            result = chat_with_pet(
                system_prompt=system_prompt,
                user_input=test_input,
                model=os.getenv('OLLAMA_MODEL', 'qwen:7b')
            )
            print(f"✅ Ollama 對話測試成功: {result[:50]}...")
            
    except Exception as e:
        print(f"❌ AI 功能測試失敗: {e}")
        import traceback
        traceback.print_exc()

def check_service_logs():
    """檢查服務日誌"""
    print("\n🔍 檢查服務日誌...")
    
    try:
        import subprocess
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', 'line-bot.service', '--since', '10 minutes ago', '-n', '20'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logs = result.stdout
            print("📋 最近的服務日誌:")
            print(logs)
            
            # 檢查錯誤訊息
            if "ERROR" in logs or "Exception" in logs:
                print("❌ 發現錯誤訊息")
            else:
                print("✅ 未發現明顯錯誤")
        else:
            print("❌ 無法讀取服務日誌")
            
    except Exception as e:
        print(f"❌ 檢查日誌失敗: {e}")

def main():
    """主診斷函數"""
    print("=" * 60)
    print("🤖 AI 模式診斷工具")
    print("=" * 60)
    
    # 檢查環境變數
    env_ok = check_environment()
    
    # 檢查模組匯入
    test_imports()
    
    # 檢查 AI 功能
    if env_ok:
        test_ai_functions()
    
    # 檢查服務日誌
    check_service_logs()
    
    print("\n" + "=" * 60)
    print("📋 診斷完成")
    print("=" * 60)
    
    print("\n💡 建議檢查項目:")
    print("1. 確認 .env 檔案中的 AI_MODE 設定")
    print("2. 如果使用 API 模式，確認 QWEN_API_KEY 已設定")
    print("3. 如果使用 Ollama 模式，確認 Ollama 服務正在運行")
    print("4. 檢查服務日誌: sudo journalctl -u line-bot.service -f")
    print("5. 重啟服務: sudo systemctl restart line-bot.service")

if __name__ == "__main__":
    main()
