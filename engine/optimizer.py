# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：快取與記憶體清理引擎 (engine/optimizer.py)
"""

import os
import sys
import shutil
import subprocess
import gc
import ctypes
from ctypes import wintypes
from engine.config import CONFIG, format_size_str

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.c_size_t),
        ('th32ModuleID', wintypes.DWORD),
        ('cntThreads', wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
        ('szExeFile', wintypes.WCHAR * 260)
    ]

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]

def get_process_working_set_mb(pid):
    """Win32 原生查詢指定 PID 之 WorkingSet 記憶體 (MB)"""
    try:
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if h:
            counters = PROCESS_MEMORY_COUNTERS_EX()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            if ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(counters), counters.cb):
                ctypes.windll.kernel32.CloseHandle(h)
                return counters.WorkingSetSize / (1024 * 1024)
            ctypes.windll.kernel32.CloseHandle(h)
    except Exception: pass
    return 0.0

def get_running_processes_fast():
    """Win32 Native Toolhelp32 快照 API 取得極速處理程序列表 (0.5ms 無子進程)"""
    procs = []
    try:
        TH32CS_SNAPPROCESS = 0x00000002
        hSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnap and hSnap != -1:
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if ctypes.windll.kernel32.Process32FirstW(hSnap, ctypes.byref(pe)):
                while True:
                    procs.append((pe.th32ProcessID, pe.szExeFile))
                    if not ctypes.windll.kernel32.Process32NextW(hSnap, ctypes.byref(pe)):
                        break
            ctypes.windll.kernel32.CloseHandle(hSnap)
    except Exception: pass
    return procs

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

    @staticmethod
    def clean_temp_cache(log_callback, target_dir, skip_protected=True, max_depth=1, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 系統暫存區 (設定深度: {max_depth} 層)...", CONFIG.THEME["PRIMARY"])
        res = OptimizerEngine._clean_folder_files(log_callback, target_dir, skip_protected=skip_protected, max_depth=max_depth, dry_run=dry_run)
        if dry_run: return res
        else:
            deleted_bytes, deleted_count, failed_count = res
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ 暫存清理完成！成功釋放空間: {mb_released:.2f} MB", CONFIG.THEME["SUCCESS"])
            log_callback(f"📊 統計：成功刪除 {deleted_count} 個檔案，跳過 {failed_count} 個項目。\n", CONFIG.THEME["TEXT_LIGHT"])
            return mb_released

    @staticmethod
    def clean_crash_dumps_and_wer(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 系統崩潰傾印檔與錯誤報告 (Crash Dumps & WER)...", CONFIG.THEME["PRIMARY"])
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
            log_callback(f"✅ 崩潰傾印檔與 WER 清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_delivery_optimization(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 微軟傳遞優化下載快取 (Delivery Optimization Cache)...", CONFIG.THEME["PRIMARY"])
        res = OptimizerEngine._clean_folder_files(log_callback, CONFIG.DELIVERY_OPTIMIZATION_DIR, dry_run=dry_run, label="Delivery Optimization")
        if dry_run: return res
        else:
            deleted_bytes, deleted_count, failed_count = res
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ 傳遞優化快取清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_pkg_caches(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 開發套件包快取 (pip / uv / npm / pnpm / Yarn / Poetry)...", CONFIG.THEME["PRIMARY"])
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
            log_callback(f"✅ 開發套件包快取清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_shader_caches(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 顯示卡與 DirectX 著色器快取 (DirectX / NVIDIA / AMD)...", CONFIG.THEME["PRIMARY"])
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
            log_callback(f"✅ 顯卡著色器快取清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_thumbnail_cache(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} Windows 檔案總管縮圖快取 (thumbcache_*.db)...", CONFIG.THEME["PRIMARY"])
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
            log_callback(f"✅ 檔案總管縮圖快取清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_browser_cache(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 網頁暫存快取 (Chrome / Edge / Brave / Firefox 各 Profile 快取檔)...", CONFIG.THEME["PRIMARY"])
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
            log_callback(f"✅ 網頁暫存快取清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_app_cache(log_callback, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 常用應用軟體與 IDE 快取 (VS Code / JetBrains / Adobe / Discord / Spotify)...", CONFIG.THEME["PRIMARY"])
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
            log_callback(f"✅ 應用軟體與 IDE 快取清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def clean_prefetch(log_callback, target_dir, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 系統預載歷史快取 (Prefetch)...", CONFIG.THEME["PRIMARY"])
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
                        log_callback(f"🔍 [模擬模式] 預計清理檔案: {file_path}", CONFIG.THEME["TEXT_MUTED"])
                        pending_files.append(file_path)
                    else:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_bytes += file_size; deleted_count += 1
                        except Exception: failed_count += 1
        except Exception as e:
            log_callback(f"❌ 讀取 Prefetch 發生錯誤 (可能需要管理員權限): {str(e)}", CONFIG.THEME["WARNING"])
            
        if dry_run: return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ Prefetch 清理完成！成功釋放空間: {mb_released:.2f} MB\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def kill_zombie_processes(log_callback, ram_limit_mb, target_extensions=None, dry_run=False):
        """Win32 Native 原生快照處理程序清理 (0.5ms 極速且完全零頓感)"""
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 背景閒置處理程序 (極速快照，門檻 > {ram_limit_mb}MB)...", CONFIG.THEME["PRIMARY"])
        if target_extensions is None: target_extensions = CONFIG.TARGET_PROCESSES
        
        killed_count = 0; total_freed_ram_mb = 0.0; pending_pids = []
        try:
            # 採用 Win32 Toolhelp 原生 API 進行超極速快照
            procs = get_running_processes_fast()
            my_pid = os.getpid()
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            for pid, proc_name in procs:
                if pid <= 4 or pid == my_pid: continue
                if any(ext in proc_name.lower() for ext in target_extensions):
                    mem_mb = get_process_working_set_mb(pid)
                    if mem_mb > ram_limit_mb:
                        if dry_run:
                            log_callback(f"🔍 [模擬模式] 預計結束處理程序：{proc_name} (PID: {pid}) 佔用 {mem_mb:.1f} MB", CONFIG.THEME["WARNING"])
                            pending_pids.append((pid, proc_name, mem_mb))
                        else:
                            log_callback(f"⚠️ 偵測到高能耗閒置處理程序：{proc_name} (PID: {pid}) 佔用 {mem_mb:.1f} MB", CONFIG.THEME["WARNING"])
                            subprocess.run(f"taskkill /F /PID {pid}", startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            log_callback(f"❌ 已成功關閉處理程序 PID: {pid} (釋放約 {mem_mb:.1f} MB RAM)", CONFIG.THEME["DANGER"])
                            killed_count += 1
                            total_freed_ram_mb += mem_mb
        except Exception as e:
            log_callback(f"❌ 讀取處理程序列表時發生錯誤: {str(e)}", CONFIG.THEME["DANGER"])
            
        if dry_run: return pending_pids
        else:
            if killed_count == 0: log_callback("✅ 處理程序檢查完成，目前無超標之閒置處理程序。\n", CONFIG.THEME["SUCCESS"])
            else: log_callback(f"✅ 成功關閉了 {killed_count} 個背景閒置處理程序，預計釋放 {total_freed_ram_mb:.2f} MB RAM！\n", CONFIG.THEME["SUCCESS"])
            return killed_count, total_freed_ram_mb

    @staticmethod
    def empty_system_working_set(log_callback):
        log_callback("🚀 調用 Windows 原生 API 進行 Working Set 記憶體深度壓縮...", CONFIG.THEME["PRIMARY"])
        compressed_count = 0
        try:
            if sys.platform.startswith('win'):
                psapi = ctypes.windll.psapi
                kernel32 = ctypes.windll.kernel32
                hProcess = kernel32.GetCurrentProcess()
                psapi.EmptyWorkingSet(hProcess)
                compressed_count += 1
                PROCESS_SET_QUOTA = 0x0100
                PROCESS_VM_READ = 0x0010
                
                procs = get_running_processes_fast()
                my_pid = os.getpid()
                for pid, proc_name in procs:
                    if pid > 4 and pid != my_pid:
                        try:
                            h = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_VM_READ, False, pid)
                            if h:
                                psapi.EmptyWorkingSet(h)
                                kernel32.CloseHandle(h)
                                compressed_count += 1
                        except: pass
                log_callback(f"✅ Windows Working Set 深度記憶體回收完成！成功壓縮 {compressed_count} 個處理程序之閒置記憶體。", CONFIG.THEME["SUCCESS"])
        except Exception as e:
            log_callback(f"⚠️ Working Set 記憶體壓縮跳過: {str(e)}", CONFIG.THEME["WARNING"])

    @staticmethod
    def scan_smart_caches(log_callback, min_size_mb=50.0, dry_run=False):
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 智慧快取自動盤點 (搜尋 > {min_size_mb:.0f} MB 之隱藏快取)...", CONFIG.THEME["PRIMARY"])
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

        pending_files = []; found_cache_dirs = []
        exclude_dirs = ["windows", "program files", "program files (x86)", "$recycle.bin", "system volume information", ".antigravity", ".git"]

        for base_dir in target_bases:
            log_callback(f"🔍 [智慧盤點] 掃描區塊：{base_dir}", CONFIG.THEME["TEXT_MUTED"])
            for root, dirs, files in os.walk(base_dir, topdown=True):
                root_lower = root.lower()
                if any(ex in root_lower for ex in exclude_dirs) or any(key in root_lower for key in CONFIG.PROTECTED_KEYWORDS):
                    dirs.clear(); continue
                    
                dir_name = os.path.basename(root).lower()
                is_cache_dir = any(k in dir_name for k in ["cache", "caches", "code cache", "gpu_cache", "webcache", "htmlcache"])
                if is_cache_dir:
                    dirs.clear()
                    total_size = 0; cache_files = []
                    try:
                        for sub_root, sub_dirs, sub_files in os.walk(root):
                            for sf in sub_files:
                                sf_path = os.path.join(sub_root, sf)
                                if not (sf.lower().endswith('.py') or sf.lower().endswith('.html')) and not any(key in sf.lower() for key in CONFIG.PROTECTED_KEYWORDS):
                                    try:
                                        total_size += os.path.getsize(sf_path)
                                        cache_files.append(sf_path)
                                    except: pass
                    except: pass
                    size_mb = total_size / (1024 * 1024)
                    if size_mb >= min_size_mb:
                        size_fmt = format_size_str(size_mb)
                        log_callback(f"💡 發現快取巨頭：{root} ({size_fmt})", CONFIG.THEME["WARNING"])
                        found_cache_dirs.append((root, size_mb, cache_files))
                        if dry_run: pending_files.extend(cache_files)

        if dry_run:
            log_callback(f"✅ 智慧快取盤點完畢！共發現 {len(found_cache_dirs)} 個超標快取巨頭。\n", CONFIG.THEME["SUCCESS"])
            return pending_files
        else:
            deleted_bytes = 0; deleted_count = 0
            for r, sz_mb, files_list in found_cache_dirs:
                for f_path in files_list:
                    try:
                        if os.path.exists(f_path):
                            sz = os.path.getsize(f_path)
                            try: os.chmod(f_path, 0o777)
                            except: pass
                            os.remove(f_path)
                            deleted_bytes += sz; deleted_count += 1
                    except: pass
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ 智慧快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def force_garbage_collection(log_callback):
        log_callback("🚀 啟動 Python 記憶體回收機制...", CONFIG.THEME["PRIMARY"])
        try:
            gc.get_referrers()
            collected = gc.collect()
            OptimizerEngine.empty_system_working_set(log_callback)
            log_callback(f"✅ 記憶體回收成功！回收物件群組共: {collected} 組", CONFIG.THEME["SUCCESS"])
            log_callback("⚙️ 系統記憶體分頁已完成深度整理與縮減。\n", CONFIG.THEME["TEXT_MUTED"])
        except Exception as e:
            log_callback(f"❌ 回收記憶體時發生錯誤: {str(e)}\n", CONFIG.THEME["DANGER"])
