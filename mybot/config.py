# config.py
# ============================================
# 寵物聊天機器人 - 資料庫配置
# ============================================
# 功能：從環境變數讀取資料庫連線設定
# 安全性：敏感資料（密碼）不直接寫在程式碼中
# 使用方式：在 .env 檔案中設定資料庫參數
# ============================================

import os

# 從環境變數讀取資料庫配置
# 如果環境變數不存在，使用預設值
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),        # 資料庫主機位址
    "user": os.getenv("DB_USER", "root"),              # 資料庫使用者名稱
    "password": os.getenv("DB_PASSWORD", "root"),      # 資料庫密碼
    "database": os.getenv("DB_NAME", "lbblacktech-laravel"),  # 資料庫名稱
    "charset": "utf8mb4"                               # 字元編碼（支援表情符號和繁體中文）
}

# API 基礎 URL（從環境變數讀取）
# BASE_URL: A 專案的 API 基礎 URL（用於 API 調用）
BASE_URL = os.getenv("BASE_URL", "https://test.ruru1211.xyz")

# 外部訪問 URL（從環境變數讀取）
# EXTERNAL_URL: LINE Bot 的外部訪問 URL（用於生成占卜卡圖片 URL）
EXTERNAL_URL = os.getenv("EXTERNAL_URL", os.getenv("BASE_URL", "https://chatbot.ruru1211.xyz"))