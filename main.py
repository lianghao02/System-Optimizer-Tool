#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool) - v2.6 UI 美化全能版
主要功能：
  1. 快取與記憶體優化：清理第一類/第二類系統快取、網頁快取、顯卡著色器快取、Win32 Working Set 原生記憶體壓縮。
  2. 開機加速與工作排程管理：自動盤點 Windows Registry (Run/RunApproved)、Startup 資料夾與 Windows 工作排程器 (Schtasks) 所有啟動項目；
     提供一鍵「🚫 停用 / 關閉啟動」與「✅ 復原 / 開啟啟動」動態開關控制，同時保留自訂腳本延遲啟動。
  3. 軟體徹底卸載 (Geek 版)：讀取本機安裝軟體清單、顯示軟體圖示/安裝日期/估算容量、識別系統必備元件、
     支援快速關鍵字搜尋與「隱藏系統必備元件」開關、官方卸載呼叫、卸載後 AppData / ProgramData 深層殘留資料夾掃蕩。
  4. 設定與保護白名單：系統核心與關鍵檔案白名單防護管理。
相依套件：Python 3 標準庫 (tkinter, os, sys, shutil, subprocess, gc, ctypes, json, winreg)
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
import json
import customtkinter as ctk
from tkinter import messagebox, scrolledtext

if sys.platform.startswith('win'):
    import winreg

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
# 1. 全域系統配置與路徑設定 (CONFIG)
# ==============================================================================
class CONFIG:
    APP_NAME = "本機系統快取清理與記憶體優化工具"
    VERSION = "v2.6 (UI 美化全能版)"
    
    DEFAULT_CPU_THRESHOLD = 80.0       # CPU 警告閾值 (%)
    DEFAULT_PROCESS_RAM_LIMIT = 500    # 閒置處理程序記憶體判定門檻 (MB)
    TARGET_PROCESSES = ["python.exe", "node.exe"]  # 預設掃描的高資源佔用處理程序
    
    USER_HOME = os.path.expanduser("~")
    TEMP_DIR = os.path.join(USER_HOME, "AppData", "Local", "Temp")
    PREFETCH_DIR = r"C:\Windows\Prefetch"
    CUSTOM_SCRIPT_JSON = os.path.join(USER_HOME, "AppData", "Local", "SystemOptimizerTool", "custom_scripts.json")
    STARTUP_BACKUP_JSON = os.path.join(USER_HOME, "AppData", "Local", "SystemOptimizerTool", "startup_backup.json")

    # 第一類：完全無害 / 無感清理標的路徑
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

    # 第二類：輕微影響 / 短暫延遲清理標的路徑
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
        "TEXT_MUTED": "#6B6B8A",
        "PRIMARY": "#5B7BFE",
        "PRIMARY_HOVER": "#4A68E8",
        "SUCCESS": "#2ECC8A",
        "SUCCESS_HOVER": "#25B87A",
        "WARNING": "#F0A500",
        "DANGER": "#FF4757",
        "DANGER_HOVER": "#E03050",
        "ACCENT": "#A78BFA"
    }
    
    PROTECTED_KEYWORDS = [
        ".git", ".antigravity", "rules.md", "main.py", 
        "explorer.exe", "taskmgr.exe", "svchost.exe"
    ]

