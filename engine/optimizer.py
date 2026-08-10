# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：已知快取與檔案清理引擎 (engine/optimizer.py)
職責：專注於已知安全清理項目 (🟢 級別) 與可重建快取項目 (🟡 級別) 之檔案掃描與刪除。
"""

import os
import sys
import gc
from engine.config import CONFIG, format_size_str

class OptimizerEngine:
    @staticmethod
    def _clean_folder_files(log_callback, target_dir, skip_protected=True, max_depth=999, dry_run=False, label=""):
        if not os.path.exists(target_dir): return [] if dry_run else (0, 0, 0)
        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        for root, dirs, files in os.walk(target_dir):
            if root == target_dir: depth_level = 1
            else: depth_level = len(os.path.relpath(root, target_dir).split(os.sep)) + 1
            if depth_level >= max_depth: dirs.clear()
            if skip_protected and any(key in root.lower() for key in CONFIG.PROTECTED_KEYWORDS): continue
                
            for file in files:
                is_protected_ext = file.lower().endswith('.py') or file.lower().endswith('.html')
                if skip_protected and (is_protected_ext or any(key in file.lower() for key in CONFIG.PROTECTED_KEYWORDS)):
                    continue
                file_path = os.path.join(root, file)
                if dry_run:
                    prefix = f" ({label})" if label else ""
                    log_callback(f"🔍 [模擬模式] 預計清理檔案{prefix}: {file_path}", CONFIG.THEME["TEXT_MUTED"])
                    pending_files.append(file_path)
                else:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.chmod(file_path, 0o777)
                        os.remove(file_path)
                        deleted_bytes += file_size; deleted_count += 1
                    except Exception: failed_count += 1
                        
        if dry_run: return pending_files
        else: return deleted_bytes, deleted_count, failed_count

    # --------------------------------------------------------------------------
    # 🟢 第一層：安全清理 (Safe Cleaning - 預設勾選)
    # --------------------------------------------------------------------------
    @staticmethod
    def clean_temp_cache(log_callback, target_dir, skip_protected=True, max_depth=1, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟢 [安全清理] 使用者暫存區 (Temp)...", CONFIG.THEME["PRIMARY"])
        res = OptimizerEngine._clean_folder_files(log_callback, target_dir, skip_protected=skip_protected, max_depth=max_depth, dry_run=dry_run)
        if dry_run: return res
        else:
            deleted_bytes, deleted_count, failed_count = res
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [安全清理] 暫存清理完成！成功釋放空間: {format_size_str(mb_released)}", CONFIG.THEME["SUCCESS"])
            log_callback(f"📊 統計：成功刪除 {deleted_count} 個檔案，跳過 {failed_count} 個項目。\n", CONFIG.THEME["TEXT_LIGHT"])
            return mb_released

    @staticmethod
    def clean_crash_dumps_and_wer(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟢 [安全清理] 系統崩潰傾印檔與錯誤報告 (CrashDumps & WER)...", CONFIG.THEME["PRIMARY"])
        targets = [("CrashDumps", CONFIG.CRASH_DUMPS_DIR), ("Windows 錯誤報告", CONFIG.WER_DIR)]
        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        for label, path in targets:
            res = OptimizerEngine._clean_folder_files(log_callback, path, dry_run=dry_run, label=label)
            if dry_run: pending_files.extend(res)
            else:
                b, c, f = res
                deleted_bytes += b; deleted_count += c; failed_count += f
        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [安全清理] 崩潰傾印檔與 WER 清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_delivery_optimization(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟢 [安全清理] 微軟傳遞優化下載快取...", CONFIG.THEME["PRIMARY"])
        res = OptimizerEngine._clean_folder_files(log_callback, CONFIG.DELIVERY_OPTIMIZATION_DIR, dry_run=dry_run, label="Delivery Optimization")
        if dry_run: return res
        else:
            deleted_bytes, deleted_count, failed_count = res
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [安全清理] 傳遞優化快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_pkg_caches(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟢 [安全清理] 開發套件包快取 (pip / uv / npm / Yarn / Poetry)...", CONFIG.THEME["PRIMARY"])
        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        for label, path in CONFIG.PKG_CACHE_DIRS:
            res = OptimizerEngine._clean_folder_files(log_callback, path, dry_run=dry_run, label=label)
            if dry_run: pending_files.extend(res)
            else:
                b, c, f = res
                deleted_bytes += b; deleted_count += c; failed_count += f
        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [安全清理] 開發套件包快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_browser_cache(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟢 [安全清理] 網頁暫存快取 (Chrome / Edge / Brave / Firefox)...", CONFIG.THEME["PRIMARY"])
        target_dirs = []
        for browser_label, base_dir in [("Chrome", CONFIG.CHROME_USER_DATA), ("Edge", CONFIG.EDGE_USER_DATA), ("Brave", CONFIG.BRAVE_USER_DATA)]:
            if os.path.exists(base_dir):
                for item in os.listdir(base_dir):
                    item_path = os.path.join(base_dir, item)
                    if os.path.isdir(item_path) and (item.lower() == "default" or item.lower().startswith("profile ")):
                        cache_path = os.path.join(item_path, "Cache")
                        code_cache_path = os.path.join(item_path, "Code Cache")
                        if os.path.exists(cache_path): target_dirs.append((f"{browser_label} ({item}) 快取", cache_path))
                        if os.path.exists(code_cache_path): target_dirs.append((f"{browser_label} ({item}) Code 快取", code_cache_path))
        if os.path.exists(CONFIG.FIREFOX_PROFILES):
            for p in os.listdir(CONFIG.FIREFOX_PROFILES):
                p_path = os.path.join(CONFIG.FIREFOX_PROFILES, p)
                if os.path.isdir(p_path):
                    cache2_path = os.path.join(p_path, "cache2")
                    if os.path.exists(cache2_path): target_dirs.append((f"Firefox ({p}) 快取", cache2_path))

        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        for label, path in target_dirs:
            res = OptimizerEngine._clean_folder_files(log_callback, path, dry_run=dry_run, label=label)
            if dry_run: pending_files.extend(res)
            else:
                b, c, f = res
                deleted_bytes += b; deleted_count += c; failed_count += f
                            
        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [安全清理] 網頁暫存快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    # --------------------------------------------------------------------------
    # 🟡 第二層：可重建快取 (Rebuildable Cache - 預設不勾選)
    # --------------------------------------------------------------------------
    @staticmethod
    def clean_shader_caches(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟡 [可重建快取] 顯示卡與 DirectX 著色器快取...", CONFIG.THEME["WARNING"])
        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        for label, path in CONFIG.SHADER_CACHE_DIRS:
            res = OptimizerEngine._clean_folder_files(log_callback, path, dry_run=dry_run, label=label)
            if dry_run: pending_files.extend(res)
            else:
                b, c, f = res
                deleted_bytes += b; deleted_count += c; failed_count += f
        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [可重建快取] 顯卡著色器快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_thumbnail_cache(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟡 [可重建快取] 檔案總管縮圖快取 (thumbcache_*.db)...", CONFIG.THEME["WARNING"])
        target_dir = CONFIG.THUMBNAIL_CACHE_DIR
        if not os.path.exists(target_dir): return [] if dry_run else 0
        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        try:
            for file in os.listdir(target_dir):
                if file.lower().startswith("thumbcache_") and file.lower().endswith(".db"):
                    file_path = os.path.join(target_dir, file)
                    if dry_run:
                        log_callback(f"🔍 [模擬模式] 預計清理縮圖快取: {file_path}", CONFIG.THEME["TEXT_MUTED"])
                        pending_files.append(file_path)
                    else:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.chmod(file_path, 0o777)
                            os.remove(file_path)
                            deleted_bytes += file_size; deleted_count += 1
                        except Exception: failed_count += 1
        except Exception as e:
            log_callback(f"⚠️ 存取縮圖快取資料夾時發生異常: {str(e)}", CONFIG.THEME["WARNING"])

        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [可重建快取] 縮圖快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_app_cache(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🟡 [可重建快取] 常用軟體與 IDE 快取 (VS Code / JetBrains / Adobe)...", CONFIG.THEME["WARNING"])
        target_dirs = list(CONFIG.APP_CACHE_DIRS)
        if os.path.exists(CONFIG.JETBRAINS_BASE_DIR):
            for item in os.listdir(CONFIG.JETBRAINS_BASE_DIR):
                item_path = os.path.join(CONFIG.JETBRAINS_BASE_DIR, item)
                if os.path.isdir(item_path):
                    jb_cache = os.path.join(item_path, "system", "caches")
                    jb_log = os.path.join(item_path, "system", "log")
                    if os.path.exists(jb_cache): target_dirs.append((f"JetBrains ({item}) 索引快取", jb_cache))
                    if os.path.exists(jb_log): target_dirs.append((f"JetBrains ({item}) 日誌檔", jb_log))

        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        for label, path in target_dirs:
            res = OptimizerEngine._clean_folder_files(log_callback, path, dry_run=dry_run, label=label)
            if dry_run: pending_files.extend(res)
            else:
                b, c, f = res
                deleted_bytes += b; deleted_count += c; failed_count += f
                            
        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [可重建快取] 應用軟體快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    # --------------------------------------------------------------------------
    # 🔴 第三層：進階項目 (Advanced Items - Prefetch，預設不勾選)
    # --------------------------------------------------------------------------
    @staticmethod
    def clean_prefetch(log_callback, target_dir, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 🔴 [進階項目] 系統預載歷史 (Prefetch)...", CONFIG.THEME["DANGER"])
        log_callback("⚠️ 提示：Prefetch 不屬於一般垃圾，清理後系統需要時間重新建立預載檔，短時間內程式啟動可能變慢。", CONFIG.THEME["WARNING"])
        if not os.path.exists(target_dir):
            log_callback(f"⚠️ 目標路徑不存在，自動跳過：{target_dir}", CONFIG.THEME["WARNING"])
            return [] if dry_run else 0
        deleted_bytes = 0; deleted_count = 0; failed_count = 0; pending_files = []
        try:
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    if file.lower().endswith('.py') or file.lower().endswith('.html'): continue
                    file_path = os.path.join(root, file)
                    if dry_run:
                        log_callback(f"🔍 [模擬模式] 預計清理 Prefetch: {file_path}", CONFIG.THEME["TEXT_MUTED"])
                        pending_files.append(file_path)
                    else:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_bytes += file_size; deleted_count += 1
                        except Exception: failed_count += 1
        except Exception as e:
            log_callback(f"❌ 讀取 Prefetch 發生錯誤: {str(e)}", CONFIG.THEME["WARNING"])
            
        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ [進階項目] Prefetch 清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def force_python_gc(log_callback):
        try:
            gc.get_referrers()
            collected = gc.collect()
            log_callback(f"✅ Python 垃圾回收成功，釋放 {collected} 組記憶體物件。", CONFIG.THEME["TEXT_MUTED"])
        except Exception: pass
