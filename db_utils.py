# db_utils.py
# ============================================
# 寵物聊天機器人 - 資料庫工具
# ============================================
# 功能：提供資料庫連接和寵物資料查詢功能
# 資料來源：MySQL 資料庫
# 依賴：pymysql, cryptography
# ============================================

import pymysql
from config import DB_CONFIG

def get_connection():
    """
    建立並返回 MySQL 資料庫連接
    
    返回:
        pymysql.Connection: 資料庫連接物件
    
    說明:
        - 使用 DictCursor 讓查詢結果以字典格式返回（更易讀）
        - 連接參數從 config.py 的 DB_CONFIG 讀取
        - 每次查詢後記得關閉連接，避免連接池耗盡
    """
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_pet_profile(pet_id: int):
    """
    從資料庫查詢寵物的完整資料
    
    參數:
        pet_id (int): 寵物的 ID
    
    返回:
        dict: 包含寵物完整資料的字典，結構如下：
            {
                "name": str,           # 寵物名字
                "breed": str,          # 品種
                "persona_key": str,    # 性格類型（對應 personalities.py）
                "cover_slogan": str,   # 主人的愛意表達
                "lifeData": list,      # 生命軌跡事件列表
                "letter": str          # 主人寫的信件
            }
        None: 如果找不到該寵物
    
    說明:
        此函數會查詢三個資料表：
        1. pets - 寵物基本資料
        2. timeline_events - 寵物的生命軌跡事件
        3. letters - 主人寫給寵物的信件
        
        資料查詢後會組合成統一格式，供 chatbot_ollama.py 使用
    
    資料庫結構:
        - pets 表：pet_id, pet_name, slogan
        - timeline_events 表：pet_id, age, event_title, event_description, is_visible, display_order
        - letters 表：pet_id, letter_content
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # 1. 查詢寵物基本資料
            cursor.execute("SELECT * FROM pets WHERE pet_id=%s", (pet_id,))
            pet = cursor.fetchone()
            
            # 如果找不到寵物，返回 None
            if not pet:
                return None

            # 2. 查詢生命軌跡（只顯示 is_visible=1 的事件，按 display_order 排序）
            cursor.execute(
                "SELECT age, event_title as title, event_description as text "
                "FROM timeline_events "
                "WHERE pet_id=%s AND is_visible=1 "
                "ORDER BY display_order", 
                (pet_id,)
            )
            life = cursor.fetchall()

            # 3. 查詢主人的信件
            cursor.execute("SELECT letter_content as content FROM letters WHERE pet_id=%s", (pet_id,))
            letter = cursor.fetchone()

        # 組合並返回完整的寵物資料
        return {
            "name": pet["pet_name"],                           # 寵物名字
            "breed": "黃金獵犬",                                # 寵物品種（暫時寫死，未來可從資料庫讀取）
            "persona_key": "easygoing",                        # 性格類型（暫時寫死，未來可從資料庫讀取）
            "cover_slogan": pet["slogan"] if pet["slogan"] else "",  # 主人的愛意標語
            "lifeData": life,                                  # 生命軌跡事件列表
            "letter": letter["content"] if letter else ""      # 主人的信件內容
        }

    finally:
        # 無論成功或失敗，都要關閉資料庫連接
        connection.close()


def get_pet_id_by_line_user(line_user_id: str):
    """
    根據 LINE 使用者 ID 查詢對應的寵物 ID
    
    參數:
        line_user_id (str): LINE 使用者 ID
    
    返回:
        int: 對應的寵物 ID，如果找不到則返回 None
    
    說明:
        從 pets 表中查詢 line_user_id 對應的寵物
        如果使用者尚未設定，返回 None
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pet_id FROM pets WHERE line_user_id=%s", 
                (line_user_id,)
            )
            result = cursor.fetchone()
            return result["pet_id"] if result else None
    except Exception as e:
        print(f"查詢使用者寵物對應失敗: {e}")
        return None
    finally:
        connection.close()
