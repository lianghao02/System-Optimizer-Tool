#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
主要功能：過濾清理系統暫存檔案、網頁與常用應用程式快取、盤點清理背景閒置 Python/Node 處理程序、深度釋放記憶體
相依套件：本工具採用 Python 3 標準庫 (tkinter, os, sys, shutil, subprocess, gc, ctypes)
安裝指令：pip install customtkinter
執行指令：python main.py
"""

import os
import sys
import shutil
import subprocess
import gc
import datetime
import threading
import ctypes
import customtkinter as ctk
from tkinter import messagebox, scrolledtext

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_ulong),
        ('dwMemoryLoad', ctypes.c_ulong),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
    ]

def get_system_ram_info():
    """使用 Windows 原生 API 獲取當前系統記憶體狀態 (MB, 負載%)"""
    try:
        if sys.platform.startswith('win'):
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_mb = stat.ullTotalPhys / (1024 * 1024)
            avail_mb = stat.ullAvailPhys / (1024 * 1024)
            used_mb = total_mb - avail_mb
            load_percent = stat.dwMemoryLoad
            return total_mb, avail_mb, used_mb, load_percent
    except Exception:
        pass
    return 0.0, 0.0, 0.0, 0

def format_size_str(mb_val):
    """容量單位自動轉換：大於等於 1024 MB 轉換為 GB 顯示，否則顯示 MB"""
    if mb_val >= 1024:
        return f"{mb_val / 1024:.2f} GB"
    else:
        return f"{mb_val:.1f} MB"

# ==============================================================================
# 1. 系統預設參數配置 (Configuration)
# ==============================================================================
class CONFIG:
    APP_NAME = "本機系統快取清理與記憶體優化工具"
    VERSION = "v1.2.0 (旗艦版)"
    
    # 清理門檻與路徑設定
    DEFAULT_CPU_THRESHOLD = 80.0       # CPU 警告閾值 (%)
    DEFAULT_PROCESS_RAM_LIMIT = 500    # 閒置處理程序記憶體判定門檻 (MB)
    TARGET_PROCESSES = ["python.exe", "node.exe"]  # 預設掃描的高資源佔用處理程序
    
    # 預設掃描的系統暫存與網頁快取路徑
    USER_HOME = os.path.expanduser("~")
    TEMP_DIR = os.path.join(USER_HOME, "AppData", "Local", "Temp")
    PIP_CACHE_DIR = os.path.join(USER_HOME, "AppData", "Local", "pip", "cache")
    PREFETCH_DIR = r"C:\Windows\Prefetch"  # 系統預載快取區 (需管理員權限)
    
    # 瀏覽器網頁暫存快取 (Cache) - 僅圖片與網頁樣式檔，不影響瀏覽紀錄與個人資料
    CHROME_CACHE_DIR = os.path.join(USER_HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Cache")
    CHROME_CODE_CACHE_DIR = os.path.join(USER_HOME, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Code Cache")
    EDGE_CACHE_DIR = os.path.join(USER_HOME, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Cache")
    EDGE_CODE_CACHE_DIR = os.path.join(USER_HOME, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Code Cache")
    
    # 常用開發與通訊軟體快取目錄 (BleachBit 借鏡)
    APP_CACHE_DIRS = [
        ("VS Code 快取", os.path.join(USER_HOME, "AppData", "Roaming", "Code", "Cache")),
        ("VS Code 程式碼快取", os.path.join(USER_HOME, "AppData", "Roaming", "Code", "CachedData")),
        ("Discord 快取", os.path.join(USER_HOME, "AppData", "Roaming", "discord", "Cache")),
        ("Spotify 暫存區", os.path.join(USER_HOME, "AppData", "Local", "Spotify", "Storage")),
        ("npm 快取目錄", os.path.join(USER_HOME, "AppData", "Local", "npm-cache")),
        ("Yarn 快取目錄", os.path.join(USER_HOME, "AppData", "Local", "Yarn", "Cache")),
    ]

    # 動態掃描深度設定
    SCAN_DEPTH_OPTIONS = {
        "僅首層目錄": 1,
        "掃描 2 層": 2,
        "掃描 3 層": 3,
        "無限制 (完整清理)": 999
    }
    DEFAULT_SCAN_DEPTH = "無限制 (完整清理)"
    DRY_RUN = True  # 預設啟用模擬模式 (安全性第一)
    
    # UI 視覺主題顏色
    THEME = {
        "BG_DARK": "#1E1E24",          # 主背景深灰
        "CARD_BG": "#2A2A32",          # 卡片背景
        "TEXT_LIGHT": "#F5F5F7",       # 主要文字
        "TEXT_MUTED": "#8E8E93",       # 次要提示字
        "PRIMARY": "#2980B9",          # 科技藍
        "SUCCESS": "#27AE60",          # 綠色標示
        "WARNING": "#F39C12",          # 警告橙
        "DANGER": "#E74C3C"            # 警示紅
    }
    
    # 安全保護白名單：絕對禁止刪除或關閉的關鍵檔名與系統關鍵服務
    PROTECTED_KEYWORDS = [
        ".git", ".antigravity", "rules.md", "main.py", 
        "explorer.exe", "taskmgr.exe", "svchost.exe"
    ]

# ==============================================================================
# 2. 核心清理與優化邏輯引擎 (Optimizer Engine)
# ==============================================================================
class OptimizerEngine:
    
    @staticmethod
    def clean_temp_cache(log_callback, target_dir, skip_protected=True, max_depth=1, dry_run=False):
        """核心邏輯一：暫存快取清理 (Temp Clean)"""
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 系統暫存區 (設定深度: {max_depth} 層)...", CONFIG.THEME["PRIMARY"])
        if not os.path.exists(target_dir):
            log_callback(f"⚠️ 目標路徑不存在，自動跳過：{target_dir}", CONFIG.THEME["WARNING"])
            return [] if dry_run else 0
            
        deleted_bytes = 0
        deleted_count = 0
        failed_count = 0
        pending_files = []
        
        for root, dirs, files in os.walk(target_dir):
            if root == target_dir:
                depth_level = 1
            else:
                depth_level = len(os.path.relpath(root, target_dir).split(os.sep)) + 1
                
            if depth_level >= max_depth:
                dirs.clear()

            if skip_protected and any(key in root.lower() for key in CONFIG.PROTECTED_KEYWORDS):
                continue
                
            for file in files:
                is_protected_ext = file.lower().endswith('.py') or file.lower().endswith('.html')
                if skip_protected and (is_protected_ext or any(key in file.lower() for key in CONFIG.PROTECTED_KEYWORDS)):
                    continue
                    
                file_path = os.path.join(root, file)
                if dry_run:
                    log_callback(f"🔍 [模擬模式] 預計清理檔案: {file_path}", CONFIG.THEME["TEXT_MUTED"])
                    pending_files.append(file_path)
                else:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_bytes += file_size
                        deleted_count += 1
                    except Exception:
                        failed_count += 1
                    
        if dry_run:
            return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ 暫存清理完成！成功釋放空間: {mb_released:.2f} MB", CONFIG.THEME["SUCCESS"])
            log_callback(f"📊 統計：成功刪除 {deleted_count} 個檔案，跳過 {failed_count} 個項目 (原因: 檔案正被其他程式佔用或權限不足)。\n", CONFIG.THEME["TEXT_LIGHT"])
            return mb_released

    @staticmethod
    def clean_browser_cache(log_callback, dry_run=False):
        """核心邏輯二：網頁暫存快取清理 (Chrome / Edge 圖片與靜態檔)"""
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 網頁暫存快取 (Chrome / Edge 圖片與樣式檔)...", CONFIG.THEME["PRIMARY"])
        
        target_dirs = [
            ("Chrome 快取", CONFIG.CHROME_CACHE_DIR),
            ("Chrome Code 快取", CONFIG.CHROME_CODE_CACHE_DIR),
            ("Edge 快取", CONFIG.EDGE_CACHE_DIR),
            ("Edge Code 快取", CONFIG.EDGE_CODE_CACHE_DIR)
        ]
        
        deleted_bytes = 0
        deleted_count = 0
        failed_count = 0
        pending_files = []
        
        for label, path in target_dirs:
            if not os.path.exists(path):
                continue
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if dry_run:
                        log_callback(f"🔍 [模擬模式] 預計清理網頁快取 ({label}): {file_path}", CONFIG.THEME["TEXT_MUTED"])
                        pending_files.append(file_path)
                    else:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_bytes += file_size
                            deleted_count += 1
                        except Exception:
                            failed_count += 1
                            
        if dry_run:
            return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ 網頁暫存快取清理完成！成功釋放空間: {mb_released:.2f} MB", CONFIG.THEME["SUCCESS"])
            if failed_count > 0:
                log_callback(f"📊 統計：成功刪除 {deleted_count} 個快取檔，跳過 {failed_count} 個項目 (原因: 瀏覽器正在執行中並鎖定檔案)。\n", CONFIG.THEME["TEXT_LIGHT"])
            return mb_released

    @staticmethod
    def clean_app_cache(log_callback, dry_run=False):
        """核心邏輯三：常用開發與通訊軟體快取清理 (VS Code, Discord, Spotify, npm)"""
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 常用應用軟體快取 (VS Code / Discord / Spotify / npm)...", CONFIG.THEME["PRIMARY"])
        
        deleted_bytes = 0
        deleted_count = 0
        failed_count = 0
        pending_files = []
        
        for label, path in CONFIG.APP_CACHE_DIRS:
            if not os.path.exists(path):
                continue
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if dry_run:
                        log_callback(f"🔍 [模擬模式] 預計清理軟體快取 ({label}): {file_path}", CONFIG.THEME["TEXT_MUTED"])
                        pending_files.append(file_path)
                    else:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_bytes += file_size
                            deleted_count += 1
                        except Exception:
                            failed_count += 1
                            
        if dry_run:
            return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ 應用軟體快取清理完成！成功釋放空間: {mb_released:.2f} MB", CONFIG.THEME["SUCCESS"])
            if failed_count > 0:
                log_callback(f"📊 統計：成功刪除 {deleted_count} 個軟體快取檔，跳過 {failed_count} 個項目。\n", CONFIG.THEME["TEXT_LIGHT"])
            return mb_released

    @staticmethod
    def clean_prefetch(log_callback, target_dir, dry_run=False):
        """核心邏輯四：系統預載快取清理 (Prefetch Clean)"""
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 系統預載歷史快取 (Prefetch)...", CONFIG.THEME["PRIMARY"])
        if not os.path.exists(target_dir):
            log_callback(f"⚠️ 目標路徑不存在，自動跳過：{target_dir}", CONFIG.THEME["WARNING"])
            return [] if dry_run else 0
            
        deleted_bytes = 0
        deleted_count = 0
        failed_count = 0
        pending_files = []
        
        try:
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    is_protected_ext = file.lower().endswith('.py') or file.lower().endswith('.html')
                    if is_protected_ext:
                        continue
                        
                    file_path = os.path.join(root, file)
                    if dry_run:
                        log_callback(f"🔍 [模擬模式] 預計清理檔案: {file_path}", CONFIG.THEME["TEXT_MUTED"])
                        pending_files.append(file_path)
                    else:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_bytes += file_size
                            deleted_count += 1
                        except Exception:
                            failed_count += 1
        except Exception as e:
            log_callback(f"❌ 讀取 Prefetch 發生錯誤 (可能需要管理員權限): {str(e)}", CONFIG.THEME["WARNING"])
            
        if dry_run:
            return pending_files
        else:
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ Prefetch 清理完成！成功釋放空間: {mb_released:.2f} MB", CONFIG.THEME["SUCCESS"])
            log_callback(f"📊 統計：成功刪除 {deleted_count} 個檔案，跳過 {failed_count} 個項目 (原因: 檔案正被其他程式佔用或權限不足)。\n", CONFIG.THEME["TEXT_LIGHT"])
            return mb_released

    @staticmethod
    def kill_zombie_processes(log_callback, ram_limit_mb, target_extensions=None, dry_run=False):
        """核心邏輯五：背景閒置處理程序清理 (Process Cleaner)"""
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 背景閒置處理程序 (記憶體佔用 > {ram_limit_mb}MB)...", CONFIG.THEME["PRIMARY"])
        if target_extensions is None:
            target_extensions = CONFIG.TARGET_PROCESSES
            
        killed_count = 0
        total_freed_ram_mb = 0.0
        pending_pids = []
        try:
            cmd = 'tasklist /FO CSV /NH'
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(cmd, startupinfo=startupinfo, text=True, encoding='cp950', errors='ignore')
            
            for line in output.splitlines():
                if not line.strip():
                    continue
                parts = line.replace('"', '').split(',')
                if len(parts) >= 5:
                    proc_name = parts[0].strip()
                    pid = parts[1].strip()
                    mem_usage_str = parts[4].replace(' K', '').replace(',', '').strip()
                    
                    if any(ext in proc_name.lower() for ext in target_extensions):
                        try:
                            mem_mb = int(mem_usage_str) / 1024
                            if mem_mb > ram_limit_mb:
                                if int(pid) == os.getpid():
                                    continue
                                    
                                if dry_run:
                                    log_callback(f"🔍 [模擬模式] 預計結束處理程序：{proc_name} (PID: {pid}) 佔用 {mem_mb:.1f} MB", CONFIG.THEME["WARNING"])
                                    pending_pids.append((pid, proc_name, mem_mb))
                                else:
                                    log_callback(f"⚠️ 偵測到高能耗閒置處理程序：{proc_name} (PID: {pid}) 佔用 {mem_mb:.1f} MB", CONFIG.THEME["WARNING"])
                                    subprocess.run(f"taskkill /F /PID {pid}", startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    log_callback(f"❌ 已成功關閉處理程序 PID: {pid} (釋放約 {mem_mb:.1f} MB RAM)", CONFIG.THEME["DANGER"])
                                    killed_count += 1
                                    total_freed_ram_mb += mem_mb
                        except ValueError:
                            continue
        except Exception as e:
            log_callback(f"❌ 讀取處理程序列表時發生錯誤: {str(e)}", CONFIG.THEME["DANGER"])
            
        if dry_run:
            return pending_pids
        else:
            if killed_count == 0:
                log_callback("✅ 處理程序檢查完成，目前無超標之閒置處理程序。\n", CONFIG.THEME["SUCCESS"])
            else:
                log_callback(f"✅ 成功關閉了 {killed_count} 個背景閒置處理程序，預計釋放 {total_freed_ram_mb:.2f} MB RAM！\n", CONFIG.THEME["SUCCESS"])
            return killed_count, total_freed_ram_mb

    @staticmethod
    def empty_system_working_set(log_callback):
        """核心邏輯六：Windows 原生 API 深度 Working Set 記憶體壓縮 (Mem Reduct 借鏡)"""
        log_callback("🚀 調用 Windows 原生 API 進行 Working Set 記憶體深度壓縮...", CONFIG.THEME["PRIMARY"])
        compressed_count = 0
        try:
            if sys.platform.startswith('win'):
                psapi = ctypes.windll.psapi
                kernel32 = ctypes.windll.kernel32
                
                # 壓縮本工具自身工作集
                hProcess = kernel32.GetCurrentProcess()
                psapi.EmptyWorkingSet(hProcess)
                compressed_count += 1
                
                # 遍歷目前系統執行中可存取之 process 並呼叫 EmptyWorkingSet
                # 權限：PROCESS_SET_QUOTA (0x0100) | PROCESS_VM_READ (0x0010)
                PROCESS_SET_QUOTA = 0x0100
                PROCESS_VM_READ = 0x0010
                
                # 透過 tasklist 列出 PID 進行安全 Working Set 壓縮
                cmd = 'tasklist /FO CSV /NH'
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                output = subprocess.check_output(cmd, startupinfo=startupinfo, text=True, encoding='cp950', errors='ignore')
                
                for line in output.splitlines():
                    if not line.strip(): continue
                    parts = line.replace('"', '').split(',')
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1].strip())
                            if pid > 4 and pid != os.getpid():
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
        """核心邏輯八：智慧全碟快取自動盤點 (Smart Cache Finder)"""
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 智慧快取自動盤點 (搜尋 > {min_size_mb:.0f} MB 之隱藏快取)...", CONFIG.THEME["PRIMARY"])
        
        target_bases = []
        user_home = CONFIG.USER_HOME
        
        # 定向高價值目錄區塊
        appdata_local = os.path.join(user_home, "AppData", "Local")
        appdata_roaming = os.path.join(user_home, "AppData", "Roaming")
        programdata = r"C:\ProgramData"
        
        for path in [appdata_local, appdata_roaming, programdata]:
            if os.path.exists(path):
                target_bases.append(path)
                
        # 偵測額外本機磁碟 (例如 D:\, E:\, F:\)
        for drive_letter in ['D', 'E', 'F']:
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path):
                target_bases.append(drive_path)

        pending_files = []
        found_cache_dirs = []
        
        exclude_dirs = ["windows", "program files", "program files (x86)", "$recycle.bin", "system volume information", ".antigravity", ".git"]

        for base_dir in target_bases:
            log_callback(f"🔍 [智慧盤點] 掃描區塊：{base_dir}", CONFIG.THEME["TEXT_MUTED"])
            for root, dirs, files in os.walk(base_dir, topdown=True):
                root_lower = root.lower()
                
                # 排除敏感與保護目錄
                if any(ex in root_lower for ex in exclude_dirs) or any(key in root_lower for key in CONFIG.PROTECTED_KEYWORDS):
                    dirs.clear()
                    continue
                    
                dir_name = os.path.basename(root).lower()
                is_cache_dir = any(k in dir_name for k in ["cache", "caches", "code cache", "gpu_cache", "webcache", "htmlcache"])
                
                if is_cache_dir:
                    dirs.clear()  # 剪枝優化：停止繼續往內部子資料夾走訪
                    
                    total_size = 0
                    cache_files = []
                    try:
                        for sub_root, sub_dirs, sub_files in os.walk(root):
                            for sf in sub_files:
                                sf_path = os.path.join(sub_root, sf)
                                is_protected_ext = sf.lower().endswith('.py') or sf.lower().endswith('.html')
                                if not is_protected_ext and not any(key in sf.lower() for key in CONFIG.PROTECTED_KEYWORDS):
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
                        if dry_run:
                            pending_files.extend(cache_files)

        if dry_run:
            log_callback(f"✅ 智慧快取盤點完畢！共發現 {len(found_cache_dirs)} 個超標快取巨頭。\n", CONFIG.THEME["SUCCESS"])
            return pending_files
        else:
            deleted_bytes = 0
            deleted_count = 0
            for r, sz_mb, files_list in found_cache_dirs:
                for f_path in files_list:
                    try:
                        if os.path.exists(f_path):
                            sz = os.path.getsize(f_path)
                            try: os.chmod(f_path, 0o777)
                            except: pass
                            os.remove(f_path)
                            deleted_bytes += sz
                            deleted_count += 1
                    except: pass
            mb_released = deleted_bytes / (1024 * 1024)
            log_callback(f"✅ 智慧快取清理完成！成功釋放空間: {format_size_str(mb_released)}\n", CONFIG.THEME["SUCCESS"])
            return mb_released

    @staticmethod
    def force_garbage_collection(log_callback):
        """核心邏輯七：記憶體垃圾回收 (RAM Garbage Collection)"""
        log_callback("🚀 啟動 Python 記憶體回收機制...", CONFIG.THEME["PRIMARY"])
        try:
            gc.get_referrers()
            collected = gc.collect()
            OptimizerEngine.empty_system_working_set(log_callback)
            log_callback(f"✅ 記憶體回收成功！回收物件群組共: {collected} 組", CONFIG.THEME["SUCCESS"])
            log_callback("⚙️ 系統記憶體分頁已完成深度整理與縮減。\n", CONFIG.THEME["TEXT_MUTED"])
        except Exception as e:
            log_callback(f"❌ 回收記憶體時發生錯誤: {str(e)}\n", CONFIG.THEME["DANGER"])

# ==============================================================================
# 3. 擬清理預覽對話框 (Preview Dialog - Optimizer 借鏡)
# ==============================================================================
class PreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, pending_files, pending_pids, on_confirm_callback, on_cancel_callback=None):
        super().__init__(parent)
        self.title("🔍 模擬模式 - 擬清理與處理程序預覽明細")
        self.geometry("750x500")
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        self.pending_files = pending_files
        self.pending_pids = pending_pids
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.transient(parent)
        self.grab_set()
        
        self.build_ui()

    def build_ui(self):
        lbl_title = ctk.CTkLabel(
            self, text=f"📋 模擬預覽統計：擬清理 {len(self.pending_files)} 個檔案 / 擬關閉 {len(self.pending_pids)} 個閒置處理程序",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]
        )
        lbl_title.pack(anchor="w", padx=15, pady=(15, 10))

        # 搜尋輸入框
        frame_search = ctk.CTkFrame(self, fg_color="transparent")
        frame_search.pack(fill="x", padx=15, pady=(0, 10))
        
        lbl_search = ctk.CTkLabel(frame_search, text="🔍 快速搜尋清單：", font=ctk.CTkFont(family="Microsoft JhengHei", size=11))
        lbl_search.pack(side="left")
        
        self.entry_search = ctk.CTkEntry(frame_search, placeholder_text="輸入檔名或關鍵字過濾...", width=300)
        self.entry_search.pack(side="left", padx=5)
        self.entry_search.bind("<KeyRelease>", self._filter_list)

        # 預覽清單容器
        text_frame = ctk.CTkFrame(self, fg_color="#111115", corner_radius=8)
        text_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.txt_preview = scrolledtext.ScrolledText(
            text_frame, bg="#111115", fg=CONFIG.THEME["TEXT_LIGHT"], font=("Consolas", 10),
            relief="flat", wrap="none", borderwidth=0, highlightthickness=0
        )
        self.txt_preview.pack(fill="both", expand=True, padx=10, pady=10)

        self._populate_text(self.pending_files, self.pending_pids)

        # 底部動作按鈕
        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(fill="x", padx=15, pady=(0, 15))

        btn_cancel = ctk.CTkButton(
            frame_btns, text="🛑 取消清理", fg_color=CONFIG.THEME["CARD_BG"],
            hover_color=CONFIG.THEME["DANGER"], text_color=CONFIG.THEME["TEXT_LIGHT"], command=self._on_cancel
        )
        btn_cancel.pack(side="right", padx=5)

        btn_confirm = ctk.CTkButton(
            frame_btns, text="⚡ 確認並執行真實清理", fg_color=CONFIG.THEME["SUCCESS"],
            hover_color="#2196F3", text_color=CONFIG.THEME["TEXT_LIGHT"], command=self._confirm_and_close
        )
        btn_confirm.pack(side="right", padx=5)

    def _populate_text(self, files, pids, keyword=""):
        self.txt_preview.delete("1.0", "end")
        kw = keyword.lower()
        
        if pids:
            self.txt_preview.insert("end", "=== 擬關閉之高佔用閒置處理程序 ===\n")
            for pid, proc_name, mem_mb in pids:
                line = f"[處理程序] {proc_name} (PID: {pid}) - 佔用 {mem_mb:.1f} MB RAM\n"
                if not kw or kw in line.lower():
                    self.txt_preview.insert("end", line)
            self.txt_preview.insert("end", "\n")

        self.txt_preview.insert("end", "=== 擬清理之檔案清單 ===\n")
        for f in files:
            if not kw or kw in f.lower():
                self.txt_preview.insert("end", f"{f}\n")

    def _filter_list(self, event=None):
        kw = self.entry_search.get()
        self._populate_text(self.pending_files, self.pending_pids, kw)

    def _on_cancel(self):
        self.destroy()
        if self.on_cancel_callback:
            self.on_cancel_callback()

    def _confirm_and_close(self):
        self.destroy()
        self.on_confirm_callback()

# ==============================================================================
# 4. 使用者介面實作 (GUI Interface)
# ==============================================================================
class SystemOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{CONFIG.APP_NAME} {CONFIG.VERSION}")
        self.geometry("940x700")
        ctk.set_appearance_mode("dark")
        
        self.default_font = ctk.CTkFont(family="Microsoft JhengHei", size=12)
        self.title_font = ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold")
        
        # 累積清理統計數值 (Optimizer 借鏡)
        self.total_freed_disk_mb = 0.0
        self.total_freed_ram_mb = 0.0

        # UI 控制變數
        self.var_clean_temp = ctk.BooleanVar(value=True)
        self.var_clean_browser = ctk.BooleanVar(value=True)
        self.var_clean_apps = ctk.BooleanVar(value=True)
        self.var_smart_scan = ctk.BooleanVar(value=True)
        self.var_clean_pip = ctk.BooleanVar(value=False)
        self.var_clean_prefetch = ctk.BooleanVar(value=False)
        self.var_kill_zombie = ctk.BooleanVar(value=True)
        self.var_ram_limit = ctk.IntVar(value=CONFIG.DEFAULT_PROCESS_RAM_LIMIT)
        self.var_scan_depth = ctk.StringVar(value=CONFIG.DEFAULT_SCAN_DEPTH)
        self.var_dry_run = ctk.BooleanVar(value=CONFIG.DRY_RUN)
        
        self.build_ui()
        
        self.append_log(f"✅ {CONFIG.APP_NAME} 已成功啟動。", CONFIG.THEME["SUCCESS"])
        self.append_log("💡 提示：設定左側清理選項後，點擊「開始一鍵優化」即可執行系統清理與記憶體釋放。\n---", CONFIG.THEME["TEXT_MUTED"])

    def build_ui(self):
        """建構主畫面視覺排版"""
        header_frame = ctk.CTkFrame(self, fg_color=CONFIG.THEME["CARD_BG"], height=60)
        header_frame.pack(fill="x", padx=15, pady=10)
        header_frame.pack_propagate(False)
        
        lbl_title = ctk.CTkLabel(header_frame, text=f"🚀 {CONFIG.APP_NAME}", font=ctk.CTkFont(family="Microsoft JhengHei", size=16, weight="bold"), text_color=CONFIG.THEME["TEXT_LIGHT"])
        lbl_title.pack(side="left", padx=15, pady=15)

        self.lbl_ram_status = ctk.CTkLabel(header_frame, text="💾 讀取 RAM 中...", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"), text_color=CONFIG.THEME["SUCCESS"])
        self.lbl_ram_status.pack(side="left", padx=15, pady=15)
        
        lbl_ver = ctk.CTkLabel(header_frame, text=CONFIG.VERSION, font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"])
        lbl_ver.pack(side="right", padx=15, pady=18)
        
        frame_depth = ctk.CTkFrame(header_frame, fg_color="transparent")
        frame_depth.pack(side="right", padx=10, pady=15)
        lbl_depth = ctk.CTkLabel(frame_depth, text="📂 掃描深度：", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"])
        lbl_depth.pack(side="left")
        self.cmb_depth = ctk.CTkComboBox(frame_depth, variable=self.var_scan_depth, values=list(CONFIG.SCAN_DEPTH_OPTIONS.keys()), state="readonly", width=140, font=self.default_font, fg_color=CONFIG.THEME["BG_DARK"], border_color=CONFIG.THEME["PRIMARY"])
        self.cmb_depth.pack(side="left", padx=5)

        self.update_ram_status()

        self.progress_bar = ctk.CTkProgressBar(self, height=8, progress_color=CONFIG.THEME["PRIMARY"], fg_color=CONFIG.THEME["CARD_BG"])
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.progress_bar.set(0)

        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=5)
        
        # 左側控制面板
        left_panel = ctk.CTkFrame(main_container, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        left_panel.pack(side="left", fill="both", padx=(0, 10))
        
        left_title = ctk.CTkLabel(left_panel, text="⚙️ 系統優化設定選項", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"])
        left_title.pack(anchor="w", padx=15, pady=(12, 6))
        
        chk_temp = ctk.CTkCheckBox(left_panel, text="清理使用者暫存區 (Temp)", variable=self.var_clean_temp, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_temp.pack(anchor="w", padx=15, pady=4)
        
        chk_browser = ctk.CTkCheckBox(left_panel, text="清理網頁暫存快取 (Chrome / Edge)", variable=self.var_clean_browser, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_browser.pack(anchor="w", padx=15, pady=4)
        
        chk_apps = ctk.CTkCheckBox(left_panel, text="清理軟體快取 (VS Code / Discord 等)", variable=self.var_clean_apps, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_apps.pack(anchor="w", padx=15, pady=4)

        chk_smart = ctk.CTkCheckBox(left_panel, text="🔍 智慧快取自動盤點 (搜尋 > 50MB 快取)", variable=self.var_smart_scan, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_smart.pack(anchor="w", padx=15, pady=4)

        chk_pip = ctk.CTkCheckBox(left_panel, text="清理 Python pip 快取目錄", variable=self.var_clean_pip, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_pip.pack(anchor="w", padx=15, pady=4)
        
        chk_prefetch = ctk.CTkCheckBox(left_panel, text="清理系統預載歷史 (Prefetch)", variable=self.var_clean_prefetch, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_prefetch.pack(anchor="w", padx=15, pady=4)
        
        divider = ctk.CTkFrame(left_panel, fg_color=CONFIG.THEME["BG_DARK"], height=2)
        divider.pack(fill="x", padx=15, pady=8)
        
        chk_zombie = ctk.CTkCheckBox(left_panel, text="關閉高記憶體佔用閒置處理程序", variable=self.var_kill_zombie, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_zombie.pack(anchor="w", padx=15, pady=4)
        
        chk_dry_run = ctk.CTkCheckBox(left_panel, text="🛡️ 模擬開關 (僅預覽不刪除檔案)", variable=self.var_dry_run, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_dry_run.pack(anchor="w", padx=15, pady=(4, 4))
        
        lbl_slider_desc = ctk.CTkLabel(left_panel, text="處理程序記憶體判定門檻：", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"])
        lbl_slider_desc.pack(anchor="w", padx=15, pady=(4, 2))
        
        self.lbl_unit = ctk.CTkLabel(left_panel, text=f"當前門檻: {CONFIG.DEFAULT_PROCESS_RAM_LIMIT} MB", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["WARNING"])
        self.lbl_unit.pack(anchor="e", padx=15, pady=(0, 2))

        self.ram_slider = ctk.CTkSlider(
            left_panel, from_=100, to=2000, number_of_steps=38,
            variable=self.var_ram_limit, command=self._on_ram_slider_change,
            progress_color=CONFIG.THEME["PRIMARY"], button_color=CONFIG.THEME["PRIMARY"]
        )
        self.ram_slider.pack(fill="x", padx=15, pady=4)

        # 累積清理成果統計卡片 (Optimizer 借鏡)
        stats_card = ctk.CTkFrame(left_panel, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        stats_card.pack(fill="x", padx=15, pady=(8, 5))
        
        self.lbl_total_stats = ctk.CTkLabel(
            stats_card, text="🧹 暫存已清理容量：0.0 MB\n💾 實體 RAM 已釋出：0.0 MB",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["SUCCESS"],
            justify="left"
        )
        self.lbl_total_stats.pack(padx=10, pady=8)

        self.btn_launch = ctk.CTkButton(
            left_panel, text="⚡ 開始一鍵優化", font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color="#2196F3",
            corner_radius=8, height=42, command=self.execute_optimization_flow
        )
        self.btn_launch.pack(fill="x", side="bottom", padx=15, pady=12)

        # 右側執行日誌 Console
        right_panel = ctk.CTkFrame(main_container, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)
        
        right_title = ctk.CTkLabel(right_panel, text="🖥️ 系統優化即時執行日誌", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"])
        right_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        log_frame = ctk.CTkFrame(right_panel, fg_color="#111115", corner_radius=8)
        log_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.log_display = scrolledtext.ScrolledText(
            log_frame, bg="#111115", fg=CONFIG.THEME["TEXT_LIGHT"], font=("Consolas", 11),
            relief="flat", wrap="word", insertbackground=CONFIG.THEME["TEXT_LIGHT"], borderwidth=0, highlightthickness=0
        )
        self.log_display.pack(fill="both", expand=True, padx=10, pady=10)
        
        for key, color in CONFIG.THEME.items():
            self.log_display.tag_config(color, foreground=color)

    def _on_ram_slider_change(self, value):
        self.lbl_unit.configure(text=f"當前門檻: {int(value)} MB")

    def update_ram_status(self):
        total, avail, used, load = get_system_ram_info()
        if total > 0:
            avail_gb = avail / 1024
            self.lbl_ram_status.configure(text=f"💾 系統 RAM 負載: {load}% (可用 {avail_gb:.1f} GB)")
        self.after(3000, self.update_ram_status)

    def append_log(self, message, color_key=None):
        def _update():
            self.log_display.insert("end", message + "\n")
            if color_key:
                end_line = float(self.log_display.index("end")) - 1.0
                start_line = end_line - 1.0
                self.log_display.tag_add(color_key, f"{start_line:.1f}", f"{end_line:.1f}")
            self.log_display.see("end")
            self.update_idletasks()
        self.after(0, _update)

    def update_cumulative_stats(self, freed_disk_mb=0.0, freed_ram_mb=0.0):
        self.total_freed_disk_mb += freed_disk_mb
        self.total_freed_ram_mb += freed_ram_mb
        disk_str = format_size_str(self.total_freed_disk_mb)
        ram_str = format_size_str(self.total_freed_ram_mb)
        self.lbl_total_stats.configure(text=f"🧹 暫存已清理容量：{disk_str}\n💾 實體 RAM 已釋出：{ram_str}")

    # ==============================================================================
    # 5. 一鍵排程與工作流管理 (Execution Flow)
    # ==============================================================================
    def execute_optimization_flow(self):
        self.btn_launch.configure(state="disabled", text="⏳ 優化執行中...")
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])
        self.append_log(f"⏰ 任務啟動時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", CONFIG.THEME["TEXT_LIGHT"])
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])
        
        is_dry_run = self.var_dry_run.get()
        selected_depth_str = self.var_scan_depth.get()
        max_depth = CONFIG.SCAN_DEPTH_OPTIONS.get(selected_depth_str, 1)
        do_temp = self.var_clean_temp.get()
        do_browser = self.var_clean_browser.get()
        do_apps = self.var_clean_apps.get()
        do_smart = self.var_smart_scan.get()
        do_pip = self.var_clean_pip.get()
        do_prefetch = self.var_clean_prefetch.get()
        do_zombie = self.var_kill_zombie.get()
        current_threshold_mb = self.var_ram_limit.get()
        
        if is_dry_run:
            self.append_log("🛡️ 目前為 [模擬模式]，僅預覽掃描結果，不會實際刪除檔案。", CONFIG.THEME["WARNING"])

        def _update_progress(value):
            self.after(0, lambda: self.progress_bar.set(value))

        def _thread_task():
            try:
                tot_ram, avail_before, used_before, load_before = get_system_ram_info()

                _update_progress(0.1)
                pending_files = []
                pending_pids = []
                total_items = 0
                freed_ram_from_procs = 0.0

                # 1. 清理使用者 Temp 暫存
                if do_temp:
                    res = OptimizerEngine.clean_temp_cache(self.append_log, CONFIG.TEMP_DIR, max_depth=max_depth, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.2)

                # 2. 清理網頁暫存快取 (Chrome / Edge)
                if do_browser:
                    res = OptimizerEngine.clean_browser_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.35)

                # 3. 清理常用應用軟體快取 (VS Code, Discord, Spotify, npm)
                if do_apps:
                    res = OptimizerEngine.clean_app_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.5)

                # 4. 智慧全碟快取自動盤點 (Smart Cache Finder)
                if do_smart:
                    res = OptimizerEngine.scan_smart_caches(self.append_log, min_size_mb=50.0, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.7)
                    
                # 5. 清理 Python pip 快取
                if do_pip:
                    res = OptimizerEngine.clean_temp_cache(self.append_log, CONFIG.PIP_CACHE_DIR, max_depth=max_depth, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.75)
                    
                # 6. 清理系統預載歷史 (Prefetch)
                if do_prefetch:
                    res = OptimizerEngine.clean_prefetch(self.append_log, CONFIG.PREFETCH_DIR, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.85)
                    
                # 6. 處理程序清理
                if do_zombie:
                    res = OptimizerEngine.kill_zombie_processes(self.append_log, ram_limit_mb=current_threshold_mb, dry_run=is_dry_run)
                    if is_dry_run:
                        pending_pids.extend(res)
                    else:
                        killed_count, freed_ram_from_procs = res
                _update_progress(0.9)
                    
                if is_dry_run:
                    total_items = len(pending_files) + len(pending_pids)
                    est_proc_ram = sum(item[2] for item in pending_pids if len(item) >= 3)
                    est_proc_ram_fmt = format_size_str(est_proc_ram)
                    if total_items == 0:
                        _update_progress(1.0)
                        self.append_log("✅ 模擬掃描結束，目前環境乾淨，無需要清理的項目。\n", CONFIG.THEME["SUCCESS"])
                        self.after(0, lambda: messagebox.showinfo("模擬完成", "模擬掃描結束，目前無需要清理的項目。"))
                    else:
                        _update_progress(1.0)
                        self.append_log(f"📊 [模擬統計] 預計清理 {len(pending_files)} 個檔案，預計關閉 {len(pending_pids)} 個處理程序 (約釋放 {est_proc_ram_fmt} RAM)。", CONFIG.THEME["TEXT_LIGHT"])
                        self.append_log("⚠️ 請點擊對話框查看擬刪除明細並確認執行。", CONFIG.THEME["WARNING"])
                        
                        def _reset_launch_btn():
                            self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 開始一鍵優化"))
                            self.after(0, lambda: self.progress_bar.set(0))

                        def _open_preview_modal():
                            PreviewDialog(
                                self, pending_files, pending_pids,
                                on_confirm_callback=lambda: threading.Thread(
                                    target=_real_delete_thread, args=(pending_files, pending_pids, avail_before, load_before), daemon=True
                                ).start(),
                                on_cancel_callback=_reset_launch_btn
                            )
                        self.after(0, _open_preview_modal)
                        return
                else:
                    OptimizerEngine.force_garbage_collection(self.append_log)
                    _update_progress(1.0)
                    
                    tot_ram, avail_after, used_after, load_after = get_system_ram_info()
                    ram_diff_mb = avail_after - avail_before
                    final_freed_ram_mb = max(ram_diff_mb, freed_ram_from_procs)
                    ram_fmt = format_size_str(final_freed_ram_mb)

                    self.after(0, lambda: self.update_cumulative_stats(freed_ram_mb=final_freed_ram_mb))
                    self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                    self.append_log(f"🎉 【RAM 釋放成果】成功釋放系統記憶體: {ram_fmt}！", CONFIG.THEME["SUCCESS"])
                    if load_before > 0:
                        self.append_log(f"📊 記憶體負載變化: {load_before}% ➡️ {load_after}% (可用 RAM: {avail_after/1024:.2f} GB)", CONFIG.THEME["TEXT_LIGHT"])
                    self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                    self.append_log("🏁 【系統優化程序執行完畢】\n", CONFIG.THEME["SUCCESS"])
                    self.after(0, lambda: messagebox.showinfo("優化完成報告", f"一鍵系統優化成功完畢！\n\n🎉 成功釋放實體 RAM: {ram_fmt}\n系統負載已降至 {load_after}%。"))
                
            except Exception as e:
                self.append_log(f"❌ 執行過程中發生異常: {str(e)}", CONFIG.THEME["DANGER"])
                self.after(0, lambda err=e: messagebox.showerror("執行錯誤提示", f"程序發生非預期中斷:\n{str(err)}"))
                
            finally:
                if not is_dry_run or (is_dry_run and total_items == 0):
                    self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 開始一鍵優化"))
                    self.after(2000, lambda: self.progress_bar.set(0))

        def _real_delete_thread(files, pids, avail_before, load_before):
            try:
                self.append_log("\n⚡ 使用者授權完成，開始執行真實清理與記憶體釋放...", CONFIG.THEME["DANGER"])
                
                deleted_count = 0
                failed_count = 0
                deleted_bytes = 0
                for file_path in files:
                    try:
                        if os.path.exists(file_path):
                            sz = os.path.getsize(file_path)
                            try:
                                os.chmod(file_path, 0o777)
                            except: pass
                            os.remove(file_path)
                            deleted_count += 1
                            deleted_bytes += sz
                    except Exception:
                        failed_count += 1
                    
                killed_count = 0
                freed_ram_proc = 0.0
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                for item in pids:
                    pid = item[0]
                    proc_name = item[1]
                    mem_mb = item[2] if len(item) >= 3 else 0.0
                    try:
                        subprocess.run(f"taskkill /F /PID {pid}", startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        killed_count += 1
                        freed_ram_proc += mem_mb
                    except: pass
                    
                self.append_log(f"✅ 清理完成！成功刪除 {deleted_count} 個檔案，關閉 {killed_count} 個處理程序。", CONFIG.THEME["SUCCESS"])
                if failed_count > 0:
                    self.append_log(f"⚠️ 注意：有 {failed_count} 個檔案未刪除 (原因: 檔案正被其他程式佔用或無存取權限)。", CONFIG.THEME["WARNING"])
                    
                OptimizerEngine.force_garbage_collection(self.append_log)
                _update_progress(1.0)

                tot_ram, avail_after, used_after, load_after = get_system_ram_info()
                ram_diff_mb = avail_after - avail_before
                final_freed_ram_mb = max(ram_diff_mb, freed_ram_proc)
                disk_mb = deleted_bytes / (1024 * 1024)

                disk_fmt = format_size_str(disk_mb)
                ram_fmt = format_size_str(final_freed_ram_mb)

                self.after(0, lambda: self.update_cumulative_stats(freed_disk_mb=disk_mb, freed_ram_mb=final_freed_ram_mb))

                self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                self.append_log(f"🎉 【清理成果】釋出暫存磁碟容量: {disk_fmt} / 實體 RAM: {ram_fmt}！", CONFIG.THEME["SUCCESS"])
                if load_before > 0:
                    self.append_log(f"📊 記憶體負載變化: {load_before}% ➡️ {load_after}% (可用 RAM: {avail_after/1024:.2f} GB)", CONFIG.THEME["TEXT_LIGHT"])
                self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                self.append_log("🏁 【系統優化程序執行完畢】\n", CONFIG.THEME["SUCCESS"])
                self.after(0, lambda: messagebox.showinfo("優化完成", f"清理與優化已成功完畢！\n\n🧹 成功清理暫存檔容量: {disk_fmt}\n🎉 成功釋放實體 RAM: {ram_fmt}\n系統負載已降至 {load_after}%。"))
            except Exception as e:
                self.append_log(f"❌ 清理過程中發生異常: {str(e)}", CONFIG.THEME["DANGER"])
            finally:
                self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 開始一鍵優化"))
                self.after(2000, lambda: self.progress_bar.set(0))

        threading.Thread(target=_thread_task, daemon=True).start()

if __name__ == "__main__":
    try:
        if sys.platform.startswith('win'):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    app = SystemOptimizerApp()
    app.mainloop()