#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 模式檢查腳本
用於檢查當前使用的 AI 模式（Ollama 或 API）
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_ai_mode():
    """檢查 AI 模式設定"""
    
    print("🔍 檢查 AI 模式設定...")
    print("=" * 50)
    
    # 載入環境變數
    from dotenv import load_dotenv
    load_dotenv()
    
    # 讀取設定
    ai_mode = os.getenv('AI_MODE', 'ollama')
    ollama_model = os.getenv('OLLAMA_MODEL', 'qwen:7b')
    qwen_model = os.getenv('QWEN_MODEL', 'qwen-flash')
    qwen_api_key = os.getenv('QWEN_API_KEY', '')
    
    print(f"📋 當前設定：")
    print(f"  AI_MODE: {ai_mode}")
    print(f"  OLLAMA_MODEL: {ollama_model}")
    print(f"  QWEN_MODEL: {qwen_model}")
    print(f"  QWEN_API_KEY: {'已設定' if qwen_api_key and qwen_api_key != 'your_qwen_api_key' else '未設定'}")
    print()
    
    # 判斷當前模式
    if ai_mode == 'api':
        print("🌐 當前使用：API 模式")
        print(f"   模型：{qwen_model}")
        
        if qwen_api_key and qwen_api_key != 'your_qwen_api_key':
            print("   ✅ API Key 已設定")
        else:
            print("   ❌ API Key 未設定 - API 模式可能無法正常工作")
            
    else:
        print("🏠 當前使用：Ollama 本地模式")
        print(f"   模型：{ollama_model}")
        print("   💡 如需切換到 API 模式，請設定：")
        print("      AI_MODE=api")
        print("      QWEN_API_KEY=你的_api_key")
    
    print()
    
    # 檢查日誌檔案
    log_file = project_root / "logs" / "app.log"
    if log_file.exists():
        print("📄 查看最近的日誌記錄：")
        print("-" * 30)
        
        # 讀取最後 20 行日誌
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-20:] if len(lines) > 20 else lines
            
            for line in recent_lines:
                if 'AI 模式' in line or 'API 模式' in line or 'Ollama 模式' in line:
                    print(f"  {line.strip()}")
    else:
        print("📄 日誌檔案不存在，請先啟動服務")
    
    print()
    print("🔧 管理指令：")
    print("• 查看即時日誌：tail -f logs/app.log")
    print("• 重啟服務：sudo systemctl restart line-bot.service")
    print("• 查看服務狀態：sudo systemctl status line-bot.service")

def main():
    """主函數"""
    print("🤖 AI 模式檢查工具")
    print("=" * 50)
    print(f"⏰ 檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_ai_mode()

if __name__ == "__main__":
    main()
