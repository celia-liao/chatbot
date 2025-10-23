#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試完整的訊息流程和資料庫寫入
"""

import sys
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加 mybot 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'mybot'))

def test_database_connection():
    """測試資料庫連接"""
    print("🔍 測試資料庫連接...")
    
    try:
        from mybot.db_utils import get_connection
        from mybot.config import DB_CONFIG
        
        print(f"📊 資料庫配置: {DB_CONFIG}")
        
        connection = get_connection()
        print("✅ 資料庫連接成功！")
        
        with connection.cursor() as cursor:
            # 檢查當前資料庫
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            print(f"🗄️ 當前資料庫: {current_db['DATABASE()']}")
            
            # 檢查 chat_history 表
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ chat_history 表存在")
                
                # 檢查記錄數量
                cursor.execute("SELECT COUNT(*) as count FROM chat_history")
                count_result = cursor.fetchone()
                print(f"📊 現有記錄數量: {count_result['count']}")
                
            else:
                print("❌ chat_history 表不存在")
                return False
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        return False

def test_pet_id_lookup():
    """測試寵物 ID 查詢"""
    print("\n🔍 測試寵物 ID 查詢...")
    
    try:
        from mybot.db_utils import get_pet_id_by_line_user
        
        # 使用您提供的測試 LINE 使用者 ID
        test_line_user_id = "U6f37e67d13133e38eebed16a2974e60a"
        
        print(f"📝 查詢 LINE 使用者: {test_line_user_id}")
        pet_id = get_pet_id_by_line_user(test_line_user_id)
        
        if pet_id:
            print(f"✅ 找到寵物 ID: {pet_id}")
            return pet_id
        else:
            print("❌ 找不到寵物 ID，使用預設值 1")
            return 1
            
    except Exception as e:
        print(f"❌ 寵物 ID 查詢失敗: {e}")
        return 1

def test_save_user_message():
    """測試儲存使用者訊息"""
    print("\n📝 測試儲存使用者訊息...")
    
    try:
        from mybot.db_utils import save_chat_message
        
        test_line_user_id = "U6f37e67d13133e38eebed16a2974e60a"
        test_pet_id = 1
        test_message = "這是一則測試使用者訊息"
        
        print(f"📤 儲存使用者訊息: {test_message}")
        result = save_chat_message(test_line_user_id, test_pet_id, 'user', test_message)
        
        if result:
            print("✅ 使用者訊息儲存成功")
            return True
        else:
            print("❌ 使用者訊息儲存失敗")
            return False
            
    except Exception as e:
        print(f"❌ 儲存使用者訊息失敗: {e}")
        return False

def test_save_assistant_message():
    """測試儲存助手訊息"""
    print("\n🤖 測試儲存助手訊息...")
    
    try:
        from mybot.db_utils import save_chat_message
        
        test_line_user_id = "U6f37e67d13133e38eebed16a2974e60a"
        test_pet_id = 1
        test_message = "這是一則測試助手回覆"
        
        print(f"📤 儲存助手訊息: {test_message}")
        result = save_chat_message(test_line_user_id, test_pet_id, 'assistant', test_message)
        
        if result:
            print("✅ 助手訊息儲存成功")
            return True
        else:
            print("❌ 助手訊息儲存失敗")
            return False
            
    except Exception as e:
        print(f"❌ 儲存助手訊息失敗: {e}")
        return False

def test_read_chat_history():
    """測試讀取對話歷史"""
    print("\n📚 測試讀取對話歷史...")
    
    try:
        from mybot.db_utils import get_chat_history
        
        test_line_user_id = "U6f37e67d13133e38eebed16a2974e60a"
        test_pet_id = 1
        
        print(f"📖 讀取對話歷史: {test_line_user_id}")
        history = get_chat_history(test_line_user_id, test_pet_id, limit=5)
        
        print(f"📊 讀取到 {len(history)} 條對話記錄")
        
        if history:
            print("📋 對話記錄內容:")
            for i, record in enumerate(history):
                print(f"   {i+1}. 使用者: {record['user']}")
                print(f"      助手: {record['bot']}")
            return True
        else:
            print("❌ 沒有讀取到對話記錄")
            return False
            
    except Exception as e:
        print(f"❌ 讀取對話歷史失敗: {e}")
        return False

def test_database_records():
    """檢查資料庫中的實際記錄"""
    print("\n🔍 檢查資料庫中的實際記錄...")
    
    try:
        from mybot.db_utils import get_connection
        
        connection = get_connection()
        
        with connection.cursor() as cursor:
            # 查詢最近的記錄
            cursor.execute("""
                SELECT line_user_id, pet_id, role, message, created_at 
                FROM chat_history 
                WHERE line_user_id = 'U6f37e67d13133e38eebed16a2974e60a'
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            records = cursor.fetchall()
            
            if records:
                print(f"📊 找到 {len(records)} 條記錄:")
                for i, record in enumerate(records, 1):
                    print(f"   {i}. {record['created_at']} - {record['role']}: {record['message'][:50]}...")
                return True
            else:
                print("❌ 沒有找到記錄")
                return False
        
        connection.close()
        
    except Exception as e:
        print(f"❌ 檢查資料庫記錄失敗: {e}")
        return False

