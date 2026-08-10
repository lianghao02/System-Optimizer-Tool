# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：Windows 儲存空間與全碟檔案分析器 (engine/storage_analyzer.py)
職責：負責大型檔案、長期未使用檔案、三階段 SHA-256 重複檔案分析、Downloads 下載健檢與超大型 Log/Dump 診斷。
100% 唯讀分析，預設絕不安裝自動刪除。
"""

import os
import sys
import time
import hashlib
from datetime import datetime
from engine.config import CONFIG, format_size_str

class StorageAnalyzerEngine:
    # --------------------------------------------------------------------------
    # 1. 🔍 大型檔案分析器 (Large File Analyzer)
    # --------------------------------------------------------------------------
    @staticmethod
    def analyze_large_files(log_callback, min_size_mb=500.0):
        """分析本機巨型檔案 (>500MB / 1GB / 5GB)，包含 ISO, ZIP, MP4, DMP, GGUF, VHD 等"""
        log_callback(f"🔍 [空間分析] 開始盤點全碟 > {min_size_mb:.0f} MB 巨型檔案...", CONFIG.THEME["PRIMARY"])
        user_home = CONFIG.USER_HOME
        search_roots = [
            os.path.join(user_home, "Downloads"),
            os.path.join(user_home, "Desktop"),
            os.path.join(user_home, "Documents"),
            os.path.join(user_home, "Videos"),
            os.path.join(user_home, "AppData", "Local")
        ]
        for drive in ["D:\\", "E:\\", "F:\\"]:
            if os.path.exists(drive): search_roots.append(drive)

        large_files = []
        exclude_dirs = ["windows", "$recycle.bin", "system volume information", ".git"]

        min_bytes = min_size_mb * 1024 * 1024
        for base in search_roots:
            if not os.path.exists(base): continue
            for root, dirs, files in os.walk(base):
                root_lower = root.lower()
                if any(ex in root_lower for ex in exclude_dirs): dirs.clear(); continue
                for f in files:
                    try:
                        f_path = os.path.join(root, f)
                        sz = os.path.getsize(f_path)
                        if sz >= min_bytes:
                            mtime = os.path.getmtime(f_path)
                            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                            ext = os.path.splitext(f)[1].lower()

                            # 檔案類型標籤
                            category = "其他大檔"
                            if ext in ['.iso', '.img', '.vhd', '.vhdx']: category = "系統光碟/虛擬磁碟"
                            elif ext in ['.zip', '.7z', '.rar', '.tar', '.gz']: category = "大型壓縮檔"
                            elif ext in ['.mp4', '.mkv', '.mov', '.avi']: category = "大型影音檔"
                            elif ext in ['.dmp', '.mdmp', '.log', '.etl']: category = "系統傾印/日誌"
                            elif ext in ['.gguf', '.safetensors', '.bin', '.pth']: category = "AI 模型/權重檔"
                            elif ext in ['.exe', '.msi']: category = "大型軟體安裝包"

                            large_files.append({
                                "name": f,
                                "path": f_path,
                                "size_mb": sz / (1024 * 1024),
                                "size_fmt": format_size_str(sz / (1024 * 1024)),
                                "mtime_str": mtime_str,
                                "category": category
                            })
                    except: pass

        large_files.sort(key=lambda x: x["size_mb"], reverse=True)
        log_callback(f"✅ [空間分析] 巨型檔案盤點完成，共發現 {len(large_files)} 個巨型標的！\n", CONFIG.THEME["SUCCESS"])
        return large_files

    # --------------------------------------------------------------------------
    # 2. 🕒 長期未使用檔案分析 (Long Unused File Inspector)
    # --------------------------------------------------------------------------
    @staticmethod
    def analyze_aged_files(log_callback, min_size_mb=100.0, min_days=180):
        """分析大於 100MB 且超過 180/365/730 天未修改之檔案 (依據：檔案大小 + 最後修改時間 + 路徑)"""
        log_callback(f"🕒 [長期未使用] 盤點 > {min_size_mb:.0f} MB 且超過 {min_days} 天未修改之檔案...", CONFIG.THEME["PRIMARY"])
        user_home = CONFIG.USER_HOME
        search_roots = [
            os.path.join(user_home, "Downloads"),
            os.path.join(user_home, "Desktop"),
            os.path.join(user_home, "Documents")
        ]
        now_ts = time.time()
        aged_files = []
        min_bytes = min_size_mb * 1024 * 1024

        for base in search_roots:
            if not os.path.exists(base): continue
            for root, dirs, files in os.walk(base):
                for f in files:
                    try:
                        f_path = os.path.join(root, f)
                        sz = os.path.getsize(f_path)
                        if sz >= min_bytes:
                            mtime = os.path.getmtime(f_path)
                            days_diff = int((now_ts - mtime) / (24 * 3600))
                            if days_diff >= min_days:
                                aged_label = "可能長期未使用"
                                if days_diff >= 730: age_tier = "🔴 超過 2 年未修改"
                                elif days_diff >= 365: age_tier = "🟡 超過 1 年未修改"
                                else: age_tier = "🟢 超過半年未修改"

                                aged_files.append({
                                    "name": f,
                                    "path": f_path,
                                    "size_mb": sz / (1024 * 1024),
                                    "size_fmt": format_size_str(sz / (1024 * 1024)),
                                    "days_unused": days_diff,
                                    "age_tier": age_tier,
                                    "aged_label": aged_label
                                })
                    except: pass

        aged_files.sort(key=lambda x: x["days_unused"], reverse=True)
        log_callback(f"✅ [長期未使用] 分析完成，定位 {len(aged_files)} 個可能長期未使用之大型檔案。\n", CONFIG.THEME["SUCCESS"])
        return aged_files

    # --------------------------------------------------------------------------
    # 3. 👯 三階段 SHA-256 重複檔案分析器 (3-Stage Duplicate Finder)
    # --------------------------------------------------------------------------
    @staticmethod
    def analyze_duplicate_files(log_callback, target_dirs=None):
        """
        三階段高效能重複檔案比對演算法：
        第一階段：檔案大小同分組
        第二階段：讀取首尾 64KB 快速 Hash 分組
        第三階段：完整 SHA-256 內容 Hash 比對
        """
        if target_dirs is None:
            user_home = CONFIG.USER_HOME
            target_dirs = [
                os.path.join(user_home, "Downloads"),
                os.path.join(user_home, "Desktop"),
                os.path.join(user_home, "Documents")
            ]

        log_callback("👯 [重複檔案分析] 啟動三階段極速 SHA-256 比對引擎...", CONFIG.THEME["PRIMARY"])
        
        # 第一階段：按容量大小初篩
        size_dict = {}
        for base in target_dirs:
            if not os.path.exists(base): continue
            for root, dirs, files in os.walk(base):
                for f in files:
                    try:
                        f_path = os.path.join(root, f)
                        sz = os.path.getsize(f_path)
                        if sz > 1024 * 1024:  # 僅比對 > 1MB 檔案
                            size_dict.setdefault(sz, []).append(f_path)
                    except: pass

        candidate_groups = [paths for sz, paths in size_dict.items() if len(paths) > 1]
        log_callback(f"💡 第一階段：篩選出 {len(candidate_groups)} 組同容量候選群組。", CONFIG.THEME["TEXT_MUTED"])

        # 第二階段：首尾 64KB 區塊快速雜湊
        fast_hash_groups = []
        for group in candidate_groups:
            fast_dict = {}
            for path in group:
                try:
                    h = hashlib.md5()
                    sz = os.path.getsize(path)
                    with open(path, 'rb') as fp:
                        h.update(fp.read(65536))
                        if sz > 131072:
                            fp.seek(sz - 65536)
                            h.update(fp.read(65536))
                    fast_dict.setdefault(h.hexdigest(), []).append(path)
                except: pass
            for paths in fast_dict.values():
                if len(paths) > 1: fast_hash_groups.append(paths)

        log_callback(f"💡 第二階段：首尾區塊過濾後剩餘 {len(fast_hash_groups)} 組高擬似群組。", CONFIG.THEME["TEXT_MUTED"])

        # 第三階段：完整 SHA-256 精準 Hash 比對
        duplicate_groups = []
        for group in fast_hash_groups:
            full_hash_dict = {}
            for path in group:
                try:
                    h = hashlib.sha256()
                    with open(path, 'rb') as fp:
                        while chunk := fp.read(1048576):
                            h.update(chunk)
                    full_hash_dict.setdefault(h.hexdigest(), []).append(path)
                except: pass
            for sha, paths in full_hash_dict.values():
                if len(paths) > 1:
                    sz = os.path.getsize(paths[0])
                    waste_mb = (len(paths) - 1) * (sz / (1024 * 1024))
                    duplicate_groups.append({
                        "sha256": sha[:12],
                        "file_size_mb": sz / (1024 * 1024),
                        "file_size_fmt": format_size_str(sz / (1024 * 1024)),
                        "waste_mb": waste_mb,
                        "waste_fmt": format_size_str(waste_mb),
                        "paths": paths
                    })

        duplicate_groups.sort(key=lambda x: x["waste_mb"], reverse=True)
        log_callback(f"✅ [重複檔案分析] 比對完成！發現 {len(duplicate_groups)} 組 100% 內容完全相同之重複檔案。(預設全不勾選)\n", CONFIG.THEME["SUCCESS"])
        return duplicate_groups

    # --------------------------------------------------------------------------
    # 4. 📥 Downloads 下載資料夾健檢 (Downloads Health Checker)
    # --------------------------------------------------------------------------
    @staticmethod
    def analyze_downloads_health(log_callback):
        """下載資料夾健檢：診斷舊軟體安裝檔 (.exe/.msi >180天) 與冗餘壓縮檔 (同名資料夾並存)"""
        log_callback("📥 [下載健檢] 診斷 Downloads 與 Desktop 資料夾健康狀態...", CONFIG.THEME["PRIMARY"])
        downloads_dir = os.path.join(CONFIG.USER_HOME, "Downloads")
        if not os.path.exists(downloads_dir): return {"old_installers": [], "redundant_archives": []}

        now_ts = time.time()
        old_installers = []
        redundant_archives = []

        try:
            items = os.listdir(downloads_dir)
            folders_set = {item.lower() for item in items if os.path.isdir(os.path.join(downloads_dir, item))}

            for f in items:
                f_path = os.path.join(downloads_dir, f)
                if os.path.isfile(f_path):
                    f_lower = f.lower()
                    ext = os.path.splitext(f_lower)[1]
                    sz = os.path.getsize(f_path)
                    mtime = os.path.getmtime(f_path)
                    days_diff = int((now_ts - mtime) / (24 * 3600))

                    # 1. 舊安裝程式 (.exe / .msi > 180 天)
                    if ext in ['.exe', '.msi', '.msix', '.appx'] and days_diff >= 180:
                        old_installers.append({
                            "name": f,
                            "path": f_path,
                            "size_fmt": format_size_str(sz / (1024 * 1024)),
                            "days_old": days_diff
                        })

                    # 2. 冗餘壓縮檔診斷 (以解壓同名資料夾並存)
                    if ext in ['.zip', '.7z', '.rar']:
                        base_name = os.path.splitext(f_lower)[0]
                        if base_name in folders_set:
                            redundant_archives.append({
                                "name": f,
                                "path": f_path,
                                "size_fmt": format_size_str(sz / (1024 * 1024)),
                                "matched_folder": base_name
                            })
        except Exception: pass

        log_callback(f"✅ [下載健檢] 檢測完畢：發現 {len(old_installers)} 個舊版安裝程式，{len(redundant_archives)} 個已解壓同名封存檔。\n", CONFIG.THEME["SUCCESS"])
        return {
            "old_installers": old_installers,
            "redundant_archives": redundant_archives
        }
