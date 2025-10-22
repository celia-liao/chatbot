# db_utils.py
# ============================================
# 寵物聊天機器人 - 資料庫工具
# ============================================
# 功能：提供資料庫連接和寵物資料查詢功能
# 資料來源：MySQL 資料庫
# 依賴：pymysql, cryptography
# ============================================

import pymysql

# 支援兩種運行方式
try:
    from mybot.config import DB_CONFIG
except ImportError:
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
            # 1. 查詢寵物基本資料（明確指定欄位）
            cursor.execute(
                "SELECT pet_id, pet_name, breed, personality, slogan, line_user_id "
                "FROM pets WHERE pet_id=%s", 
                (pet_id,)
            )
            pet = cursor.fetchone()
            
            # 除錯：顯示查詢到的寵物資料
            print(f"[DEBUG] 查詢 pet_id={pet_id} 的資料：{pet}")
            
            # 如果找不到寵物，返回 None
            if not pet:
                print(f"[DEBUG] 找不到 pet_id={pet_id} 的資料")
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
        result = {
            "name": pet["pet_name"],                           # 寵物名字
            "breed": pet["breed"] if pet.get("breed") else "寵物",  # 寵物品種（從資料庫讀取）
            "persona_key": pet["personality"] if pet.get("personality") else "friendly",  # 性格類型（從資料庫讀取）
            "cover_slogan": pet["slogan"] if pet.get("slogan") else "",  # 主人的愛意標語
            "lifeData": life,                                  # 生命軌跡事件列表
            "letter": letter["content"] if letter else ""      # 主人的信件內容
        }
        
        # 除錯：顯示最終返回的資料
        print(f"[DEBUG] 返回的寵物資料 - name: {result['name']}, breed: {result['breed']}, persona: {result['persona_key']}")
        
        return result

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
            # 查詢時可能欄位名稱是 id 或 pet_id，都試試
            cursor.execute(
                "SELECT pet_id, pet_name, breed FROM pets WHERE line_user_id=%s", 
                (line_user_id,)
            )
            result = cursor.fetchone()
            
            # 除錯：顯示查詢結果
            print(f"[DEBUG] 查詢 line_user_id={line_user_id} 的結果：{result}")
            
            # 優先使用 pet_id，如果沒有則用 id
            if result:
                pet_id = result.get("pet_id") or result.get("id")
                print(f"[DEBUG] 找到 pet_id={pet_id}, 寵物名稱={result.get('pet_name')}, 品種={result.get('breed')}")
                return pet_id
            else:
                print(f"[DEBUG] 找不到 line_user_id={line_user_id} 的寵物綁定")
                return None
    except Exception as e:
        print(f"[ERROR] 查詢使用者寵物對應失敗: {e}")
        return None
    finally:
        connection.close()


# ============================================
# 對話記錄資料庫操作函數
# ============================================

def save_chat_message(line_user_id: str, pet_id: int, role: str, message: str):
    """
    儲存一則對話訊息到資料庫
    
    參數:
        line_user_id (str): LINE 使用者 ID
        pet_id (int): 寵物 ID
        role (str): 角色，'user' 或 'assistant'
        message (str): 訊息內容
    
    返回:
        bool: 儲存成功返回 True，失敗返回 False
    
    說明:
        將對話記錄儲存到 chat_history 資料表
        每一則使用者訊息或寵物回覆都會獨立儲存
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_history (line_user_id, pet_id, role, message) "
                "VALUES (%s, %s, %s, %s)",
                (line_user_id, pet_id, role, message)
            )
            connection.commit()
            print(f"[DEBUG] 已儲存對話記錄 - user: {line_user_id}, pet: {pet_id}, role: {role}")
            return True
    except Exception as e:
        print(f"[ERROR] 儲存對話記錄失敗: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()


def get_chat_history(line_user_id: str, pet_id: int, limit: int = 10):
    """
    從資料庫讀取對話歷史
    
    參數:
        line_user_id (str): LINE 使用者 ID
        pet_id (int): 寵物 ID
        limit (int): 最多讀取幾輪對話（預設 10 輪，即 20 則訊息）
    
    返回:
        list: 對話歷史列表，格式為 [{"user": "...", "bot": "..."}, ...]
        空列表: 如果沒有對話記錄或發生錯誤
    
    說明:
        從 chat_history 資料表讀取最近的對話記錄
        自動組合成 user-bot 配對格式，供 AI 模型使用
        按時間順序排列（最舊的在前）
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # 讀取最近的對話（限制數量避免 prompt 過長）
            # limit * 2 是因為一輪對話包含 user 和 assistant 兩則訊息
            cursor.execute(
                "SELECT role, message FROM chat_history "
                "WHERE line_user_id=%s AND pet_id=%s "
                "ORDER BY created_at DESC "
                "LIMIT %s",
                (line_user_id, pet_id, limit * 2)
            )
            messages = cursor.fetchall()
            
            # 反轉順序（最舊的在前）
            messages.reverse()
            
            # 組合成 {"user": "...", "bot": "..."} 格式
            history = []
            temp_user_msg = None
            
            for msg in messages:
                if msg['role'] == 'user':
                    temp_user_msg = msg['message']
                elif msg['role'] == 'assistant' and temp_user_msg:
                    history.append({
                        "user": temp_user_msg,
                        "bot": msg['message']
                    })
                    temp_user_msg = None
            
            print(f"[DEBUG] 讀取對話歷史 - user: {line_user_id}, pet: {pet_id}, 共 {len(history)} 輪對話")
            return history
            
    except Exception as e:
        print(f"[ERROR] 讀取對話歷史失敗: {e}")
        return []
    finally:
        connection.close()


def clear_chat_history(line_user_id: str, pet_id: int):
    """
    清除特定使用者與特定寵物的對話記錄
    
    參數:
        line_user_id (str): LINE 使用者 ID
        pet_id (int): 寵物 ID
    
    返回:
        bool: 清除成功返回 True，失敗返回 False
    
    說明:
        刪除資料庫中該使用者與該寵物的所有對話記錄
        用於「清除」指令
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM chat_history WHERE line_user_id=%s AND pet_id=%s",
                (line_user_id, pet_id)
            )
            deleted_count = cursor.rowcount
            connection.commit()
            print(f"[DEBUG] 已清除對話記錄 - user: {line_user_id}, pet: {pet_id}, 刪除 {deleted_count} 則訊息")
            return True
    except Exception as e:
        print(f"[ERROR] 清除對話記錄失敗: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()