# ==============================================================================
# 2. 快取與記憶體清理引擎 (Optimizer Engine)
# ==============================================================================
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
        mode_text = "[模擬掃描]" if dry_run else "開始掃描"
        log_callback(f"🚀 {mode_text} 背景閒置處理程序 (記憶體佔用 > {ram_limit_mb}MB)...", CONFIG.THEME["PRIMARY"])
        if target_extensions is None: target_extensions = CONFIG.TARGET_PROCESSES
        killed_count = 0; total_freed_ram_mb = 0.0; pending_pids = []
        try:
            cmd = 'tasklist /FO CSV /NH'
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(cmd, startupinfo=startupinfo, text=True, encoding='cp950', errors='ignore')
            for line in output.splitlines():
                if not line.strip(): continue
                parts = line.replace('"', '').split(',')
                if len(parts) >= 5:
                    proc_name = parts[0].strip(); pid = parts[1].strip()
                    mem_usage_str = parts[4].replace(' K', '').replace(',', '').strip()
                    if any(ext in proc_name.lower() for ext in target_extensions):
                        try:
                            mem_mb = int(mem_usage_str) / 1024
                            if mem_mb > ram_limit_mb:
                                if int(pid) == os.getpid(): continue
                                if dry_run:
                                    log_callback(f"🔍 [模擬模式] 預計結束處理程序：{proc_name} (PID: {pid}) 佔用 {mem_mb:.1f} MB", CONFIG.THEME["WARNING"])
                                    pending_pids.append((pid, proc_name, mem_mb))
                                else:
                                    log_callback(f"⚠️ 偵測到高能耗閒置處理程序：{proc_name} (PID: {pid}) 佔用 {mem_mb:.1f} MB", CONFIG.THEME["WARNING"])
                                    subprocess.run(f"taskkill /F /PID {pid}", startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    log_callback(f"❌ 已成功關閉處理程序 PID: {pid} (釋放約 {mem_mb:.1f} MB RAM)", CONFIG.THEME["DANGER"])
                                    killed_count += 1
                                    total_freed_ram_mb += mem_mb
                        except ValueError: continue
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

# ==============================================================================
# 3. 開機加速與工作排程管理引擎 (Boot & Startup Engine)
# ==============================================================================
class BootOptimizerEngine:
    KNOWN_STARTUP_DB = [
        ("msedge.exe", "Microsoft Edge 網頁瀏覽器", "開機在背景預載 Microsoft Edge 瀏覽器分頁與工作階段"),
        ("microsoftedgeautolaunch", "Microsoft Edge 網頁瀏覽器", "開機在背景預載 Microsoft Edge 瀏覽器分頁與工作階段"),
        ("qshelper.exe", "Lenovo Vantage 電池與系統工具", "Lenovo 聯想筆電之電池計量器與硬體服務輔助模組"),
        ("canvaautolaunch", "Canva 線上設計軟體", "Canva 設計軟體之開機自動檢查更新與快取代理程式"),
        ("linelauncher.exe", "LINE 即時通訊軟體", "LINE 通訊軟體 (開機自動啟動並登入接收好友訊息)"),
        ("onedrive.exe", "Microsoft OneDrive 雲端硬碟", "微軟雲端檔案同步服務 (開機自動背景同步資料夾)"),
        ("steam.exe", "Steam 遊戲平台", "Valve Steam 遊戲客戶端 (開機自動登入與社群通訊)"),
        ("epicgameslauncher.exe", "Epic Games 遊戲平台", "Epic Games 商店客戶端 (開機背景檢查遊戲更新)"),
        ("discord.exe", "Discord 社群通訊軟體", "Discord 語音與文字社群軟體 (開機自動啟動)"),
        ("spotify.exe", "Spotify 音樂播放器", "Spotify 音樂串流客戶端 (開機自動登入與背景播放器)"),
    ]

    @staticmethod
    def get_last_boot_time_str():
        try:
            if sys.platform.startswith('win'):
                uptime_ms = ctypes.windll.kernel32.GetTickCount64()
                uptime_sec = uptime_ms / 1000.0
                hours = int(uptime_sec // 3600)
                minutes = int((uptime_sec % 3600) // 60)
                seconds = int(uptime_sec % 60)
                return f"系統已連續運行：{hours} 小時 {minutes} 分 {seconds} 秒"
        except Exception: pass
        return "系統運行時間正常"

    @staticmethod
    def resolve_friendly_name_and_description(raw_name, command_str):
        raw_name_lower = raw_name.lower()
        cmd_lower = command_str.lower()

        for key, friendly_name, desc in BootOptimizerEngine.KNOWN_STARTUP_DB:
            if key in raw_name_lower or key in cmd_lower:
                return friendly_name, desc

        clean_path = ""
        if '.exe' in cmd_lower:
            parts = command_str.split('.exe')
            clean_path = (parts[0] + '.exe').replace('"', '').strip()

        if clean_path and os.path.exists(clean_path):
            try:
                size = ctypes.windll.version.GetFileVersionInfoSizeW(clean_path, None)
                if size > 0:
                    res = ctypes.create_string_buffer(size)
                    ctypes.windll.version.GetFileVersionInfoW(clean_path, 0, size, res)
                    lptr = ctypes.c_void_p(); lsize = ctypes.c_uint()

                    for sub in [r"\StringFileInfo\040404b0\ProductName", r"\StringFileInfo\040904b0\ProductName", r"\StringFileInfo\000004b0\ProductName"]:
                        if ctypes.windll.version.VerQueryValueW(res, sub, ctypes.byref(lptr), ctypes.byref(lsize)) and lsize.value > 0:
                            p_name = ctypes.wstring_at(lptr)
                            if p_name and len(p_name.strip()) > 1:
                                return p_name.strip(), f"自動跟隨系統開機啟動軟體：{p_name.strip()}"

                    for sub in [r"\StringFileInfo\040404b0\FileDescription", r"\StringFileInfo\040904b0\FileDescription", r"\StringFileInfo\000004b0\FileDescription"]:
                        if ctypes.windll.version.VerQueryValueW(res, sub, ctypes.byref(lptr), ctypes.byref(lsize)) and lsize.value > 0:
                            f_desc = ctypes.wstring_at(lptr)
                            if f_desc and len(f_desc.strip()) > 1:
                                return f_desc.strip(), f"開機自動載入背景服務：{f_desc.strip()}"
            except Exception: pass

        basename = os.path.basename(clean_path) if clean_path else raw_name
        name_no_ext = os.path.splitext(basename)[0]
        return f"應用程式 ({name_no_ext})", f"開機跟隨 Windows 啟動之程式：{name_no_ext}"

    @staticmethod
    def open_startup_folder(scope="user"):
        """開啟本機 Startup 開機啟動資料夾 (shell:startup 或 shell:common startup)"""
        try:
            if scope == "common":
                folder = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"
            else:
                folder = os.path.join(CONFIG.USER_HOME, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            
            os.startfile(folder)
            return True, f"已成功開啟 [{scope}] 啟動資料夾: {folder}"
        except Exception as e:
            return False, f"開啟資料夾失敗: {str(e)}"

    @staticmethod
    def is_driver_or_system_item(raw_name, cmd_str):
        """辨識是否為核心系統、顯示卡、音效卡或硬體驅動關鍵項目 (NVIDIA, Realtek, Intel, Defender 等)"""
        driver_keys = [
            "nvidia", "realtek", "intel", "amd", "radeon", "asus", "msi", 
            "lenovo", "dell", "hp", "synaptics", "logitech", "defend", "security",
            "windows", "system32", "svchost", "ctfmon"
        ]
        combined = (str(raw_name) + " " + str(cmd_str)).lower()
        return any(k in combined for k in driver_keys)

    @staticmethod
    def backup_and_delete_shortcut(item):
        """安全將 Startup 資料夾之捷徑檔 (.lnk) 移至 LocalAppData 安全備份垃圾桶"""
        try:
            src = item["command"]
            if not os.path.exists(src):
                return False, "目標捷徑檔案不存在或已被刪除"
            
            backup_dir = os.path.join(CONFIG.USER_HOME, "AppData", "Local", "SystemOptimizerTool", "backup_shortcuts")
            os.makedirs(backup_dir, exist_ok=True)
            
            file_name = os.path.basename(src)
            dst = os.path.join(backup_dir, file_name)
            
            if os.path.exists(dst):
                try: os.remove(dst)
                except: pass
                
            shutil.move(src, dst)
            return True, f"已安全將捷徑 [{item['friendly_name']}] 移至備份垃圾桶！"
        except Exception as e:
            return False, f"備份刪除捷徑失敗: {str(e)}"

    @staticmethod
    def restore_shortcut_from_backup(file_name, target_scope="user"):
        """從備份垃圾桶復原 Shortcut 捷徑"""
        try:
            backup_dir = os.path.join(CONFIG.USER_HOME, "AppData", "Local", "SystemOptimizerTool", "backup_shortcuts")
            src = os.path.join(backup_dir, file_name)
            if not os.path.exists(src):
                return False, "備份捷徑檔案不存在"
            
            if target_scope == "common":
                dst_dir = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"
            else:
                dst_dir = os.path.join(CONFIG.USER_HOME, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, file_name)
            shutil.move(src, dst)
            return True, f"已將捷徑 [{file_name}] 成功復原至啟動資料夾！"
        except Exception as e:
            return False, f"復原捷徑失敗: {str(e)}"

    @staticmethod
    def get_system_startup_programs():
        """盤點雙層 Registry (Run/RunDisabled)、個人/全機 Startup 資料夾與 Windows 工作排程器 (Schtasks) 項目"""
        items = []
        system_high_impact = ["steam", "epic", "discord", "spotify", "onedrive", "chrome", "edge", "update", "lenovo"]

        # 1. 讀取 Registry (包含個人與本機系統鍵)
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "當前使用者 Registry", True),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunDisabled", "當前使用者 Registry (已停用)", False),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "全機系統 Registry", True),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunDisabled", "全機系統 Registry (已停用)", False)
        ]

        for hkey, subkey, loc_name, is_enabled in reg_paths:
            try:
                key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                count = winreg.QueryInfoKey(key)[1]
                for i in range(count):
                    try:
                        name, val, _type = winreg.EnumValue(key, i)
                        val_str = str(val).strip()
                        friendly_name, friendly_desc = BootOptimizerEngine.resolve_friendly_name_and_description(name, val_str)
                        impact = "🔴 高影響" if any(k in name.lower() or k in val_str.lower() for k in system_high_impact) else "🟡 中影響"
                        is_sys_driver = BootOptimizerEngine.is_driver_or_system_item(name, val_str)
                        items.append({
                            "type": "registry",
                            "raw_name": name,
                            "friendly_name": friendly_name,
                            "description": friendly_desc,
                            "command": val_str,
                            "location": loc_name,
                            "impact": impact,
                            "enabled": is_enabled,
                            "is_sys_driver": is_sys_driver,
                            "hkey": hkey,
                            "subkey": subkey
                        })
                    except: pass
                winreg.CloseKey(key)
            except: pass

        # 2. 讀取雙層 Startup 資料夾 (個人與全機所有使用者)
        startup_dirs = [
            ("個人 Startup 資料夾 (shell:startup)", os.path.join(CONFIG.USER_HOME, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup"), "user"),
            ("全機共用 Startup 資料夾 (shell:common startup)", r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp", "common")
        ]

        for loc_name, st_path, scope in startup_dirs:
            if os.path.exists(st_path):
                try:
                    for f in os.listdir(st_path):
                        if f.lower().endswith('.lnk') or f.lower().endswith('.exe') or f.lower().endswith('.bat') or f.lower().endswith('.disabled'):
                            full_p = os.path.join(st_path, f)
                            is_enabled = not f.lower().endswith('.disabled')
                            clean_fn = f.replace('.disabled', '')
                            friendly_name, friendly_desc = BootOptimizerEngine.resolve_friendly_name_and_description(clean_fn, full_p)
                            impact = "🔴 高影響" if any(k in f.lower() for k in system_high_impact) else "🟢 低影響"
                            is_sys_driver = BootOptimizerEngine.is_driver_or_system_item(f, full_p)
                            items.append({
                                "type": "file",
                                "raw_name": f,
                                "friendly_name": friendly_name,
                                "description": friendly_desc,
                                "command": full_p,
                                "location": loc_name,
                                "scope": scope,
                                "impact": impact,
                                "is_sys_driver": is_sys_driver,
                                "enabled": is_enabled
                            })
                except: pass

        # 3. 讀取 Windows 工作排程器 (schtasks)
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output('schtasks /Query /FO CSV /V', startupinfo=startupinfo, text=True, encoding='cp950', errors='ignore')
            lines = output.splitlines()
            if len(lines) > 1:
                header = [h.replace('"', '').strip() for h in lines[0].split(',')]
                for line in lines[1:]:
                    parts = [p.replace('"', '').strip() for p in line.split(',')]
                    if len(parts) == len(header):
                        row = dict(zip(header, parts))
                        task_name = row.get("工作名稱", "").strip()
                        status = row.get("狀態", "").strip()
                        cmd = row.get("要執行的工作", "").strip()
                        
                        if task_name and not task_name.startswith("\\Microsoft\\Windows\\"):
                            friendly_name, friendly_desc = BootOptimizerEngine.resolve_friendly_name_and_description(os.path.basename(task_name), cmd)
                            is_enabled = (status.lower() != "disabled" and status != "已停用")
                            is_sys_driver = BootOptimizerEngine.is_driver_or_system_item(task_name, cmd)
                            items.append({
                                "type": "task",
                                "raw_name": task_name,
                                "friendly_name": friendly_name,
                                "description": f"[工作排程器] {friendly_desc}",
                                "command": cmd if cmd else "工作排程觸發指令",
                                "location": "Windows 工作排程器",
                                "impact": "🟡 中影響",
                                "is_sys_driver": is_sys_driver,
                                "enabled": is_enabled
                            })
        except: pass

        return items

    @staticmethod
    def toggle_startup_item_state(item):
        """實作一鍵「關閉/停用」與「開啟/復原」系統開機啟動與工作排程器狀態"""
        try:
            curr_enabled = item["enabled"]
            item_type = item["type"]

            if item_type == "registry":
                hkey = item["hkey"]
                run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
                disabled_key = r"Software\Microsoft\Windows\CurrentVersion\RunDisabled"

                if curr_enabled:
                    # 從 Run 刪除並寫入 RunDisabled
                    try:
                        k_run = winreg.OpenKey(hkey, run_key, 0, winreg.KEY_ALL_ACCESS)
                        winreg.DeleteValue(k_run, item["raw_name"])
                        winreg.CloseKey(k_run)
                    except: pass

                    k_dis = winreg.CreateKey(hkey, disabled_key)
                    winreg.SetValueEx(k_dis, item["raw_name"], 0, winreg.REG_SZ, item["command"])
                    winreg.CloseKey(k_dis)
                    return True, f"已成功關閉開機啟動項：[{item['friendly_name']}]"
                else:
                    # 從 RunDisabled 刪除並寫入 Run
                    try:
                        k_dis = winreg.OpenKey(hkey, disabled_key, 0, winreg.KEY_ALL_ACCESS)
                        winreg.DeleteValue(k_dis, item["raw_name"])
                        winreg.CloseKey(k_dis)
                    except: pass

                    k_run = winreg.CreateKey(hkey, run_key)
                    winreg.SetValueEx(k_run, item["raw_name"], 0, winreg.REG_SZ, item["command"])
                    winreg.CloseKey(k_run)
                    return True, f"已成功開啟/復原開機啟動項：[{item['friendly_name']}]"

            elif item_type == "file":
                src = item["command"]
                if curr_enabled:
                    dst = src + ".disabled"
                else:
                    dst = src.replace(".disabled", "")
                if os.path.exists(src):
                    os.rename(src, dst)
                    act_str = "關閉" if curr_enabled else "開啟"
                    return True, f"已成功{act_str}啟動資料夾項目：[{item['friendly_name']}]"

            elif item_type == "task":
                task_tn = item["raw_name"]
                action_flag = "/Disable" if curr_enabled else "/Enable"
                cmd = f'schtasks /Change /TN "{task_tn}" {action_flag}'
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                res = subprocess.run(cmd, startupinfo=startupinfo, capture_output=True, text=True)
                if res.returncode == 0:
                    act_str = "關閉" if curr_enabled else "開啟"
                    return True, f"已成功{act_str}工作排程器任務：[{item['friendly_name']}]"
                else:
                    return False, f"修改工作排程失敗 (權限不足): {res.stderr.strip()}"
        except Exception as e:
            return False, f"執行失敗: {str(e)}"
        return False, "未知錯誤"

    @staticmethod
    def load_custom_scripts():
        try:
            if os.path.exists(CONFIG.CUSTOM_SCRIPT_JSON):
                with open(CONFIG.CUSTOM_SCRIPT_JSON, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception: pass
        return []

    @staticmethod
    def save_custom_scripts(scripts_list):
        try:
            os.makedirs(os.path.dirname(CONFIG.CUSTOM_SCRIPT_JSON), exist_ok=True)
            with open(CONFIG.CUSTOM_SCRIPT_JSON, 'w', encoding='utf-8') as f:
                json.dump(scripts_list, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def test_run_script(file_path, args_str=""):
        try:
            if file_path.endswith('.py'):
                cmd = f'python "{file_path}" {args_str}'
            else:
                cmd = f'"{file_path}" {args_str}'
            subprocess.Popen(cmd, shell=True)
            return True, "腳本已成功在背景啟動！"
        except Exception as e:
            return False, str(e)

# ==============================================================================
# 4. 軟體徹底卸載與殘留清理引擎 (Geek Uninstaller Engine)
# ==============================================================================
class UninstallerEngine:
    @staticmethod
    def get_installed_software_list():
        software_list = []
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        seen_names = set()
        system_keywords = [
            "visual c++", "directx", "redistributable", "windows driver", 
            ".net framework", ".net desktop runtime", "windows sdk", 
            "system component", "update for windows", "kb", "msvc",
            "opencl", "vulkan", "runtime"
        ]

        for hkey, subkey in reg_paths:
            try:
                key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    try:
                        sub_name = winreg.EnumKey(key, i)
                        sub_key = winreg.OpenKey(key, sub_name)
                        
                        try: display_name = winreg.QueryValueEx(sub_key, "DisplayName")[0].strip()
                        except: display_name = ""
                        
                        try: uninstall_cmd = winreg.QueryValueEx(sub_key, "UninstallString")[0].strip()
                        except: uninstall_cmd = ""
                        
                        if not display_name or not uninstall_cmd:
                            winreg.CloseKey(sub_key)
                            continue

                        try: publisher = winreg.QueryValueEx(sub_key, "Publisher")[0].strip()
                        except: publisher = "未知發行商"

                        try: raw_date = str(winreg.QueryValueEx(sub_key, "InstallDate")[0]).strip()
                        except: raw_date = ""

                        if len(raw_date) == 8 and raw_date.isdigit():
                            formatted_date = f"{raw_date[:4]}/{raw_date[4:6]}/{raw_date[6:]}"
                        else:
                            formatted_date = raw_date if raw_date else "日期未知"

                        try:
                            size_kb = winreg.QueryValueEx(sub_key, "EstimatedSize")[0]
                            size_mb = size_kb / 1024.0
                            size_str = format_size_str(size_mb)
                        except:
                            size_mb = 0.0
                            size_str = "大小未知"

                        try: sys_comp_flag = winreg.QueryValueEx(sub_key, "SystemComponent")[0]
                        except: sys_comp_flag = 0

                        is_system = (sys_comp_flag == 1) or any(k in display_name.lower() for k in system_keywords)

                        winreg.CloseKey(sub_key)

                        if display_name not in seen_names:
                            seen_names.add(display_name)
                            software_list.append({
                                "name": display_name,
                                "publisher": publisher,
                                "uninstall_cmd": uninstall_cmd,
                                "install_date": formatted_date,
                                "size_mb": size_mb,
                                "size_str": size_str,
                                "is_system": is_system
                            })
                    except: pass
                winreg.CloseKey(key)
            except: pass

        return sorted(software_list, key=lambda x: (x["is_system"], x["name"].lower()))

    @staticmethod
    def scan_software_residuals(software_name):
        user_home = CONFIG.USER_HOME
        target_bases = [
            os.path.join(user_home, "AppData", "Local"),
            os.path.join(user_home, "AppData", "Roaming"),
            r"C:\ProgramData"
        ]
        residuals = []
        name_clean = software_name.split()[0].lower()
        if len(name_clean) <= 2: return residuals

        for base in target_bases:
            if os.path.exists(base):
                try:
                    for item in os.listdir(base):
                        if name_clean in item.lower():
                            full_path = os.path.join(base, item)
                            if os.path.isdir(full_path):
                                total_sz = 0
                                for r, d, files in os.walk(full_path):
                                    for f in files:
                                        try: total_sz += os.path.getsize(os.path.join(r, f))
                                        except: pass
                                residuals.append((full_path, total_sz / (1024 * 1024)))
                except: pass
        return residuals

# ==============================================================================
# 5. 對話框實作 (Dialog Modals)
# ==============================================================================
class PreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, pending_files, pending_pids, on_confirm_callback, on_cancel_callback=None):
        super().__init__(parent)
        self.title("🔍 模擬測試模式 - 擬清理檔案與處理程序明細")
        self.geometry("780x520")
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        self.pending_files = pending_files
        self.pending_pids = pending_pids
        self.transient(parent)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        lbl_title = ctk.CTkLabel(
            self, text=f"📋 模擬預覽統計：擬清理 {len(self.pending_files)} 個檔案 / 擬關閉 {len(self.pending_pids)} 個閒置處理程序",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]
        )
        lbl_title.pack(anchor="w", padx=15, pady=(15, 10))

        frame_search = ctk.CTkFrame(self, fg_color="transparent")
        frame_search.pack(fill="x", padx=15, pady=(0, 10))
        lbl_search = ctk.CTkLabel(frame_search, text="🔍 快速搜尋清單：", font=ctk.CTkFont(family="Microsoft JhengHei", size=11))
        lbl_search.pack(side="left")
        self.entry_search = ctk.CTkEntry(frame_search, placeholder_text="輸入檔名或關鍵字過濾...", width=320)
        self.entry_search.pack(side="left", padx=5)
        self.entry_search.bind("<KeyRelease>", self._filter_list)

        text_frame = ctk.CTkFrame(self, fg_color="#111115", corner_radius=8)
        text_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.txt_preview = scrolledtext.ScrolledText(
            text_frame, bg="#111115", fg=CONFIG.THEME["TEXT_LIGHT"], font=("Consolas", 10),
            relief="flat", wrap="none", borderwidth=0, highlightthickness=0
        )
        self.txt_preview.pack(fill="both", expand=True, padx=10, pady=10)
        self._populate_text(self.pending_files, self.pending_pids)

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(fill="x", padx=15, pady=(0, 15))
        btn_cancel = ctk.CTkButton(
            frame_btns, text="🛑 取消清理", fg_color=CONFIG.THEME["CARD_BG"],
            hover_color=CONFIG.THEME["DANGER"], text_color=CONFIG.THEME["TEXT_LIGHT"], command=self.destroy
        )
        btn_cancel.pack(side="right", padx=5)

        btn_confirm = ctk.CTkButton(
            frame_btns, text="⚡ 確認並執行真實清理", fg_color=CONFIG.THEME["SUCCESS"],
            hover_color="#2196F3", text_color=CONFIG.THEME["TEXT_LIGHT"], command=self._confirm
        )
        btn_confirm.pack(side="right", padx=5)

    def _populate_text(self, files, pids, keyword=""):
        self.txt_preview.delete("1.0", "end")
        kw = keyword.lower()
        if pids:
            self.txt_preview.insert("end", "=== 擬關閉之高佔用閒置處理程序 ===\n")
            for pid, proc_name, mem_mb in pids:
                line = f"[處理程序] {proc_name} (PID: {pid}) - 佔用 {mem_mb:.1f} MB RAM\n"
                if not kw or kw in line.lower(): self.txt_preview.insert("end", line)
            self.txt_preview.insert("end", "\n")
        self.txt_preview.insert("end", "=== 擬清理之檔案清單 ===\n")
        for f in files:
            if not kw or kw in f.lower(): self.txt_preview.insert("end", f"{f}\n")

    def _filter_list(self, event=None):
        self._populate_text(self.pending_files, self.pending_pids, self.entry_search.get())

    def _confirm(self):
        self.destroy()
        self.on_confirm_callback()

class AddCustomScriptDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_add_callback):
        super().__init__(parent)
        self.title("➕ 新增開機自動執行的軟體或腳本")
        self.geometry("550x380")
        self.on_add_callback = on_add_callback
        self.transient(parent)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        lbl_title = ctk.CTkLabel(self, text="📝 請填寫自訂開機執行項資訊", font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"), text_color=CONFIG.THEME["PRIMARY"])
        lbl_title.pack(anchor="w", padx=20, pady=(15, 10))

        frame_form = ctk.CTkFrame(self, fg_color="transparent")
        frame_form.pack(fill="both", expand=True, padx=20, pady=5)

        lbl_name = ctk.CTkLabel(frame_form, text="顯示名稱：", font=ctk.CTkFont(family="Microsoft JhengHei", size=12))
        lbl_name.grid(row=0, column=0, sticky="w", pady=6)
        self.entry_name = ctk.CTkEntry(frame_form, placeholder_text="例如：自動備份腳本", width=360)
        self.entry_name.grid(row=0, column=1, sticky="w", pady=6)

        lbl_path = ctk.CTkLabel(frame_form, text="檔案路徑：", font=ctk.CTkFont(family="Microsoft JhengHei", size=12))
        lbl_path.grid(row=1, column=0, sticky="w", pady=6)
        self.entry_path = ctk.CTkEntry(frame_form, placeholder_text="C:\\Scripts\\my_script.py", width=360)
        self.entry_path.grid(row=1, column=1, sticky="w", pady=6)

        lbl_args = ctk.CTkLabel(frame_form, text="附加參數：", font=ctk.CTkFont(family="Microsoft JhengHei", size=12))
        lbl_args.grid(row=2, column=0, sticky="w", pady=6)
        self.entry_args = ctk.CTkEntry(frame_form, placeholder_text="無可留空，例如 --quiet", width=360)
        self.entry_args.grid(row=2, column=1, sticky="w", pady=6)

        lbl_delay = ctk.CTkLabel(frame_form, text="延遲啟動：", font=ctk.CTkFont(family="Microsoft JhengHei", size=12))
        lbl_delay.grid(row=3, column=0, sticky="w", pady=6)
        self.cmb_delay = ctk.CTkComboBox(frame_form, values=["0 秒 (即時)", "15 秒", "30 秒", "60 秒"], width=180, state="readonly")
        self.cmb_delay.set("15 秒")
        self.cmb_delay.grid(row=3, column=1, sticky="w", pady=6)

        btn_save = ctk.CTkButton(
            self, text="💾 儲存並新增至開機清單", font=ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], hover_color="#2196F3", command=self._save
        )
        btn_save.pack(fill="x", padx=20, pady=(10, 20))

    def _save(self):
        name = self.entry_name.get().strip()
        path = self.entry_path.get().strip()
        args = self.entry_args.get().strip()
        delay_str = self.cmb_delay.get()
        if not name or not path:
            messagebox.showwarning("欄位不足", "請填寫顯示名稱與檔案路徑！")
            return
        self.on_add_callback(name, path, args, delay_str)
        self.destroy()

# ==============================================================================
# 6. 主使用者介面實作 (SystemOptimizerApp v2.5 排程與開關全能版)
# ==============================================================================
class SystemOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{CONFIG.APP_NAME} {CONFIG.VERSION}")
        self.geometry("1240x860")
        self.minsize(1000, 700)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=CONFIG.THEME["BG_DARK"])

        self.default_font    = ctk.CTkFont(family="Microsoft JhengHei", size=13)
        self.small_font      = ctk.CTkFont(family="Microsoft JhengHei", size=11)
        self.title_font      = ctk.CTkFont(family="Microsoft JhengHei", size=15, weight="bold")
        self.sec_title_font  = ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold")
        self.header_font     = ctk.CTkFont(family="Microsoft JhengHei", size=18, weight="bold")
        self.badge_font      = ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold")
        
        self.total_freed_disk_mb = 0.0
        self.total_freed_ram_mb = 0.0

        # UI 控制變數
        self.var_clean_temp = ctk.BooleanVar(value=True)
        self.var_clean_crash_wer = ctk.BooleanVar(value=True)
        self.var_clean_delivery_opt = ctk.BooleanVar(value=True)
        self.var_clean_pkg_cache = ctk.BooleanVar(value=True)
        self.var_clean_prefetch = ctk.BooleanVar(value=False)

        self.var_clean_browser = ctk.BooleanVar(value=True)
        self.var_clean_shader = ctk.BooleanVar(value=True)
        self.var_clean_thumbnail = ctk.BooleanVar(value=True)
        self.var_clean_apps = ctk.BooleanVar(value=True)
        self.var_smart_scan = ctk.BooleanVar(value=True)

        self.var_kill_zombie = ctk.BooleanVar(value=True)
        self.var_ram_limit = ctk.IntVar(value=CONFIG.DEFAULT_PROCESS_RAM_LIMIT)
        self.var_scan_depth = ctk.StringVar(value=CONFIG.DEFAULT_SCAN_DEPTH)
        self.var_dry_run = ctk.BooleanVar(value=CONFIG.DRY_RUN)

        self.var_hide_sys_components = ctk.BooleanVar(value=True)
        self.cached_installed_software = []

        # 開機分頁：工作排程器顯示開關 + 批次停用勾選框
        self.var_show_tasks = ctk.BooleanVar(value=False)  # 預設隱藏工作排程器
        self.startup_check_vars = {}   # {item_index: BooleanVar}
        self.startup_items_cache = []  # 暫存最後一次讀取到的 sys_items

        self.custom_scripts = BootOptimizerEngine.load_custom_scripts()

        self.build_ui()
        self.append_log(f"✅ {CONFIG.APP_NAME} {CONFIG.VERSION} 已成功啟動。", CONFIG.THEME["SUCCESS"])
        self.append_log("💡 提示：點擊左側分頁視窗切換「快取優化」、「開機加速」與「軟體徹底卸載」。\n---", CONFIG.THEME["TEXT_MUTED"])

    def build_ui(self):
        # ── 頁首 Header ──────────────────────────────────────────────
        header_frame = ctk.CTkFrame(self, fg_color=CONFIG.THEME["CARD_BG"], height=72, corner_radius=14)
        header_frame.pack(fill="x", padx=16, pady=(12, 6))
        header_frame.pack_propagate(False)

        # 左側 LOGO + 標題
        lbl_logo = ctk.CTkLabel(
            header_frame, text="⚡",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=28),
            text_color=CONFIG.THEME["PRIMARY"]
        )
        lbl_logo.pack(side="left", padx=(18, 4), pady=14)

        lbl_title = ctk.CTkLabel(
            header_frame, text=CONFIG.APP_NAME,
            font=self.header_font, text_color=CONFIG.THEME["TEXT_LIGHT"]
        )
        lbl_title.pack(side="left", padx=(0, 20), pady=14)

        # 版本標籤 (Pill 樣式)
        lbl_ver_frame = ctk.CTkFrame(header_frame, fg_color=CONFIG.THEME["PRIMARY"], corner_radius=20)
        lbl_ver_frame.pack(side="left", pady=22)
        ctk.CTkLabel(
            lbl_ver_frame, text=CONFIG.VERSION,
            font=self.small_font, text_color="#FFFFFF"
        ).pack(padx=10, pady=3)

        # 右側記憶體狀態
        self.lbl_ram_status = ctk.CTkLabel(
            header_frame, text="💾 讀取記憶體中...",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold"),
            text_color=CONFIG.THEME["SUCCESS"]
        )
        self.lbl_ram_status.pack(side="right", padx=20, pady=14)

        self.update_ram_status()

        # 進度條
        self.progress_bar = ctk.CTkProgressBar(
            self, height=5,
            progress_color=CONFIG.THEME["PRIMARY"],
            fg_color=CONFIG.THEME["CARD_BG"],
            corner_radius=3
        )
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 6))
        self.progress_bar.set(0)

        # ── 主體 ─────────────────────────────────────────────────────
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        # ── 側邊欄 Sidebar ───────────────────────────────────────────
        sidebar = ctk.CTkFrame(
            main_container, fg_color=CONFIG.THEME["SIDEBAR_BG"],
            width=220, corner_radius=14
        )
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        # Sidebar 標題
        sidebar_title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        sidebar_title_frame.pack(fill="x", padx=14, pady=(18, 4))
        ctk.CTkLabel(
            sidebar_title_frame, text="功能導覽",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            text_color=CONFIG.THEME["TEXT_MUTED"]
        ).pack(anchor="w")
        # 分隔線
        ctk.CTkFrame(sidebar, fg_color=CONFIG.THEME["CARD_BORDER"], height=1).pack(fill="x", padx=14, pady=(2, 10))

        NAV_ITEMS = [
            ("cleaner",   "🧹", "清理快取與記憶體"),
            ("boot",      "🚀", "開機加速與排程"),
            ("uninstall", "🗑",  "軟體卸載 (Geek)"),
            ("settings",  "⚙️",  "設定與保護白名單"),
        ]
        self._nav_buttons = {}
        for page_key, icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}  {label}",
                font=self.default_font,
                anchor="w",
                height=42,
                corner_radius=10,
                fg_color="transparent",
                hover_color=CONFIG.THEME["CARD_BG"],
                text_color=CONFIG.THEME["TEXT_MUTED"],
                command=lambda k=page_key: self.show_page(k)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self._nav_buttons[page_key] = btn

        # 側邊欄底部 App 資訊
        ctk.CTkFrame(sidebar, fg_color=CONFIG.THEME["CARD_BORDER"], height=1).pack(fill="x", padx=14, pady=(12, 8))
        ctk.CTkLabel(
            sidebar, text="System Optimizer Tool",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=10),
            text_color=CONFIG.THEME["TEXT_MUTED"]
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # ── 內容區 ──────────────────────────────────────────────────
        self.page_container = ctk.CTkFrame(main_container, fg_color="transparent")
        self.page_container.pack(side="right", fill="both", expand=True)

        # 相容性：保留舊的 btn_nav_* 引用
        self.btn_nav_cleaner   = self._nav_buttons["cleaner"]
        self.btn_nav_boot      = self._nav_buttons["boot"]
        self.btn_nav_uninstall = self._nav_buttons["uninstall"]
        self.btn_nav_settings  = self._nav_buttons["settings"]

        self.pages = {}
        self.build_page_cleaner()
        self.build_page_boot()
        self.build_page_uninstall()
        self.build_page_settings()

        self.show_page("cleaner")

        # ── 底部狀態列 Footer ────────────────────────────────────────
        footer_frame = ctk.CTkFrame(self, fg_color=CONFIG.THEME["CARD_BG"], height=48, corner_radius=12)
        footer_frame.pack(fill="x", padx=16, pady=(0, 12))
        footer_frame.pack_propagate(False)

        # 左側統計數字
        self.lbl_total_stats = ctk.CTkLabel(
            footer_frame,
            text="🧹 暫存已清理：0.0 MB　|　💾 記憶體已釋放：0.0 MB",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold"),
            text_color=CONFIG.THEME["SUCCESS"]
        )
        self.lbl_total_stats.pack(side="left", padx=18, pady=12)

        # 右側版本小字
        ctk.CTkLabel(
            footer_frame, text=CONFIG.VERSION,
            font=ctk.CTkFont(family="Microsoft JhengHei", size=11),
            text_color=CONFIG.THEME["TEXT_MUTED"]
        ).pack(side="right", padx=18)

    def show_page(self, page_name):
        for name, page in self.pages.items():
            page.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)

        for name, btn in self._nav_buttons.items():
            if name == page_name:
                btn.configure(
                    fg_color=CONFIG.THEME["PRIMARY"],
                    text_color="#FFFFFF"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=CONFIG.THEME["TEXT_MUTED"]
                )

    # --------------------------------------------------------------------------
    # 分頁 1：🧹 快取與記憶體優化 (Page Cleaner)
    # --------------------------------------------------------------------------
    def build_page_cleaner(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["cleaner"] = page

        left_scroll = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10, width=380)
        left_scroll.pack(side="left", fill="both", padx=(0, 10))

        ctk.CTkLabel(left_scroll, text="⚙️ 選擇要清理的快取標的", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=10, pady=(10, 4))
        
        ctk.CTkLabel(left_scroll, text="🟢 第一類：完全無害 / 無感清理項目", font=self.sec_title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(anchor="w", padx=10, pady=(6, 2))
        ctk.CTkCheckBox(left_scroll, text="清理使用者暫存區 (%TEMP%)", variable=self.var_clean_temp, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="崩潰傾印檔與錯誤報告 (CrashDumps/WER)", variable=self.var_clean_crash_wer, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="微軟傳遞優化下載快取 (Delivery Optimization)", variable=self.var_clean_delivery_opt, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="開發套件包快取 (pip/uv/npm/pnpm/Poetry)", variable=self.var_clean_pkg_cache, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="清理系統預載歷史 (Prefetch - 需管理員)", variable=self.var_clean_prefetch, font=self.default_font).pack(anchor="w", padx=20, pady=3)

        ctk.CTkLabel(left_scroll, text="🟡 第二類：輕微影響 / 短暫延遲快取標的", font=self.sec_title_font, text_color=CONFIG.THEME["WARNING"]).pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkCheckBox(left_scroll, text="網頁暫存快取 (Chrome/Edge/Brave/Firefox)", variable=self.var_clean_browser, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="顯卡與 DirectX 著色器快取 (Shader Cache)", variable=self.var_clean_shader, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="Windows 檔案總管縮圖快取 (Thumbnail)", variable=self.var_clean_thumbnail, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="軟體與 IDE 快取 (VS Code/JetBrains/Adobe)", variable=self.var_clean_apps, font=self.default_font).pack(anchor="w", padx=20, pady=3)
        ctk.CTkCheckBox(left_scroll, text="🔍 智慧快取自動盤點 (搜尋 > 50MB 快取)", variable=self.var_smart_scan, font=self.default_font).pack(anchor="w", padx=20, pady=3)

        ctk.CTkFrame(left_scroll, fg_color=CONFIG.THEME["BG_DARK"], height=2).pack(fill="x", padx=10, pady=8)
        
        ctk.CTkCheckBox(left_scroll, text="關閉高記憶體佔用閒置處理程序", variable=self.var_kill_zombie, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        
        lbl_slider = ctk.CTkLabel(left_scroll, text=f"閒置程式記憶體門檻: {CONFIG.DEFAULT_PROCESS_RAM_LIMIT} MB", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["WARNING"])
        lbl_slider.pack(anchor="w", padx=10, pady=(4, 2))
        
        slider_ram = ctk.CTkSlider(left_scroll, from_=100, to=2000, number_of_steps=38, variable=self.var_ram_limit, command=lambda v: lbl_slider.configure(text=f"閒置程式記憶體門檻: {int(v)} MB"))
        slider_ram.pack(fill="x", padx=10, pady=4)

        cleaner_action_box = ctk.CTkFrame(left_scroll, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        cleaner_action_box.pack(fill="x", padx=10, pady=(12, 10))

        chk_dry_run = ctk.CTkCheckBox(cleaner_action_box, text="🛡️ 僅預覽不刪除檔案 (安全測試)", variable=self.var_dry_run, font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color=CONFIG.THEME["PRIMARY"])
        chk_dry_run.pack(anchor="w", padx=10, pady=(8, 6))

        self.btn_launch = ctk.CTkButton(
            cleaner_action_box, text="⚡ 刪除勾選暫存與釋放記憶體", font=ctk.CTkFont(family="Microsoft JhengHei", size=13, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color="#2196F3",
            corner_radius=8, height=38, command=self.execute_optimization_flow
        )
        self.btn_launch.pack(fill="x", padx=10, pady=(4, 10))

        right_panel = ctk.CTkFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="🖥️ 執行過程即時記錄Console", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=15, pady=(12, 5))
        log_frame = ctk.CTkFrame(right_panel, fg_color="#111115", corner_radius=8)
        log_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.log_display = scrolledtext.ScrolledText(
            log_frame, bg="#111115", fg=CONFIG.THEME["TEXT_LIGHT"], font=("Consolas", 11),
            relief="flat", wrap="word", borderwidth=0, highlightthickness=0
        )
        self.log_display.pack(fill="both", expand=True, padx=10, pady=10)
        for key, color in CONFIG.THEME.items():
            self.log_display.tag_config(color, foreground=color)

    # --------------------------------------------------------------------------
    # 分頁 2：🚀 開機加速與工作排程 (Page Boot - 雙層 Startup 直覺管理與軟性防衛版)
    # --------------------------------------------------------------------------
    def build_page_boot(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["boot"] = page

        card_uptime = ctk.CTkFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        card_uptime.pack(fill="x", pady=(0, 10))

        uptime_text = BootOptimizerEngine.get_last_boot_time_str()
        ctk.CTkLabel(card_uptime, text=f"📊 開機健康度監測：{uptime_text}", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(side="left", padx=15, pady=12)

        # 頂部一鍵直達 Startup 資料夾快捷按鈕列
        frame_quick_folders = ctk.CTkFrame(card_uptime, fg_color="transparent")
        frame_quick_folders.pack(side="right", padx=10, pady=8)

        btn_open_user_st = ctk.CTkButton(
            frame_quick_folders, text="📂 開啟【個人】啟動資料夾", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["PRIMARY"], hover_color=CONFIG.THEME["PRIMARY_HOVER"], width=170,
            command=lambda: self._open_startup_dir("user")
        )
        btn_open_user_st.pack(side="left", padx=4)

        btn_open_common_st = ctk.CTkButton(
            frame_quick_folders, text="📂 開啟【全機共用】啟動資料夾", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["ACCENT"], hover_color="#8B5CF6", width=190,
            command=lambda: self._open_startup_dir("common")
        )
        btn_open_common_st.pack(side="left", padx=4)

        btn_add_script = ctk.CTkButton(
            frame_quick_folders, text="➕ 新增自訂延遲腳本", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], hover_color=CONFIG.THEME["SUCCESS_HOVER"], width=150,
            command=self._open_add_script_modal
        )
        btn_add_script.pack(side="left", padx=4)

        scroll_boot = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        scroll_boot.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_boot, text="⚙️ Windows 開機啟動項管理 (直覺分區與軍規軟性防禦)", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=15, pady=(12, 4))
        ctk.CTkLabel(scroll_boot, text="💡 提示：本區分為【Startup 捷徑】、【登錄檔 Run 鍵值】與【工作排程器】三大直覺區塊。Startup 捷徑可安全備份刪除；登錄檔與排程器提供「軟性停用/開啟」，絕不安裝或硬刪除系統關鍵項目。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=(0, 6))

        # 篩選與批次控制列
        filter_bar = ctk.CTkFrame(scroll_boot, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        filter_bar.pack(fill="x", padx=15, pady=(0, 8))

        chk_show_tasks = ctk.CTkCheckBox(
            filter_bar,
            text="📅 同時顯示工作排程器任務 (系統背景自動更新，一般不需變動)",
            variable=self.var_show_tasks,
            font=self.default_font,
            text_color=CONFIG.THEME["TEXT_MUTED"],
            command=self.load_system_startup_list
        )
        chk_show_tasks.pack(side="left", padx=12, pady=8)

        self.btn_batch_disable = ctk.CTkButton(
            filter_bar,
            text="🚫 批次停用勾選項目",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["DANGER"],
            hover_color="#C0392B",
            width=160,
            command=self._batch_disable_checked_items
        )
        self.btn_batch_disable.pack(side="right", padx=12, pady=8)

        self.frame_sys_startup_list = ctk.CTkFrame(scroll_boot, fg_color="transparent")
        self.frame_sys_startup_list.pack(fill="x", padx=15, pady=5)

        ctk.CTkFrame(scroll_boot, fg_color=CONFIG.THEME["BG_DARK"], height=2).pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(scroll_boot, text="📝 自訂開機軟體/腳本延遲啟動管理清單", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=15, pady=(4, 6))

        self.frame_script_list = ctk.CTkFrame(scroll_boot, fg_color="transparent")
        self.frame_script_list.pack(fill="x", padx=15, pady=5)

        self.after(300, self.load_system_startup_list)
        self.refresh_custom_script_list()

    def _open_startup_dir(self, scope):
        ok, msg = BootOptimizerEngine.open_startup_folder(scope)
        if not ok:
            messagebox.showerror("開啟失敗", msg)

    def load_system_startup_list(self):
        for widget in self.frame_sys_startup_list.winfo_children(): widget.destroy()

        def _bg_load():
            sys_items = BootOptimizerEngine.get_system_startup_programs()
            self.after(0, lambda: self.render_system_startup_items(sys_items))
        threading.Thread(target=_bg_load, daemon=True).start()

    def render_system_startup_items(self, sys_items):
        for widget in self.frame_sys_startup_list.winfo_children(): widget.destroy()
        self.startup_check_vars.clear()
        self.startup_items_cache = sys_items

        show_tasks = self.var_show_tasks.get()
        visible_items = [it for it in sys_items if show_tasks or it["type"] != "task"]

        if not visible_items:
            ctk.CTkLabel(
                self.frame_sys_startup_list,
                text="目前未偵測到任何跟隨開機啟動的第三方軟體。" if not show_tasks else "目前未偵測到任何跟隨開機啟動的第三方軟體或排程任務。",
                font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]
            ).pack(anchor="w", pady=8)
            return

        # 將項目按「Startup 捷徑區」、「登錄檔 Run 區」與「工作排程器區」進行分區
        file_items = [it for it in visible_items if it["type"] == "file"]
        reg_items = [it for it in visible_items if it["type"] == "registry"]
        task_items = [it for it in visible_items if it["type"] == "task"]

        # ======================================================================
        # 區塊 1：🟢 Startup 資料夾捷徑區 (最直觀且安全)
        # ======================================================================
        if file_items:
            sec1_header = ctk.CTkFrame(self.frame_sys_startup_list, fg_color="transparent")
            sec1_header.pack(fill="x", pady=(10, 4))
            ctk.CTkLabel(sec1_header, text="🟢 1. Startup 開機啟動資料夾捷徑區 (直觀且安全刪除/備份)", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(side="left")

            for idx, item in enumerate(file_items):
                self._render_single_startup_row(item, idx)

        # ======================================================================
        # 區塊 2：🟡 Windows 登錄檔 Run 鍵值區 (軟性開關防護)
        # ======================================================================
        if reg_items:
            sec2_header = ctk.CTkFrame(self.frame_sys_startup_list, fg_color="transparent")
            sec2_header.pack(fill="x", pady=(15, 4))
            ctk.CTkLabel(sec2_header, text="🟡 2. Windows 登錄檔 Run 鍵值區 (提供軟性關閉/開啟，不刪除機碼)", font=self.title_font, text_color=CONFIG.THEME["WARNING"]).pack(side="left")

            for idx, item in enumerate(reg_items):
                self._render_single_startup_row(item, idx + 100)

        # ======================================================================
        # 區塊 3：🔵 Windows 工作排程器啟動區 (系統背景與定時排程)
        # ======================================================================
        if task_items:
            sec3_header = ctk.CTkFrame(self.frame_sys_startup_list, fg_color="transparent")
            sec3_header.pack(fill="x", pady=(15, 4))
            ctk.CTkLabel(sec3_header, text="🔵 3. Windows 工作排程器啟動區 (系統背景與定時排程，軟性切換)", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(side="left")

            for idx, item in enumerate(task_items):
                self._render_single_startup_row(item, idx + 200)

    def _render_single_startup_row(self, item, idx):
        row = ctk.CTkFrame(self.frame_sys_startup_list, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        row.pack(fill="x", pady=4)

        # 左側勾選框
        chk_var = ctk.BooleanVar(value=False)
        self.startup_check_vars[idx] = (chk_var, item)
        chk = ctk.CTkCheckBox(
            row, text="", variable=chk_var, width=28,
            checkbox_width=18, checkbox_height=18,
            fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
            state="normal" if item["enabled"] else "disabled"
        )
        chk.pack(side="left", padx=(8, 0), pady=10)

        # 狀態 Badge 與範圍標籤
        status_text = "🟢 [運行中]" if item["enabled"] else "🛑 [已關閉]"
        status_color = CONFIG.THEME["SUCCESS"] if item["enabled"] else CONFIG.THEME["TEXT_MUTED"]

        frame_left = ctk.CTkFrame(row, fg_color="transparent", width=120)
        frame_left.pack(side="left", padx=(6, 5), pady=8)

        lbl_status = ctk.CTkLabel(frame_left, text=status_text, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=status_color)
        lbl_status.pack(anchor="w")

        lbl_impact = ctk.CTkLabel(frame_left, text=item["impact"], font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["WARNING"])
        lbl_impact.pack(anchor="w")

        # 軟體與用途說明
        frame_info = ctk.CTkFrame(row, fg_color="transparent")
        frame_info.pack(side="left", fill="both", expand=True, padx=5, pady=6)

        title_text = f"✨ {item['friendly_name']}"
        if item.get("scope") == "user":
            title_text += " [個人帳號]"
        elif item.get("scope") == "common":
            title_text += " [全機共用]"

        lbl_name = ctk.CTkLabel(frame_info, text=title_text, font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w")
        lbl_name.pack(anchor="w")

        # 若為驅動或核心系統項目，加入警示標籤
        if item.get("is_sys_driver"):
            lbl_sys_warn = ctk.CTkLabel(frame_info, text="⚠️ 系統/驅動必備項目 (建議維持開啟，勿隨意刪除)", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["WARNING"], anchor="w")
            lbl_sys_warn.pack(anchor="w", pady=(1, 0))

        lbl_desc = ctk.CTkLabel(frame_info, text=f"💡 開機用途：{item['description']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["SUCCESS"], anchor="w")
        lbl_desc.pack(anchor="w", pady=(1, 0))

        raw_info = f"登記名稱：{item['raw_name']} | 位置：{item['location']}\n指令：{item['command']}"
        lbl_cmd = ctk.CTkLabel(frame_info, text=raw_info, font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w", justify="left")
        lbl_cmd.pack(anchor="w", pady=(2, 0))

        # 右側一鍵控制按鈕
        if item["type"] == "file":
            # Startup 捷徑專屬按鈕：備份並刪除捷徑
            btn_del_shortcut = ctk.CTkButton(
                row, text="🗑️ 備份並刪除捷徑", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=150, fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
                command=lambda it=item: self._backup_delete_shortcut(it)
            )
            btn_del_shortcut.pack(side="right", padx=10, pady=10)
        else:
            # 登錄檔與排程器軟性開關按鈕 (關閉 / 開啟)
            if item["enabled"]:
                btn_txt = "🚫 軟性停用開機啟動"
                btn_col = CONFIG.THEME["DANGER"]
                btn_hov = "#C0392B"
            else:
                btn_txt = "✅ 復原開啟開機啟動"
                btn_col = CONFIG.THEME["SUCCESS"]
                btn_hov = "#27AE60"

            btn_toggle = ctk.CTkButton(
                row, text=btn_txt, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=160, fg_color=btn_col, hover_color=btn_hov,
                command=lambda it=item: self._toggle_startup_item(it)
            )
            btn_toggle.pack(side="right", padx=10, pady=10)

    def _backup_delete_shortcut(self, item):
        if messagebox.askyesno("備份並刪除捷徑確認", f"確定要將捷徑 [{item['friendly_name']}] 移至安全備份垃圾桶嗎？\n\n這將取消該軟體的開機自動啟動，對軟體本身零影響，隨時可復原。"):
            ok, msg = BootOptimizerEngine.backup_and_delete_shortcut(item)
            if ok:
                messagebox.showinfo("成功刪除捷徑", msg)
                self.load_system_startup_list()
            else:
                messagebox.showerror("刪除失敗", msg)

    def _batch_disable_checked_items(self):
        """批次停用所有勾選中的開機啟動項目（保留在清單，可再還原）"""
        checked = [(var, item) for var, item in self.startup_check_vars.values() if var.get() and item["enabled"]]
        if not checked:
            messagebox.showwarning("未選取任何項目", "請先勾選想要停用的開機啟動項目（左側勾選框）後，再執行批次停用。")
            return

        names = "、".join([item["friendly_name"] for _, item in checked])
        if not messagebox.askyesno(
            "確認批次停用",
            f"即將停用以下 {len(checked)} 個開機啟動項目：\n\n{names}\n\n停用後，這些項目仍會保留在清單中，可隨時點擊「✅ 復原 / 開啟開機啟動」按鈕還原。\n\n確定執行嗎？"
        ):
            return

        success_count = 0
        fail_msgs = []
        for _, item in checked:
            ok, msg = BootOptimizerEngine.toggle_startup_item_state(item)
            if ok:
                success_count += 1
            else:
                fail_msgs.append(f"• {item['friendly_name']}：{msg}")

        result_msg = f"✅ 已成功停用 {success_count} 個開機啟動項目。"
        if fail_msgs:
            result_msg += f"\n\n⚠️ 以下 {len(fail_msgs)} 個項目操作失敗 (可能需要管理員權限)：\n" + "\n".join(fail_msgs)

        messagebox.showinfo("批次停用結果", result_msg)
        self.load_system_startup_list()

    def _toggle_startup_item(self, item):
        success, msg = BootOptimizerEngine.toggle_startup_item_state(item)
        if success:
            messagebox.showinfo("更新成功", msg)
            self.load_system_startup_list()
        else:
            messagebox.showerror("操作失敗", f"無法修改狀態:\n{msg}")

    def refresh_custom_script_list(self):
        for widget in self.frame_script_list.winfo_children(): widget.destroy()

        if not self.custom_scripts:
            ctk.CTkLabel(self.frame_script_list, text="目前尚未新增任何自訂開機腳本。點擊右上角「➕ 新增」開始設定。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", pady=10)
            return

        for idx, item in enumerate(self.custom_scripts):
            row_frame = ctk.CTkFrame(self.frame_script_list, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
            row_frame.pack(fill="x", pady=4)

            name_str = f"📌 {item['name']} (延遲: {item['delay']})"
            ctk.CTkLabel(row_frame, text=name_str, font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(row_frame, text=item['path'], font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(side="left", padx=10, pady=8)

            btn_test = ctk.CTkButton(
                row_frame, text="🧪 立即測試執行腳本", font=ctk.CTkFont(family="Microsoft JhengHei", size=11),
                width=130, fg_color=CONFIG.THEME["PRIMARY"], command=lambda p=item['path'], a=item.get('args',''): self._test_script(p, a)
            )
            btn_test.pack(side="right", padx=6, pady=6)

            btn_del = ctk.CTkButton(
                row_frame, text="🗑️ 刪除", font=ctk.CTkFont(family="Microsoft JhengHei", size=11),
                width=60, fg_color=CONFIG.THEME["DANGER"], command=lambda i=idx: self._delete_custom_script(i)
            )
            btn_del.pack(side="right", padx=6, pady=6)

    def _open_add_script_modal(self):
        AddCustomScriptDialog(self, on_add_callback=self._add_custom_script_item)

    def _add_custom_script_item(self, name, path, args, delay):
        self.custom_scripts.append({"name": name, "path": path, "args": args, "delay": delay})
        BootOptimizerEngine.save_custom_scripts(self.custom_scripts)
        self.refresh_custom_script_list()
        messagebox.showinfo("新增成功", f"已成功將 [{name}] 加入自訂開機清單！")

    def _delete_custom_script(self, idx):
        if 0 <= idx < len(self.custom_scripts):
            del self.custom_scripts[idx]
            BootOptimizerEngine.save_custom_scripts(self.custom_scripts)
            self.refresh_custom_script_list()

    def _test_script(self, path, args):
        success, msg = BootOptimizerEngine.test_run_script(path, args)
        if success: messagebox.showinfo("測試成功", msg)
        else: messagebox.showerror("測試失敗", f"無法執行腳本:\n{msg}")

    # --------------------------------------------------------------------------
    # 分頁 3：🗑️ 軟體徹底卸載 (Page Uninstall - Geek Uninstaller 樣式)
    # --------------------------------------------------------------------------
    def build_page_uninstall(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["uninstall"] = page

        top_bar = ctk.CTkFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        top_bar.pack(fill="x", pady=(0, 10))

        self.lbl_sw_summary = ctk.CTkLabel(top_bar, text="📊 正在讀取軟體庫...", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"])
        self.lbl_sw_summary.pack(side="left", padx=15, pady=12)

        self.entry_sw_search = ctk.CTkEntry(top_bar, placeholder_text="🔍 搜尋軟體名稱或發行商...", width=240, font=self.default_font)
        self.entry_sw_search.pack(side="left", padx=10, pady=10)
        self.entry_sw_search.bind("<KeyRelease>", lambda e: self.render_uninstall_software_rows())

        chk_hide_sys = ctk.CTkCheckBox(
            top_bar, text="☑️ 隱藏系統必備元件 (防誤刪)", variable=self.var_hide_sys_components,
            font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], command=self.render_uninstall_software_rows
        )
        chk_hide_sys.pack(side="left", padx=10, pady=12)

        btn_reload = ctk.CTkButton(
            top_bar, text="🔄 重新讀取軟體庫", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            width=130, fg_color=CONFIG.THEME["PRIMARY"], command=self.load_uninstall_software_list
        )
        btn_reload.pack(side="right", padx=15, pady=10)

        self.scroll_uninstall = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        self.scroll_uninstall.pack(fill="both", expand=True)

        self.frame_sw_list = ctk.CTkFrame(self.scroll_uninstall, fg_color="transparent")
        self.frame_sw_list.pack(fill="x", padx=10, pady=5)

        self.after(400, self.load_uninstall_software_list)

    def load_uninstall_software_list(self):
        def _bg_load():
            sw_list = UninstallerEngine.get_installed_software_list()
            self.cached_installed_software = sw_list
            self.after(0, self.render_uninstall_software_rows)
        threading.Thread(target=_bg_load, daemon=True).start()

    def render_uninstall_software_rows(self):
        for widget in self.frame_sw_list.winfo_children(): widget.destroy()

        kw = self.entry_sw_search.get().strip().lower() if hasattr(self, 'entry_sw_search') else ""
        hide_sys = self.var_hide_sys_components.get()

        filtered_list = []
        total_mb = 0.0

        for item in self.cached_installed_software:
            if hide_sys and item["is_system"]:
                continue
            if kw and (kw not in item["name"].lower() and kw not in item["publisher"].lower()):
                continue
            filtered_list.append(item)
            total_mb += item["size_mb"]

        tot_gb_str = format_size_str(total_mb)
        self.lbl_sw_summary.configure(text=f"📊 已讀取 {len(filtered_list)} 個軟體 | 總佔用容量約 {tot_gb_str}")

        if not filtered_list:
            ctk.CTkLabel(self.frame_sw_list, text="找不到符合條件的已安裝軟體。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", pady=15)
            return

        for item in filtered_list:
            row = ctk.CTkFrame(self.frame_sw_list, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
            row.pack(fill="x", pady=3)

            if item["is_system"]:
                badge_text = "🛡️ [系統必備元件]"
                badge_color = CONFIG.THEME["WARNING"]
            else:
                badge_text = "📦 [應用軟體]"
                badge_color = CONFIG.THEME["PRIMARY"]

            lbl_icon = ctk.CTkLabel(row, text=badge_text, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=badge_color, width=110)
            lbl_icon.pack(side="left", padx=(10, 5), pady=8)

            frame_info = ctk.CTkFrame(row, fg_color="transparent")
            frame_info.pack(side="left", fill="both", expand=True, padx=5, pady=4)

            lbl_name = ctk.CTkLabel(frame_info, text=item["name"], font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w")
            lbl_name.pack(anchor="w")

            lbl_pub = ctk.CTkLabel(frame_info, text=f"發行商：{item['publisher']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w")
            lbl_pub.pack(anchor="w")

            lbl_date = ctk.CTkLabel(row, text=f"📅 安裝日期：{item['install_date']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["TEXT_MUTED"], width=150)
            lbl_date.pack(side="left", padx=5, pady=8)

            lbl_size = ctk.CTkLabel(row, text=f"💾 容量：{item['size_str']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["SUCCESS"], width=120)
            lbl_size.pack(side="left", padx=5, pady=8)

            btn_color = "#555555" if item["is_system"] else CONFIG.THEME["DANGER"]
            btn_hover = "#777777" if item["is_system"] else "#C0392B"

            btn_do_uninstall = ctk.CTkButton(
                row, text="🗑️ 卸載軟體並清理殘留", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=170, fg_color=btn_color, hover_color=btn_hover, command=lambda sw=item: self._uninstall_target(sw)
            )
            btn_do_uninstall.pack(side="right", padx=10, pady=8)

    def _uninstall_target(self, sw_info):
        sw_name = sw_info["name"]
        cmd = sw_info["uninstall_cmd"]
        is_sys = sw_info["is_system"]

        if is_sys:
            warn_msg = f"⚠️ [安全警示] [{sw_name}] 被標記為【系統必備組件】(如 Visual C++ 或驅動程式)。\n強行卸載可能會導致其他軟體或 Windows 無法正常運行！\n\n您確定真的要強制卸載嗎？"
            if not messagebox.askyesno("警告：系統必備元件", warn_msg, icon="warning"):
                return
        else:
            if not messagebox.askyesno("確認卸載", f"確定要卸載 [{sw_name}] 並掃描清理殘留資料夾嗎？"):
                return

        try:
            subprocess.Popen(cmd, shell=True)
            messagebox.showinfo("官方卸載中", f"已啟動 [{sw_name}] 官方卸載程序。\n請在彈出的視窗完成卸載後點擊確定，工具將自動掃描 AppData 殘留資料夾。")
            residuals = UninstallerEngine.scan_software_residuals(sw_name)
            if residuals:
                res_str = "\n".join([f"• {path} ({size:.1f} MB)" for path, size in residuals])
                if messagebox.askyesno("發現殘留資料夾", f"偵測到以下殘留資料夾:\n{res_str}\n\n要立即一鍵刪除這些殘留資料夾嗎？"):
                    for path, _ in residuals:
                        try: shutil.rmtree(path, ignore_errors=True)
                        except: pass
                    messagebox.showinfo("清理完成", "已成功移除所有殘留資料夾！")
            else:
                messagebox.showinfo("檢查完畢", "未發現顯著殘留資料夾，環境乾淨！")
            self.load_uninstall_software_list()
        except Exception as e:
            messagebox.showerror("卸載異常", f"執行卸載時發生錯誤:\n{str(e)}")

    # --------------------------------------------------------------------------
    # 分頁 4：⚙️ 設定與保護白名單 (Page Settings)
    # --------------------------------------------------------------------------
    def build_page_settings(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["settings"] = page

        scroll_set = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        scroll_set.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_set, text="⚙️ 系統優化保護白名單與設定", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=15, pady=(12, 6))

        desc = "🛡️ 保護白名單關鍵字：系統掃描清理時，絕對禁止刪除包含以下關鍵字的檔案或路徑。"
        ctk.CTkLabel(scroll_set, text=desc, font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=4)

        self.txt_whitelist = scrolledtext.ScrolledText(scroll_set, height=8, bg="#111115", fg=CONFIG.THEME["TEXT_LIGHT"], font=("Consolas", 11))
        self.txt_whitelist.pack(fill="x", padx=15, pady=10)
        self.txt_whitelist.insert("1.0", "\n".join(CONFIG.PROTECTED_KEYWORDS))

        btn_save_white = ctk.CTkButton(
            scroll_set, text="💾 儲存保護白名單設定", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], command=self._save_whitelist
        )
        btn_save_white.pack(anchor="w", padx=15, pady=10)

    def _save_whitelist(self):
        content = self.txt_whitelist.get("1.0", "end").strip()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        CONFIG.PROTECTED_KEYWORDS = lines
        messagebox.showinfo("儲存成功", "已成功更新安全保護白名單關鍵字！")

    # --------------------------------------------------------------------------
    # 一鍵排程與工作流管理 (Execution Flow)
    # --------------------------------------------------------------------------
    def update_ram_status(self):
        total, avail, used, load = get_system_ram_info()
        if total > 0:
            avail_gb = avail / 1024
            self.lbl_ram_status.configure(text=f"💾 系統記憶體負載: {load}% (可用 {avail_gb:.1f} GB)")
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
        self.lbl_total_stats.configure(text=f"🧹 暫存已清理容量：{disk_str} | 💾 記憶體已釋放容量：{ram_str}")

    def execute_optimization_flow(self):
        self.btn_launch.configure(state="disabled", text="⏳ 優化執行中...")
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])
        self.append_log(f"⏰ 任務啟動時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", CONFIG.THEME["TEXT_LIGHT"])
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])

        is_dry_run = self.var_dry_run.get()
        selected_depth_str = self.var_scan_depth.get()
        max_depth = CONFIG.SCAN_DEPTH_OPTIONS.get(selected_depth_str, 1)

        do_temp = self.var_clean_temp.get()
        do_crash_wer = self.var_clean_crash_wer.get()
        do_delivery_opt = self.var_clean_delivery_opt.get()
        do_pkg_cache = self.var_clean_pkg_cache.get()
        do_prefetch = self.var_clean_prefetch.get()

        do_browser = self.var_clean_browser.get()
        do_shader = self.var_clean_shader.get()
        do_thumbnail = self.var_clean_thumbnail.get()
        do_apps = self.var_clean_apps.get()
        do_smart = self.var_smart_scan.get()

        do_zombie = self.var_kill_zombie.get()
        current_threshold_mb = self.var_ram_limit.get()

        if is_dry_run:
            self.append_log("🛡️ 目前為 [僅預覽不刪除檔案]，僅測試顯示掃描結果。", CONFIG.THEME["WARNING"])

        def _update_progress(value): self.after(0, lambda: self.progress_bar.set(value))

        def _thread_task():
            try:
                tot_ram, avail_before, used_before, load_before = get_system_ram_info()
                _update_progress(0.05)
                pending_files = []; pending_pids = []; total_items = 0; freed_ram_from_procs = 0.0

                if do_temp:
                    res = OptimizerEngine.clean_temp_cache(self.append_log, CONFIG.TEMP_DIR, max_depth=max_depth, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.15)

                if do_crash_wer:
                    res = OptimizerEngine.clean_crash_dumps_and_wer(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.25)

                if do_delivery_opt:
                    res = OptimizerEngine.clean_delivery_optimization(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.35)

                if do_pkg_cache:
                    res = OptimizerEngine.clean_pkg_caches(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.45)

                if do_browser:
                    res = OptimizerEngine.clean_browser_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.55)

                if do_shader:
                    res = OptimizerEngine.clean_shader_caches(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.65)

                if do_thumbnail:
                    res = OptimizerEngine.clean_thumbnail_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.72)

                if do_apps:
                    res = OptimizerEngine.clean_app_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.80)

                if do_smart:
                    res = OptimizerEngine.scan_smart_caches(self.append_log, min_size_mb=50.0, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.85)

                if do_prefetch:
                    res = OptimizerEngine.clean_prefetch(self.append_log, CONFIG.PREFETCH_DIR, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.90)

                if do_zombie:
                    res = OptimizerEngine.kill_zombie_processes(self.append_log, ram_limit_mb=current_threshold_mb, dry_run=is_dry_run)
                    if is_dry_run: pending_pids.extend(res)
                    else: killed_count, freed_ram_from_procs = res
                _update_progress(0.95)

                if is_dry_run:
                    total_items = len(pending_files) + len(pending_pids)
                    est_proc_ram = sum(item[2] for item in pending_pids if len(item) >= 3)
                    est_proc_ram_fmt = format_size_str(est_proc_ram)
                    if total_items == 0:
                        _update_progress(1.0)
                        self.append_log("✅ 模擬測試掃描結束，目前環境乾淨，無需要清理的項目。\n", CONFIG.THEME["SUCCESS"])
                        self.after(0, lambda: messagebox.showinfo("模擬測試完成", "模擬掃描結束，目前無需要清理的項目。"))
                    else:
                        _update_progress(1.0)
                        self.append_log(f"📊 [模擬統計] 預計清理 {len(pending_files)} 個檔案，預計關閉 {len(pending_pids)} 個處理程序 (約釋放 {est_proc_ram_fmt} RAM)。", CONFIG.THEME["TEXT_LIGHT"])
                        
                        def _reset_launch_btn():
                            self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 刪除勾選暫存與釋放記憶體"))
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
                    self.append_log(f"🎉 【記憶體釋放成果】成功釋放實體記憶體: {ram_fmt}！", CONFIG.THEME["SUCCESS"])
                    self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                    self.after(0, lambda: messagebox.showinfo("優化完成", f"一鍵系統優化成功完畢！\n\n🎉 成功釋放實體記憶體: {ram_fmt}"))
            except Exception as e:
                self.append_log(f"❌ 執行過程中發生異常: {str(e)}", CONFIG.THEME["DANGER"])
            finally:
                if not is_dry_run or (is_dry_run and total_items == 0):
                    self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 刪除勾選暫存與釋放記憶體"))
                    self.after(2000, lambda: self.progress_bar.set(0))

        def _real_delete_thread(files, pids, avail_before, load_before):
            try:
                self.append_log("\n⚡ 使用者授權完成，開始執行真實清理與記憶體釋放...", CONFIG.THEME["DANGER"])
                deleted_count = 0; failed_count = 0; deleted_bytes = 0
                for file_path in files:
                    try:
                        if os.path.exists(file_path):
                            sz = os.path.getsize(file_path)
                            try: os.chmod(file_path, 0o777)
                            except: pass
                            os.remove(file_path)
                            deleted_count += 1; deleted_bytes += sz
                    except Exception: failed_count += 1

                killed_count = 0; freed_ram_proc = 0.0
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                for item in pids:
                    pid = item[0]; proc_name = item[1]; mem_mb = item[2] if len(item) >= 3 else 0.0
                    try:
                        subprocess.run(f"taskkill /F /PID {pid}", startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        killed_count += 1; freed_ram_proc += mem_mb
                    except: pass

                self.append_log(f"✅ 清理完成！成功刪除 {deleted_count} 個檔案，關閉 {killed_count} 個處理程序。", CONFIG.THEME["SUCCESS"])
                OptimizerEngine.force_garbage_collection(self.append_log)
                _update_progress(1.0)

                tot_ram, avail_after, used_after, load_after = get_system_ram_info()
                ram_diff_mb = avail_after - avail_before
                final_freed_ram_mb = max(ram_diff_mb, freed_ram_proc)
                disk_mb = deleted_bytes / (1024 * 1024)

                disk_fmt = format_size_str(disk_mb)
                ram_fmt = format_size_str(final_freed_ram_mb)

                self.after(0, lambda: self.update_cumulative_stats(freed_disk_mb=disk_mb, freed_ram_mb=final_freed_ram_mb))
                self.append_log(f"🎉 【清理成果】釋出暫存磁碟容量: {disk_fmt} / 實體記憶體: {ram_fmt}！", CONFIG.THEME["SUCCESS"])
                self.after(0, lambda: messagebox.showinfo("優化完成", f"清理與優化成功完畢！\n\n🧹 清理暫存檔: {disk_fmt}\n🎉 釋放實體記憶體: {ram_fmt}"))
            except Exception as e:
                self.append_log(f"❌ 清理過程中發生異常: {str(e)}", CONFIG.THEME["DANGER"])
            finally:
                self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 刪除勾選暫存與釋放記憶體"))
                self.after(2000, lambda: self.progress_bar.set(0))

        threading.Thread(target=_thread_task, daemon=True).start()

if __name__ == "__main__":
    try:
        if sys.platform.startswith('win'):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
    except Exception: pass

    app = SystemOptimizerApp()
    app.mainloop()