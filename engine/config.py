# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：全域系統配置與白名單持久化 (engine/config.py)
職責：純粹收容全域設定、常數、路徑、JSON 讀寫與白名單管理，100% 絕不執行系統動作。
"""

import os

def format_size_str(mb_val):
    """容量單位動態轉換：大於等於 1024 MB 轉換為 GB 顯示，否則顯示 MB"""
    if mb_val >= 1024:
        return f"{mb_val / 1024:.2f} GB"
    else:
        return f"{mb_val:.1f} MB"

def get_portable_config_dir():
    """取得便攜版優先目錄：若當前目錄可寫入，優先使用主程式旁 config/ 資料夾，否則回退至 LocalAppData"""
    base_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    portable_dir = os.path.join(base_script_dir, "config")
    try:
        os.makedirs(portable_dir, exist_ok=True)
        test_file = os.path.join(portable_dir, ".perm_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return portable_dir
    except Exception:
        user_local = os.path.join(os.path.expanduser("~"), "AppData", "Local", "SystemOptimizerTool")
        os.makedirs(user_local, exist_ok=True)
        return user_local

class CONFIG:
    APP_NAME = "本機系統快取清理與記憶體優化工具"
    VERSION = "v5.0 (全碟儲存空間分析與宣告式快取規則表版)"
    
    DEFAULT_CPU_THRESHOLD = 80.0
    DEFAULT_PROCESS_RAM_LIMIT = 500
    TARGET_PROCESSES = ["python.exe", "node.exe"]
    
    USER_HOME = os.path.expanduser("~")
    TEMP_DIR = os.path.join(USER_HOME, "AppData", "Local", "Temp")
    PREFETCH_DIR = r"C:\Windows\Prefetch"
    
    CONFIG_BASE_DIR = get_portable_config_dir()
    CUSTOM_SCRIPT_JSON = os.path.join(CONFIG_BASE_DIR, "custom_scripts.json")
    STARTUP_BACKUP_JSON = os.path.join(CONFIG_BASE_DIR, "startup_backup.json")
    BACKUP_SHORTCUTS_DIR = os.path.join(CONFIG_BASE_DIR, "backup_shortcuts")
    WHITELIST_JSON = os.path.join(CONFIG_BASE_DIR, "whitelist.json")

    CRASH_DUMPS_DIR = os.path.join(USER_HOME, "AppData", "Local", "CrashDumps")
    WER_DIR = r"C:\ProgramData\Microsoft\Windows\WER"
    DELIVERY_OPTIMIZATION_DIR = r"C:\ProgramData\Microsoft\Windows\DeliveryOptimizationCache"
    
    PKG_CACHE_DIRS = [
        ("pip 快取目錄", os.path.join(USER_HOME, "AppData", "Local", "pip", "cache")),
        ("uv 快取 (Local)", os.path.join(USER_HOME, "AppData", "Local", "uv", "cache")),
        ("uv 快取 (Home)", os.path.join(USER_HOME, ".cache", "uv")),
        ("npm 快取目錄", os.path.join(USER_HOME, "AppData", "Local", "npm-cache")),
        ("pnpm 快取目錄", os.path.join(USER_HOME, "AppData", "Local", "pnpm", "cache")),
        ("Yarn 快取目錄", os.path.join(USER_HOME, "AppData", "Local", "Yarn", "Cache")),
        ("Poetry 快取目錄", os.path.join(USER_HOME, "AppData", "Local", "pypoetry", "Cache")),
    ]

    SHADER_CACHE_DIRS = [
        ("DirectX 著色器快取", os.path.join(USER_HOME, "AppData", "Local", "D3DSCache")),
        ("NVIDIA DX 快取", os.path.join(USER_HOME, "AppData", "Local", "NVIDIA", "DXCache")),
        ("NVIDIA NV 快取", os.path.join(USER_HOME, "AppData", "Local", "NVIDIA", "NV_Cache")),
        ("AMD 著色器快取", os.path.join(USER_HOME, "AppData", "Local", "AMD", "DxCache")),
    ]
    
    THUMBNAIL_CACHE_DIR = os.path.join(USER_HOME, "AppData", "Local", "Microsoft", "Windows", "Explorer")

    CHROME_USER_DATA = os.path.join(USER_HOME, "AppData", "Local", "Google", "Chrome", "User Data")
    EDGE_USER_DATA = os.path.join(USER_HOME, "AppData", "Local", "Microsoft", "Edge", "User Data")
    BRAVE_USER_DATA = os.path.join(USER_HOME, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data")
    FIREFOX_PROFILES = os.path.join(USER_HOME, "AppData", "Local", "Mozilla", "Firefox", "Profiles")
    
    APP_CACHE_DIRS = [
        ("VS Code 快取", os.path.join(USER_HOME, "AppData", "Roaming", "Code", "Cache")),
        ("VS Code 程式碼快取", os.path.join(USER_HOME, "AppData", "Roaming", "Code", "CachedData")),
        ("Discord 快取", os.path.join(USER_HOME, "AppData", "Roaming", "discord", "Cache")),
        ("Spotify 暫存區", os.path.join(USER_HOME, "AppData", "Local", "Spotify", "Storage")),
        ("Adobe 媒體快取檔", os.path.join(USER_HOME, "AppData", "Roaming", "Adobe", "Common", "Media Cache Files")),
        ("Adobe 媒體快取區", os.path.join(USER_HOME, "AppData", "Roaming", "Adobe", "Common", "Media Cache")),
    ]
    JETBRAINS_BASE_DIR = os.path.join(USER_HOME, "AppData", "Local", "JetBrains")

    SCAN_DEPTH_OPTIONS = {
        "僅首層目錄": 1,
        "掃描 2 層": 2,
        "掃描 3 層": 3,
        "無限制 (完整清理)": 999
    }
    DEFAULT_SCAN_DEPTH = "無限制 (完整清理)"
    DRY_RUN = True

    THEME = {
        "BG_DARK": "#0F0F17",
        "SIDEBAR_BG": "#13131E",
        "CARD_BG": "#1A1A28",
        "CARD_BORDER": "#2C2C45",
        "TEXT_LIGHT": "#E8E8F0",
        "TEXT_MUTED": "#9DA0C4",  # AccessLint: 符合 WCAG 2.1 4.5:1 AA 高對比標準
        "PRIMARY": "#5B7BFE",
        "PRIMARY_HOVER": "#4A68E8",
        "SUCCESS": "#2ECC8A",
        "SUCCESS_HOVER": "#25B87A",
        "WARNING": "#F0A500",
        "DANGER": "#FF4757",
        "DANGER_HOVER": "#E03050",
        "ACCENT": "#A78BFA"
    }
    
    DEFAULT_PROTECTED_KEYWORDS = [
        ".git", ".antigravity", "rules.md", "main.py", 
        "explorer.exe", "taskmgr.exe", "svchost.exe"
    ]
    PROTECTED_KEYWORDS = list(DEFAULT_PROTECTED_KEYWORDS)

def load_protected_keywords():
    """載入動態與持久化保護白名單"""
    try:
        import json
        if os.path.exists(CONFIG.WHITELIST_JSON):
            with open(CONFIG.WHITELIST_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    CONFIG.PROTECTED_KEYWORDS = list(dict.fromkeys(CONFIG.DEFAULT_PROTECTED_KEYWORDS + data))
                    return CONFIG.PROTECTED_KEYWORDS
    except Exception: pass
    CONFIG.PROTECTED_KEYWORDS = list(CONFIG.DEFAULT_PROTECTED_KEYWORDS)
    return CONFIG.PROTECTED_KEYWORDS

def save_protected_keywords(keywords_list):
    """保存動態保護白名單至 JSON"""
    try:
        import json
        os.makedirs(os.path.dirname(CONFIG.WHITELIST_JSON), exist_ok=True)
        unique_kw = list(dict.fromkeys(keywords_list))
        CONFIG.PROTECTED_KEYWORDS = unique_kw
        with open(CONFIG.WHITELIST_JSON, "w", encoding="utf-8") as f:
            json.dump(unique_kw, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
