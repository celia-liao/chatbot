# db_utils.py
# ============================================
# 寵物聊天機器人 - 資料庫工具
# ============================================
# 功能：提供資料庫連接和寵物資料查詢功能
# 資料來源：MySQL 資料庫
# 依賴：pymysql, cryptography
# ============================================

import pymysql
import requests
import json

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
    從 API 獲取寵物的完整資料
    
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
        None: 如果找不到該寵物或 API 請求失敗
    
    說明:
        此函數會從 API 獲取寵物資料：
        API 端點：https://test.ruru1211.xyz/api/pet-data-by-id/{pet_id}
        
        資料來源改為 API，不再直接查詢資料庫
    """
    try:
        # 從 API 獲取寵物資料
        api_url = f"https://test.ruru1211.xyz/api/pet-data-by-id/{pet_id}"
        print(f"[DEBUG] 從 API 獲取 pet_id={pet_id} 的資料：{api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # 如果 HTTP 狀態碼不是 200，會拋出異常
        
        data = response.json()
        
        # 檢查 API 回應是否成功
        if not data.get("success", False):
            print(f"[DEBUG] API 回傳失敗：{data}")
            return None
            
        pet_data = data.get("data")
        if not pet_data:
            print(f"[DEBUG] API 回傳的 data 為空")
            return None
        
        # 除錯：顯示 API 回傳的資料
        print(f"[DEBUG] API 回傳的寵物資料：{pet_data}")
        
        # 組合並返回完整的寵物資料（保持與原函數相同的格式）
        result = {
            "name": pet_data.get("name", ""),                           # 寵物名字
            "breed": pet_data.get("breed", "寵物"),                      # 寵物品種
            "persona_key": pet_data.get("persona_key", "friendly"),     # 性格類型
            "cover_slogan": pet_data.get("cover_slogan", ""),           # 主人的愛意標語
            "lifeData": pet_data.get("lifeData", []),                   # 生命軌跡事件列表
            "letter": pet_data.get("letter", "")                        # 主人的信件內容
        }
        
        # 除錯：顯示最終返回的資料
        print(f"[DEBUG] 返回的寵物資料 - name: {result['name']}, breed: {result['breed']}, persona: {result['persona_key']}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API 請求失敗: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] API 回傳的 JSON 格式錯誤: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 獲取寵物資料時發生錯誤: {e}")
        return None


def get_pet_id_by_line_user(line_user_id: str):
    """
    根據 LINE 使用者 ID 查詢對應的寵物 ID
    
    參數:
        line_user_id (str): LINE 使用者 ID
    
    返回:
        int: 對應的寵物 ID，如果找不到則返回 None
    
    說明:
        此函數會從 API 獲取 LINE 使用者對應的寵物 ID：
        API 端點：https://test.ruru1211.xyz/api/pet-id-by-line-user/{line_user_id}
        
        資料來源改為 API，不再直接查詢資料庫
    """
    try:
        # 從 API 獲取 LINE 使用者對應的寵物 ID
        api_url = f"https://test.ruru1211.xyz/api/pet-id-by-line-user/{line_user_id}"
        print(f"[DEBUG] 從 API 獲取 line_user_id={line_user_id} 對應的寵物 ID：{api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # 如果 HTTP 狀態碼不是 200，會拋出異常
        
        data = response.json()
        
        # 檢查 API 回應是否成功
        if not data.get("success", False):
            print(f"[DEBUG] API 回傳失敗：{data}")
            return None
            
        pet_data = data.get("data")
        if not pet_data:
            print(f"[DEBUG] API 回傳的 data 為空")
            return None
        
        # 除錯：顯示 API 回傳的資料
        print(f"[DEBUG] API 回傳的寵物資料：{pet_data}")
        
        # 取得寵物 ID
        pet_id = pet_data.get("pet_id")
        if pet_id is not None:
            print(f"[DEBUG] 找到 pet_id={pet_id}, 寵物名稱={pet_data.get('pet_name')}")
            return pet_id
        else:
            print(f"[DEBUG] API 回傳的資料中沒有 pet_id")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API 請求失敗: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] API 回傳的 JSON 格式錯誤: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 獲取寵物 ID 時發生錯誤: {e}")
        return None


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


def get_all_bound_users():
    """
    獲取所有已綁定 LINE 的使用者
    
    返回:
        list: 包含寵物 ID 和 LINE 使用者 ID 的字典列表，格式如下：
            [{"pet_id": int, "line_user_id": str}, ...]
        空列表: 如果沒有綁定使用者或發生錯誤
    
    說明:
        此函數會從 API 獲取所有已綁定 LINE 的使用者：
        API 端點：https://test.ruru1211.xyz/api/all-bound-users
        
        資料來源改為 API，不再直接查詢資料庫
    """
    try:
        # 從 API 獲取所有已綁定 LINE 的使用者
        api_url = "https://test.ruru1211.xyz/api/all-bound-users"
        print(f"[DEBUG] 從 API 獲取所有已綁定 LINE 的使用者：{api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # 如果 HTTP 狀態碼不是 200，會拋出異常
        
        data = response.json()
        
        # 檢查 API 回應是否成功
        if not data.get("success", False):
            print(f"[DEBUG] API 回傳失敗：{data}")
            return []
            
        users_data = data.get("data", [])
        if not users_data:
            print(f"[DEBUG] API 回傳的 data 為空或沒有綁定使用者")
            return []
        
        # 確保返回格式正確（每個元素包含 pet_id 和 line_user_id）
        users = []
        for user in users_data:
            if isinstance(user, dict) and user.get("pet_id") and user.get("line_user_id"):
                users.append({
                    "pet_id": user.get("pet_id"),
                    "line_user_id": user.get("line_user_id")
                })
        
        print(f"[DEBUG] 找到 {len(users)} 位已綁定 LINE 的使用者")
        return users
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API 請求失敗: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] API 回傳的 JSON 格式錯誤: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] 獲取綁定使用者時發生錯誤: {e}")
        return []