def test_linebot_simulation():
    """模擬 LINE Bot 的完整訊息處理流程"""
    print("\n🤖 模擬 LINE Bot 訊息處理流程...")
    
    try:
        from mybot.db_utils import get_pet_id_by_line_user, save_chat_message, get_chat_history
        
        # 模擬 LINE Bot 接收訊息
        line_user_id = "U6f37e67d13133e38eebed16a2974e60a"
        user_message = "你好，我是測試訊息"
        
        print(f"📱 模擬接收訊息: {user_message}")
        
        # 1. 查詢寵物 ID
        pet_id = get_pet_id_by_line_user(line_user_id)
        if not pet_id:
            pet_id = 1  # 使用預設值
        print(f"🐾 寵物 ID: {pet_id}")
        
        # 2. 讀取對話歷史
        history = get_chat_history(line_user_id, pet_id, limit=5)
        print(f"📚 對話歷史: {len(history)} 條記錄")
        
        # 3. 儲存使用者訊息
        print("💾 儲存使用者訊息...")
        save_user_result = save_chat_message(line_user_id, pet_id, 'user', user_message)
        print(f"結果: {'✅ 成功' if save_user_result else '❌ 失敗'}")
        
        # 4. 模擬 AI 回覆
        assistant_reply = "你好！我是嚕比，很高興見到你！"
        print(f"🤖 AI 回覆: {assistant_reply}")
        
        # 5. 儲存助手訊息
        print("💾 儲存助手訊息...")
        save_assistant_result = save_chat_message(line_user_id, pet_id, 'assistant', assistant_reply)
        print(f"結果: {'✅ 成功' if save_assistant_result else '❌ 失敗'}")
        
        # 6. 驗證儲存結果
        print("🔍 驗證儲存結果...")
        final_history = get_chat_history(line_user_id, pet_id, limit=5)
        print(f"📊 最終對話記錄: {len(final_history)} 條")
        
        return save_user_result and save_assistant_result
        
    except Exception as e:
        print(f"❌ LINE Bot 模擬失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始完整的訊息流程測試...")
    print("=" * 60)
    
    # 1. 測試資料庫連接
    if not test_database_connection():
        print("\n❌ 資料庫連接失敗，無法繼續測試")
        return
    
    # 2. 測試寵物 ID 查詢
    pet_id = test_pet_id_lookup()
    
    # 3. 測試儲存使用者訊息
    if not test_save_user_message():
        print("\n❌ 儲存使用者訊息失敗")
        return
    
    # 4. 測試儲存助手訊息
    if not test_save_assistant_message():
        print("\n❌ 儲存助手訊息失敗")
        return
    
    # 5. 測試讀取對話歷史
    if not test_read_chat_history():
        print("\n❌ 讀取對話歷史失敗")
        return
    
    # 6. 檢查資料庫中的實際記錄
    if not test_database_records():
        print("\n❌ 資料庫記錄檢查失敗")
        return
    
    # 7. 模擬完整的 LINE Bot 流程
    if not test_linebot_simulation():
        print("\n❌ LINE Bot 模擬失敗")
        return
    
    print("\n" + "=" * 60)
    print("✅ 所有測試通過！訊息流程正常")
    print("💡 如果 LINE Bot 仍然無法儲存對話記錄，可能的原因:")
    print("   1. LINE Bot 沒有正確處理訊息事件")
    print("   2. 應用程式沒有正確調用 save_chat_message")
    print("   3. 訊息處理過程中有異常被忽略")
    print("   4. 檢查 logs/app.log 檔案中的錯誤訊息")

if __name__ == "__main__":
    main()
