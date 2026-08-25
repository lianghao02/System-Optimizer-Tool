# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：Win32 原生記憶體與程序管理引擎 (engine/memory.py)
"""

import os
import sys
import ctypes
import subprocess
from ctypes import wintypes

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
    except Exception: pass
    return 0.0, 0.0, 0.0, 0

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
    """Win32 Native Toolhelp32 快照 API 取得極速程序列表 (無子行程)"""
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

class MemoryEngine:
    @staticmethod
    def trim_working_set(log_callback):
        """
        記憶體暫時釋放工具：針對背景程序縮減 Working Set 頁面分頁。
        說明：本操作僅呼叫 EmptyWorkingSet API 將可移出之頁面寫入分頁檔，適合高記憶體壓力情境下手動執行。
        """
        from engine.config import CONFIG
        log_callback("⚙️ 呼叫 Windows 原生 API 進行背景程序 Working Set 分頁暫時釋放...", CONFIG.THEME["PRIMARY"])
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
                log_callback(f"✅ Working Set 暫時釋放完成！共處理 {compressed_count} 個程序之分頁記憶體。", CONFIG.THEME["SUCCESS"])
                return compressed_count
        except Exception as e:
            log_callback(f"⚠️ Working Set 釋放跳過: {str(e)}", CONFIG.THEME["WARNING"])
        return 0

    @staticmethod
    def inspect_high_ram_processes(ram_limit_mb, target_extensions=None):
        """檢視高記憶體佔用程序 (僅讀取分析，絕不上鎖或關閉)"""
        from engine.config import CONFIG
        if target_extensions is None: target_extensions = CONFIG.TARGET_PROCESSES
        high_procs = []
        try:
            procs = get_running_processes_fast()
            my_pid = os.getpid()
            for pid, proc_name in procs:
                if pid <= 4 or pid == my_pid: continue
                if any(ext in proc_name.lower() for ext in target_extensions):
                    mem_mb = get_process_working_set_mb(pid)
                    if mem_mb > ram_limit_mb:
                        high_procs.append((pid, proc_name, mem_mb))
        except Exception: pass
        return high_procs

    @staticmethod
    def terminate_process_by_pid(pid, proc_name, log_callback):
        """結束指定 PID 之程序 (需經使用者明確勾選授權)"""
        from engine.config import CONFIG
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            mem_mb = get_process_working_set_mb(pid)
            res = subprocess.run(["taskkill", "/PID", str(pid)], startupinfo=startupinfo, capture_output=True, text=True)
            if res.returncode == 0:
                log_callback(f"❌ 已手動結束程序：{proc_name} (PID: {pid}) 釋放約 {mem_mb:.1f} MB", CONFIG.THEME["DANGER"])
                return True, mem_mb
            else:
                err_msg = res.stderr.strip() if res.stderr else "存取被拒絕"
                log_callback(f"⚠️ 結束程序 {proc_name} (PID: {pid}) 失敗: {err_msg} (可能需要以系統管理員身分執行)", CONFIG.THEME["WARNING"])
        except Exception as e:
            log_callback(f"⚠️ 結束程序 PID {pid} 失敗: {str(e)}", CONFIG.THEME["WARNING"])
        return False, 0.0
