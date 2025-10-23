#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強力模型預熱腳本
確保模型完全載入到記憶體中
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

def force_warmup():
    """強力預熱模型"""
    print("🔥 強力預熱 Ollama 模型...")
    
    try:
        import ollama
        from chatbot_ollama import chat_with_pet
        
        model_name = os.getenv('OLLAMA_MODEL', 'qwen:7b')
        print(f"📦 模型名稱: {model_name}")
        
        # 1. 確保模型存在
        print("🔍 檢查模型是否存在...")
        try:
            models = ollama.list()
            model_exists = False
            
            if isinstance(models, dict) and 'models' in models:
                model_list = models['models']
            elif isinstance(models, list):
                model_list = models
            else:
                model_list = []
            
            for model in model_list:
                if model.get('name') == model_name:
                    model_exists = True
                    break
            
            if not model_exists:
                print(f"📥 下載模型 {model_name}...")
                ollama.pull(model_name)
                print(f"✅ 模型下載完成")
            else:
                print(f"✅ 模型已存在")
                
        except Exception as e:
            print(f"⚠️ 無法檢查模型: {e}")
        
        # 2. 多次預熱，確保模型完全載入
        print("🚀 開始多次預熱...")
        
        warmup_times = []
        for i in range(3):
            print(f"📤 預熱測試 {i+1}/3...")
            start_time = time.time()
            
            try:
                response = chat_with_pet(
                    system_prompt="你是一隻可愛的狗狗，用簡單的話回覆。",
                    user_input=f"測試訊息 {i+1}",
                    model=model_name
                )
                
                end_time = time.time()
                warmup_time = end_time - start_time
                warmup_times.append(warmup_time)
                
                print(f"   ⏱️ 回應時間: {warmup_time:.2f} 秒")
                print(f"   🤖 回應: {response[:30]}...")
                
                # 等待一下再進行下一次
                if i < 2:
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ 預熱測試 {i+1} 失敗: {e}")
                return False
        
        # 3. 分析預熱結果
        print(f"\n📊 預熱結果分析:")
        avg_time = sum(warmup_times) / len(warmup_times)
        min_time = min(warmup_times)
        max_time = max(warmup_times)
        
        print(f"   平均回應時間: {avg_time:.2f} 秒")
        print(f"   最快回應時間: {min_time:.2f} 秒")
        print(f"   最慢回應時間: {max_time:.2f} 秒")
        
        if avg_time < 5:
            print("✅ 模型預熱成功，回應速度良好")
            return True
        elif avg_time < 10:
            print("⚠️ 模型預熱部分成功，回應速度一般")
            return True
        else:
            print("❌ 模型預熱失敗，回應速度太慢")
            return False
        
    except Exception as e:
        print(f"❌ 強力預熱失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ollama_process():
    """檢查 Ollama 進程"""
    print("\n🔍 檢查 Ollama 進程...")
    
    try:
        import subprocess
        
        # 檢查 Ollama 進程
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        ollama_processes = [line for line in result.stdout.split('\n') if 'ollama' in line.lower()]
        
        if ollama_processes:
            print(f"✅ 找到 {len(ollama_processes)} 個 Ollama 進程")
            for process in ollama_processes[:3]:  # 只顯示前3個
                print(f"   {process}")
        else:
            print("❌ 未找到 Ollama 進程")
            print("💡 請檢查 Ollama 服務: sudo systemctl status ollama")
            
    except Exception as e:
        print(f"⚠️ 無法檢查進程: {e}")

def main():
    """主函數"""
    print("🚀 開始強力模型預熱...")
    print("=" * 50)
    
    # 檢查 Ollama 進程
    check_ollama_process()
    
    # 強力預熱
    success = force_warmup()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 強力預熱完成！")
        print("💡 現在聊天時等待時間應該大幅減少")
        print("💡 如果還是慢，可能是系統資源不足")
    else:
        print("❌ 強力預熱失敗")
        print("💡 建議:")
        print("   1. 重啟 Ollama: sudo systemctl restart ollama")
        print("   2. 檢查系統資源: free -h, df -h")
        print("   3. 檢查 Ollama 日誌: sudo journalctl -u ollama")

if __name__ == "__main__":
    main()
