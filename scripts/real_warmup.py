#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真實場景模型預熱腳本
模擬實際的對話場景進行預熱
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

def real_scenario_warmup():
    """真實場景預熱"""
    print("🔥 真實場景模型預熱...")
    
    try:
        from db_utils import get_pet_profile, get_pet_id_by_line_user
        from chatbot_ollama import chat_with_pet, build_system_prompt
        from personalities import pet_personality_templates
        
        # 使用真實的 LINE 使用者 ID 進行測試
        test_line_user_id = "U6f37e67d13133e38eebed16a2974e60a"
        model_name = os.getenv('OLLAMA_MODEL', 'qwen:7b')
        
        print(f"📦 模型名稱: {model_name}")
        print(f"👤 測試使用者: {test_line_user_id}")
        
        # 1. 模擬獲取寵物 ID
        print("🔍 模擬獲取寵物 ID...")
        start_time = time.time()
        pet_id = get_pet_id_by_line_user(test_line_user_id)
        api_time = time.time() - start_time
        print(f"⏱️ API 調用時間: {api_time:.2f} 秒")
        
        if not pet_id:
            print("❌ 無法獲取寵物 ID，使用預設值")
            pet_id = 1
        
        # 2. 模擬獲取寵物資料
        print("🔍 模擬獲取寵物資料...")
        start_time = time.time()
        pet_profile = get_pet_profile(pet_id)
        profile_time = time.time() - start_time
        print(f"⏱️ 寵物資料獲取時間: {profile_time:.2f} 秒")
        
        if not pet_profile:
            print("❌ 無法獲取寵物資料")
            return False
        
        print(f"🐾 寵物名稱: {pet_profile['name']}")
        print(f"🐕 寵物品種: {pet_profile['breed']}")
        print(f"🎭 性格類型: {pet_profile['persona_key']}")
        
        # 3. 模擬建立系統提示詞
        print("🔍 模擬建立系統提示詞...")
        start_time = time.time()
        
        system_prompt = build_system_prompt(
            pet_name=pet_profile["name"],
            breed=pet_profile["breed"],
            persona=pet_personality_templates[pet_profile["persona_key"]],
            life_data=pet_profile["lifeData"],
            cover_slogan=pet_profile["cover_slogan"],
            letter=pet_profile["letter"]
        )
        
        prompt_time = time.time() - start_time
        print(f"⏱️ 系統提示詞建立時間: {prompt_time:.2f} 秒")
        print(f"📝 提示詞長度: {len(system_prompt)} 字元")
        
        # 4. 模擬真實對話場景
        print("🚀 開始真實場景預熱...")
        
        test_messages = [
            "你好",
            "你今天過得怎麼樣？",
            "我想你了",
            "我們一起玩吧"
        ]
        
        total_times = []
        
        for i, message in enumerate(test_messages):
            print(f"📤 測試訊息 {i+1}/4: {message}")
            start_time = time.time()
            
            try:
                response = chat_with_pet(
                    system_prompt=system_prompt,
                    user_input=message,
                    model=model_name
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                total_times.append(response_time)
                
                print(f"   ⏱️ 回應時間: {response_time:.2f} 秒")
                print(f"   🤖 回應: {response[:50]}...")
                
                # 等待一下再進行下一次
                if i < len(test_messages) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"   ❌ 測試失敗: {e}")
                return False
        
        # 5. 分析結果
        print(f"\n📊 真實場景預熱結果:")
        avg_time = sum(total_times) / len(total_times)
        min_time = min(total_times)
        max_time = max(total_times)
        
        print(f"   API 調用時間: {api_time:.2f} 秒")
        print(f"   寵物資料獲取: {profile_time:.2f} 秒")
        print(f"   系統提示詞建立: {prompt_time:.2f} 秒")
        print(f"   平均回應時間: {avg_time:.2f} 秒")
        print(f"   最快回應時間: {min_time:.2f} 秒")
        print(f"   最慢回應時間: {max_time:.2f} 秒")
        
        # 判斷是否成功
        if avg_time < 10:
            print("✅ 真實場景預熱成功！")
            return True
        elif avg_time < 20:
            print("⚠️ 真實場景預熱部分成功")
            return True
        else:
            print("❌ 真實場景預熱失敗，回應太慢")
            return False
        
    except Exception as e:
        print(f"❌ 真實場景預熱失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始真實場景模型預熱...")
    print("=" * 60)
    print("💡 這個腳本會模擬真實的對話場景進行預熱")
    print("💡 包括 API 調用、寵物資料獲取、系統提示詞建立等")
    print("=" * 60)
    
    success = real_scenario_warmup()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 真實場景預熱完成！")
        print("💡 現在第一次對話應該會快很多")
        print("💡 如果還是慢，可能是系統資源不足")
    else:
        print("❌ 真實場景預熱失敗")
        print("💡 建議:")
        print("   1. 檢查 API 連接速度")
        print("   2. 檢查系統資源")
        print("   3. 重啟 Ollama 服務")

if __name__ == "__main__":
    main()
