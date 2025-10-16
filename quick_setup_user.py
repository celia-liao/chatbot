#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速設定 LINE 使用者對應
"""

from db_utils import get_connection

def setup_line_user(pet_id, line_user_id):
    """設定寵物的 LINE 使用者 ID"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # 更新 line_user_id
            cursor.execute(
                "UPDATE pets SET line_user_id = %s WHERE pet_id = %s",
                (line_user_id, pet_id)
            )
            connection.commit()
            
            # 確認更新
            cursor.execute(
                "SELECT pet_id, pet_name, line_user_id FROM pets WHERE pet_id = %s",
                (pet_id,)
            )
            result = cursor.fetchone()
            
            if result and result['line_user_id'] == line_user_id:
                print(f"✅ 設定成功！")
                print(f"  - 寵物 ID: {result['pet_id']}")
                print(f"  - 寵物名稱: {result['pet_name']}")
                print(f"  - LINE User ID: {result['line_user_id']}")
                return True
            else:
                print(f"❌ 設定失敗")
                return False
                
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 LINE 使用者快速設定工具")
    print("=" * 60)
    
    # 設定參數
    PET_ID = 1  # 寵物 ID
    LINE_USER_ID = "U6f37e67d13133e38eebed16a2974e60a"  # LINE 使用者 ID
    
    print(f"\n將要設定：")
    print(f"  寵物 ID: {PET_ID}")
    print(f"  LINE User ID: {LINE_USER_ID}")
    print()
    
    # 執行設定
    if setup_line_user(PET_ID, LINE_USER_ID):
        print("\n🎉 設定完成！現在可以在 LINE 中測試了。")
    else:
        print("\n❌ 設定失敗，請檢查錯誤訊息。")

