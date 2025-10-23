#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查模型預熱狀態
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

def check_ollama_status():
    """檢查 Ollama 服務狀態"""
    print("🔍 檢查 Ollama 服務狀態...")
    
    try:
        import ollama
        
        # 檢查服務是否運行
        models = ollama.list()
        print(f"✅ Ollama 服務正常")
        
        # 檢查模型
        model_name = os.getenv('OLLAMA_MODEL', 'qwen:7b')
        print(f"📦 目標模型: {model_name}")
        
        if isinstance(models, dict) and 'models' in models:
            model_list = models['models']
        elif isinstance(models, list):
            model_list = models
        else:
            model_list = []
        
        model_found = False
        for model in model_list:
            if model.get('name') == model_name:
                model_found = True
                print(f"✅ 模型 {model_name} 已載入")
                print(f"   大小: {model.get('size', 'Unknown')}")
                break
        
        if not model_found:
            print(f"❌ 模型 {model_name} 未找到")
            print("💡 嘗試下載模型...")
            try:
                ollama.pull(model_name)
                print(f"✅ 模型 {model_name} 下載完成")
            except Exception as e:
                print(f"❌ 下載失敗: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama 服務異常: {e}")
        return False

def test_model_response():
    """測試模型回應速度"""
    print("\n🧪 測試模型回應速度...")
    
    try:
        from chatbot_ollama import chat_with_pet
        
        model_name = os.getenv('OLLAMA_MODEL', 'qwen:7b')
        
        # 第一次測試
        print("📤 第一次測試...")
        start_time = time.time()
        
        response1 = chat_with_pet(
            system_prompt="你是一隻可愛的狗狗，用簡單的話回覆。",
            user_input="你好",
            model=model_name
        )
        
        first_time = time.time() - start_time
        print(f"⏱️ 第一次回應時間: {first_time:.2f} 秒")
        print(f"🤖 回應: {response1[:50]}...")
        
        # 第二次測試
        print("\n📤 第二次測試...")
        start_time = time.time()
        
        response2 = chat_with_pet(
            system_prompt="你是一隻可愛的狗狗，用簡單的話回覆。",
            user_input="再見",
            model=model_name
        )
        
        second_time = time.time() - start_time
        print(f"⏱️ 第二次回應時間: {second_time:.2f} 秒")
        print(f"🤖 回應: {response2[:50]}...")
        
        # 分析結果
        print(f"\n📊 分析結果:")
        if first_time > 10:
            print(f"❌ 第一次回應太慢 ({first_time:.2f}s)，模型可能未預熱")
        else:
            print(f"✅ 第一次回應正常 ({first_time:.2f}s)")
            
        if second_time > 5:
            print(f"❌ 第二次回應太慢 ({second_time:.2f}s)，可能有問題")
        else:
            print(f"✅ 第二次回應正常 ({second_time:.2f}s)")
        
        return first_time < 10 and second_time < 5
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_system_resources():
    """檢查系統資源"""
    print("\n💻 檢查系統資源...")
    
    try:
        import psutil
        
        # 檢查記憶體使用
        memory = psutil.virtual_memory()
        print(f"🧠 記憶體使用: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        
        # 檢查 CPU 使用
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"⚡ CPU 使用: {cpu_percent}%")
        
        # 檢查磁碟空間
        disk = psutil.disk_usage('/')
        print(f"💾 磁碟使用: {disk.percent}% ({disk.free / 1024**3:.1f}GB 可用)")
        
        if memory.percent > 90:
            print("⚠️ 記憶體使用率過高，可能影響模型性能")
        if cpu_percent > 90:
            print("⚠️ CPU 使用率過高，可能影響模型性能")
        if disk.percent > 90:
            print("⚠️ 磁碟空間不足，可能影響模型性能")
            
    except ImportError:
        print("⚠️ 無法檢查系統資源 (psutil 未安裝)")
    except Exception as e:
        print(f"⚠️ 檢查系統資源失敗: {e}")

def main():
    """主函數"""
    print("🔍 開始檢查模型預熱狀態...")
    print("=" * 50)
    
    # 檢查 Ollama 狀態
    ollama_ok = check_ollama_status()
    if not ollama_ok:
        print("\n❌ Ollama 服務有問題，請檢查:")
        print("   sudo systemctl status ollama")
        print("   sudo systemctl restart ollama")
        return
    
    # 檢查系統資源
    check_system_resources()
    
    # 測試模型回應
    test_ok = test_model_response()
    
    print("\n" + "=" * 50)
    if test_ok:
        print("✅ 模型預熱正常，回應速度良好")
        print("💡 如果 LINE Bot 仍然慢，可能是其他問題")
    else:
        print("❌ 模型預熱有問題")
        print("💡 建議:")
        print("   1. 重啟 Ollama: sudo systemctl restart ollama")
        print("   2. 重新預熱: python3 scripts/simple_warmup.py")
        print("   3. 檢查系統資源是否充足")

if __name__ == "__main__":
    main()
