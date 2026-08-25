# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：快取宣告式規則表與鎖定檢測 (engine/cache_rules.py)
職責：提供 CacheRule 宣告式物件與全系統快取規則註冊表，支援應用程式執行中鎖定檢測。
"""

import os
import sys

class CacheRule:
    def __init__(self, name, category, patterns, risk_level="safe", requires_closed_app=False, process_names=None):
        self.name = name
        self.category = category
        self.patterns = patterns
        self.risk_level = risk_level  # "safe" (🟢), "rebuildable" (🟡), "advanced" (🔴)
        self.requires_closed_app = requires_closed_app
        self.process_names = process_names or []

class CacheRuleRegistry:
    @staticmethod
    def get_default_rules():
        """取得系統內建全量宣告式快取規則清單"""
        user_home = os.path.expanduser("~")
        local_appdata = os.path.join(user_home, "AppData", "Local")
        roaming_appdata = os.path.join(user_home, "AppData", "Roaming")

        rules = [
            # 🟢 第一層：安全清理 (Safe Cleaning)
            CacheRule(
                name="使用者暫存區 (Temp)",
                category="系統與使用者暫存",
                patterns=[os.path.join(local_appdata, "Temp")],
                risk_level="safe"
            ),
            CacheRule(
                name="系統崩潰傾印與 WER 報告",
                category="系統診斷檔",
                patterns=[
                    os.path.join(local_appdata, "CrashDumps"),
                    r"C:\ProgramData\Microsoft\Windows\WER"
                ],
                risk_level="safe"
            ),
            CacheRule(
                name="微軟傳遞優化下載快取",
                category="系統更新快取",
                patterns=[r"C:\ProgramData\Microsoft\Windows\DeliveryOptimizationCache"],
                risk_level="safe"
            ),
            CacheRule(
                name="開發套件包快取 (pip / uv / npm / Yarn / Poetry)",
                category="開發工具快取",
                patterns=[
                    os.path.join(local_appdata, "pip", "cache"),
                    os.path.join(local_appdata, "uv", "cache"),
                    os.path.join(user_home, ".cache", "uv"),
                    os.path.join(local_appdata, "npm-cache"),
                    os.path.join(local_appdata, "pnpm", "cache"),
                    os.path.join(local_appdata, "Yarn", "Cache"),
                    os.path.join(local_appdata, "pypoetry", "Cache"),
                ],
                risk_level="safe"
            ),
            CacheRule(
                name="Google Chrome 網頁快取",
                category="瀏覽器快取",
                patterns=[
                    os.path.join(local_appdata, "Google", "Chrome", "User Data", "Default", "Cache"),
                    os.path.join(local_appdata, "Google", "Chrome", "User Data", "Default", "Code Cache")
                ],
                risk_level="safe",
                requires_closed_app=True,
                process_names=["chrome.exe"]
            ),
            CacheRule(
                name="Microsoft Edge 網頁快取",
                category="瀏覽器快取",
                patterns=[
                    os.path.join(local_appdata, "Microsoft", "Edge", "User Data", "Default", "Cache"),
                    os.path.join(local_appdata, "Microsoft", "Edge", "User Data", "Default", "Code Cache")
                ],
                risk_level="safe",
                requires_closed_app=True,
                process_names=["msedge.exe"]
            ),
            CacheRule(
                name="Brave Browser 網頁快取",
                category="瀏覽器快取",
                patterns=[
                    os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Cache")
                ],
                risk_level="safe",
                requires_closed_app=True,
                process_names=["brave.exe"]
            ),

            # 🟡 第二層：可重建快取 (Rebuildable Cache)
            CacheRule(
                name="VS Code 編輯器快取",
                category="IDE 索引快取",
                patterns=[
                    os.path.join(roaming_appdata, "Code", "Cache"),
                    os.path.join(roaming_appdata, "Code", "CachedData")
                ],
                risk_level="rebuildable",
                requires_closed_app=True,
                process_names=["code.exe"]
            ),
            CacheRule(
                name="JetBrains IDE 系統與索引快取",
                category="IDE 索引快取",
                patterns=[os.path.join(local_appdata, "JetBrains")],
                risk_level="rebuildable",
                requires_closed_app=True,
                process_names=["idea64.exe", "pycharm64.exe", "clion64.exe", "datagrip64.exe"]
            ),
            CacheRule(
                name="顯示卡著色器快取 (DirectX / NVIDIA / AMD)",
                category="繪圖著色器快取",
                patterns=[
                    os.path.join(local_appdata, "D3DSCache"),
                    os.path.join(local_appdata, "NVIDIA", "DXCache"),
                    os.path.join(local_appdata, "NVIDIA", "NV_Cache"),
                    os.path.join(local_appdata, "AMD", "DxCache"),
                ],
                risk_level="rebuildable"
            ),
            CacheRule(
                name="檔案總管縮圖快取 (thumbcache)",
                category="系統快取",
                patterns=[os.path.join(local_appdata, "Microsoft", "Windows", "Explorer")],
                risk_level="rebuildable"
            ),

            # 🔴 第三層：進階項目 (Advanced Items)
            CacheRule(
                name="系統預載歷史 (Prefetch)",
                category="系統預載檔",
                patterns=[r"C:\Windows\Prefetch"],
                risk_level="advanced"
            ),
        ]
        return rules

    @staticmethod
    def check_running_app_locks(rule):
        """檢查指定 CacheRule 對應之應用程序目前是否執行中 (鎖定防護)"""
        if not rule.requires_closed_app or not rule.process_names:
            return False, []
        try:
            from engine.memory import get_running_processes_fast
            running_procs = get_running_processes_fast()
            running_names = [p_name.lower() for _, p_name in running_procs]
            
            matched = [p for p in rule.process_names if p.lower() in running_names]
            if matched:
                return True, matched
        except Exception: pass
        return False, []
