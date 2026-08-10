# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：大型快取分析器 (engine/cache_inspector.py)
職責：負責全碟 >50MB 大型快取的動態偵測、分類評估與風險等級標註。100% 只讀分析，未知項目絕不自動刪除。
"""

import os
from engine.config import CONFIG, format_size_str

class CacheInspectorEngine:
    @staticmethod
    def inspect_large_caches(log_callback, min_size_mb=50.0):
        """
        大型快取分析器 (Large Cache Inspector)：
        掃描全碟大型快取目錄，列出 [名稱 | 完整路徑 | 容量 | 類型 | 風險評估 | 建議處置]。
        100% 純粹檢視分析，未知項目絕不安裝自動刪除。
        """
        log_callback(f"🔍 [快取分析器] 開始偵測 > {min_size_mb:.0f} MB 之大型快取巨頭...", CONFIG.THEME["PRIMARY"])
        target_bases = []
        user_home = CONFIG.USER_HOME
        appdata_local = os.path.join(user_home, "AppData", "Local")
        appdata_roaming = os.path.join(user_home, "AppData", "Roaming")
        programdata = r"C:\ProgramData"
        
        for path in [appdata_local, appdata_roaming, programdata]:
            if os.path.exists(path): target_bases.append(path)
        for drive_letter in ['D', 'E', 'F']:
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path): target_bases.append(drive_path)

        inspected_results = []
        exclude_dirs = ["windows", "program files", "program files (x86)", "$recycle.bin", "system volume information", ".antigravity", ".git"]

        for base_dir in target_bases:
            for root, dirs, files in os.walk(base_dir, topdown=True):
                root_lower = root.lower()
                if any(ex in root_lower for ex in exclude_dirs) or any(key in root_lower for key in CONFIG.PROTECTED_KEYWORDS):
                    dirs.clear(); continue
                    
                dir_name = os.path.basename(root).lower()
                is_cache_dir = any(k in dir_name for k in ["cache", "caches", "code cache", "gpu_cache", "webcache", "htmlcache"])
                if is_cache_dir:
                    dirs.clear()
                    total_size = 0; file_count = 0
                    try:
                        for sub_root, sub_dirs, sub_files in os.walk(root):
                            for sf in sub_files:
                                sf_path = os.path.join(sub_root, sf)
                                if not (sf.lower().endswith('.py') or sf.lower().endswith('.html')) and not any(key in sf.lower() for key in CONFIG.PROTECTED_KEYWORDS):
                                    try:
                                        total_size += os.path.getsize(sf_path)
                                        file_count += 1
                                    except: pass
                    except: pass

                    size_mb = total_size / (1024 * 1024)
                    if size_mb >= min_size_mb:
                        # 進行風險評估與分類標註
                        risk_level, category, recommendation, is_safe_to_auto_clean = CacheInspectorEngine.assess_cache_risk(root)
                        size_fmt = format_size_str(size_mb)
                        
                        item_info = {
                            "name": os.path.basename(root),
                            "path": root,
                            "size_mb": size_mb,
                            "size_fmt": size_fmt,
                            "file_count": file_count,
                            "category": category,
                            "risk_level": risk_level,
                            "recommendation": recommendation,
                            "is_safe_to_auto_clean": is_safe_to_auto_clean
                        }
                        inspected_results.append(item_info)
                        
                        log_tag = CONFIG.THEME["WARNING"] if is_safe_to_auto_clean else CONFIG.THEME["TEXT_MUTED"]
                        log_callback(f"💡 發現快取分析標的 [{category}]: {root} ({size_fmt}) -> 風險：{risk_level}", log_tag)

        log_callback(f"✅ 快取分析完畢！共定位 {len(inspected_results)} 個大型快取標的。(未知與高風險項目已排除自動清理)\n", CONFIG.THEME["SUCCESS"])
        return inspected_results

    @staticmethod
    def assess_cache_risk(path_str):
        """判定快取目錄風險等級與處置建議"""
        p_lower = path_str.lower()
        
        if any(b in p_lower for b in ["google\\chrome", "microsoft\\edge", "bravesoftware"]):
            return "🟢 安全", "網頁暫存快取", "完全安全，清除後瀏覽器會自動重建", True
        elif any(s in p_lower for s in ["d3dscache", "dxcache", "nv_cache", "amd\\dxcache"]):
            return "🟡 可重建", "顯示卡著色器快取", "清除後遊戲或圖形軟體可能短暫重新編譯 Shader", True
        elif "code\\cacheddata" in p_lower or "jetbrains" in p_lower:
            return "🟡 建議關閉 IDE", "開發工具索引快取", "建議先關閉編輯器再執行清理", True
        elif "pip\\cache" in p_lower or "npm-cache" in p_lower or "uv\\cache" in p_lower:
            return "🟢 安全", "套件下載快取", "安全，僅清除本機下載對照暫存", True
        else:
            return "🔴 未知/人工確認", "未知應用程式快取", "⚠️ 未知項目：請人工點擊開啟檔案位置確認後再決定", False
