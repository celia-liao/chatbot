#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫連接測試腳本
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
        
        print(f"📊 資料庫配置:")
        print(f"   Host: {DB_CONFIG.get('host', 'N/A')}")
        print(f"   User: {DB_CONFIG.get('user', 'N/A')}")
        print(f"   Database: {DB_CONFIG.get('database', 'N/A')}")
        print(f"   Password: {'已設定' if DB_CONFIG.get('password') else '❌ 未設定'}")
        
        # 嘗試連接資料庫
        print("\n🔌 嘗試連接資料庫...")
        connection = get_connection()
        print("✅ 資料庫連接成功！")
        
        # 測試基本查詢
        with connection.cursor() as cursor:
            # 檢查資料庫版本
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"📋 資料庫版本: {version['VERSION()']}")
            
            # 檢查當前資料庫
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            print(f"🗄️ 當前資料庫: {current_db['DATABASE()']}")
            
            # 檢查表是否存在
            cursor.execute("SHOW TABLES LIKE 'chat_history'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ chat_history 表存在")
                
                # 檢查表結構
                cursor.execute("DESCRIBE chat_history")
                columns = cursor.fetchall()
                print("📋 表結構:")
                for col in columns:
                    print(f"   - {col['Field']}: {col['Type']}")
                
                # 檢查記錄數量
                cursor.execute("SELECT COUNT(*) as count FROM chat_history")
                count_result = cursor.fetchone()
                print(f"📊 現有記錄數量: {count_result['count']}")
                
                # 顯示最近的記錄
                cursor.execute("""
                    SELECT line_user_id, pet_id, role, message, created_at 
                    FROM chat_history 
                    ORDER BY created_at DESC 
                    LIMIT 3
                """)
                recent_records = cursor.fetchall()
                
                if recent_records:
                    print("📝 最近的記錄:")
                    for i, record in enumerate(recent_records, 1):
                        print(f"   {i}. {record['line_user_id']} ({record['role']}): {record['message'][:30]}...")
                else:
                    print("📝 沒有記錄")
                
            else:
                print("❌ chat_history 表不存在")
                print("💡 需要創建表，請執行以下 SQL:")
                print("""
CREATE TABLE IF NOT EXISTS `chat_history` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `line_user_id` varchar(100) NOT NULL,
    `pet_id` int(11) NOT NULL,
    `role` enum('user', 'assistant') NOT NULL,
    `message` text NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_line_user_pet` (`line_user_id`, `pet_id`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
        
        connection.close()
        print("✅ 資料庫連接測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        
        # 提供診斷建議
        if "Access denied" in str(e):
            print("💡 建議: 檢查資料庫使用者名稱和密碼")
        elif "Can't connect" in str(e):
            print("💡 建議: 檢查資料庫主機位址和端口")
        elif "Unknown database" in str(e):
            print("💡 建議: 檢查資料庫名稱是否正確")
        elif "ModuleNotFoundError" in str(e):
            print("💡 建議: 安裝缺少的 Python 模組")
            print("   執行: pip install pymysql python-dotenv")
        
        return False

def test_save_function():
    """測試儲存功能"""
    print("\n🧪 測試儲存功能...")
    
    try:
        from mybot.db_utils import save_chat_message
        
        # 測試儲存
        test_user_id = "test_connection_123"
        test_pet_id = 1
        test_message = "這是一則連接測試訊息"
        
        print(f"📝 測試儲存訊息...")
        result = save_chat_message(test_user_id, test_pet_id, 'user', test_message)
        
        if result:
            print("✅ 儲存功能測試成功")
            return True
        else:
            print("❌ 儲存功能測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 儲存功能測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始資料庫連接測試...")
    print("=" * 50)
    
    # 測試資料庫連接
    connection_ok = test_database_connection()
    
    if connection_ok:
        # 測試儲存功能
        save_ok = test_save_function()
        
        if save_ok:
            print("\n" + "=" * 50)
            print("✅ 所有測試通過！資料庫連接正常")
            print("💡 如果 LINE Bot 仍然無法儲存對話記錄，請檢查:")
            print("   1. 應用程式日誌檔案 (logs/app.log)")
            print("   2. 確認 save_chat_message 函數被正確調用")
            print("   3. 檢查 LINE Bot 的訊息處理流程")
        else:
            print("\n❌ 儲存功能測試失敗")
    else:
        print("\n❌ 資料庫連接失敗，請檢查配置")
        print("💡 常見問題:")
        print("   1. 檢查 .env 檔案中的資料庫配置")
        print("   2. 確認資料庫服務正在運行")
        print("   3. 檢查防火牆設定")
        print("   4. 確認資料庫使用者權限")

if __name__ == "__main__":
    main()
