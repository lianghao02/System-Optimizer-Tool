# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：開機加速與工作排程管理引擎 (engine/boot.py)
"""

import os
import sys
import shutil
import subprocess
import ctypes
import json
import shlex
if sys.platform.startswith('win'):
    import winreg

from engine.config import CONFIG

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
        """辨識是否為核心系統、顯示卡、音效卡或硬體驅動關鍵項目"""
        driver_keys = [
            "nvidia", "realtek", "intel", "amd", "radeon", "asus", "msi", 
            "lenovo", "dell", "hp", "synaptics", "logitech", "defend", "security",
            "windows", "system32", "svchost", "ctfmon"
        ]
        combined = (str(raw_name) + " " + str(cmd_str)).lower()
        return any(k in combined for k in driver_keys)

    @staticmethod
    def open_item_location(item):
        """開啟開機啟動項目之實體檔案或資料夾位置 (Windows File Explorer)"""
        try:
            cmd = item.get("command", "").strip()
            target_path = ""

            if item.get("type") == "file" and os.path.exists(cmd):
                target_path = cmd
            elif ".exe" in cmd.lower():
                parts = cmd.split(".exe")
                raw = (parts[0] + ".exe").replace('"', '').strip()
                if os.path.exists(raw):
                    target_path = raw
            elif os.path.exists(cmd):
                target_path = cmd

            if target_path and os.path.exists(target_path):
                subprocess.Popen(["explorer.exe", f"/select,{os.path.normpath(target_path)}"])
                return True, f"已開啟檔案位置：{target_path}"
            elif target_path and os.path.exists(os.path.dirname(target_path)):
                os.startfile(os.path.dirname(target_path))
                return True, f"已開啟資料夾位置：{os.path.dirname(target_path)}"
            else:
                return False, f"無法開啟位置 (檔案可能不存在或為純參數指令)：{cmd}"
        except Exception as e:
            return False, f"開啟失敗: {str(e)}"

    @staticmethod
    def backup_and_delete_shortcut(item):
        """安全將 Startup 資料夾之捷徑檔 (.lnk) 移至便攜式安全備份垃圾桶"""
        try:
            src = item["command"]
            if not os.path.exists(src):
                return False, "目標捷徑檔案不存在或已被刪除"
            
            backup_dir = CONFIG.BACKUP_SHORTCUTS_DIR
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
            backup_dir = CONFIG.BACKUP_SHORTCUTS_DIR
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
        """盤點雙層 Registry (Run/RunDisabled)、個人/全機 Startup 資料夾與 Windows 工作排程器項目"""
        items = []
        system_high_impact = ["steam", "epic", "discord", "spotify", "onedrive", "chrome", "edge", "update", "lenovo"]

        # 1. 讀取 Registry (個人與全機)
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

        # 3. 讀取 Windows 工作排程器 (schtasks 高效串流過濾)
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output('schtasks /Query /FO CSV /V', startupinfo=startupinfo, text=True, encoding='cp950', errors='ignore')
            lines = output.splitlines()
            if len(lines) > 1:
                header = [h.replace('"', '').strip() for h in lines[0].split(',')]
                for line in lines[1:]:
                    if "\\Microsoft\\Windows\\" in line: continue  # 即刻剔除微軟龐大內部排程，減少 90% 耗時
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
        """實作一鍵「關閉/停用」與「開啟/復原」開機啟動狀態"""
        try:
            curr_enabled = item["enabled"]
            item_type = item["type"]

            if item_type == "registry":
                hkey = item["hkey"]
                run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
                disabled_key = r"Software\Microsoft\Windows\CurrentVersion\RunDisabled"

                if curr_enabled:
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
            args = shlex.split(args_str, posix=False) if args_str else []
            if file_path.lower().endswith('.py'):
                cmd = [sys.executable, file_path, *args]
            else:
                cmd = [file_path, *args]
            subprocess.Popen(cmd)
            return True, "腳本已成功在背景啟動！"
        except Exception as e:
            return False, str(e)
