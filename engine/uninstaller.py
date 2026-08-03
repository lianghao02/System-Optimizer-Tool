# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：軟體徹底卸載與殘留清理引擎 (engine/uninstaller.py)
"""

import os
import sys
import shutil
import subprocess
import datetime
if sys.platform.startswith('win'):
    import winreg

from engine.config import CONFIG, format_size_str

class UninstallerEngine:
    @staticmethod
    def get_installed_software_list():
        """盤點 Windows 32-bit / 64-bit 已安裝軟體庫"""
        software_list = []
        seen_names = set()
        
        reg_uninstall_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM 64-bit"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM 32-bit"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU User"),
        ]

        system_component_keys = ["microsoft visual c++", "windows SDK", "net framework", "directx", "vcredist", "redistributable", "update for windows"]

        for hkey, subkey, reg_type in reg_uninstall_keys:
            try:
                key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                count = winreg.QueryInfoKey(key)[0]
                for i in range(count):
                    try:
                        sub_name = winreg.EnumKey(key, i)
                        sub_k = winreg.OpenKey(key, sub_name, 0, winreg.KEY_READ)
                        
                        def _get_val(k, name):
                            try: return winreg.QueryValueEx(k, name)[0]
                            except: return ""

                        display_name = str(_get_val(sub_k, "DisplayName")).strip()
                        uninstall_string = str(_get_val(sub_k, "UninstallString")).strip()
                        quiet_uninstall = str(_get_val(sub_k, "QuietUninstallString")).strip()
                        publisher = str(_get_val(sub_k, "Publisher")).strip()
                        install_date = str(_get_val(sub_k, "InstallDate")).strip()
                        install_location = str(_get_val(sub_k, "InstallLocation")).strip()
                        estimated_size = _get_val(sub_k, "EstimatedSize")
                        system_component = _get_val(sub_k, "SystemComponent")

                        winreg.CloseKey(sub_k)

                        if display_name and uninstall_string and display_name not in seen_names:
                            seen_names.add(display_name)
                            
                            size_mb = 0.0
                            if isinstance(estimated_size, int) and estimated_size > 0:
                                size_mb = estimated_size / 1024.0
                            elif install_location and os.path.exists(install_location):
                                try:
                                    tot_b = 0
                                    for r, d, files in os.walk(install_location):
                                        for f in files:
                                            try: tot_b += os.path.getsize(os.path.join(r, f))
                                            except: pass
                                    size_mb = tot_b / (1024 * 1024)
                                except: pass

                            is_system = bool(system_component == 1) or any(sk in display_name.lower() for sk in system_component_keys)

                            fmt_date = ""
                            if len(install_date) == 8 and install_date.isdigit():
                                fmt_date = f"{install_date[:4]}-{install_date[4:6]}-{install_date[6:]}"

                            software_list.append({
                                "name": display_name,
                                "publisher": publisher if publisher else "未知發行商",
                                "uninstall_string": quiet_uninstall if quiet_uninstall else uninstall_string,
                                "install_location": install_location,
                                "install_date": fmt_date,
                                "size_mb": size_mb,
                                "is_system": is_system,
                                "reg_type": reg_type
                            })
                    except: pass
                winreg.CloseKey(key)
            except: pass

        software_list.sort(key=lambda x: x["size_mb"], reverse=True)
        return software_list

    @staticmethod
    def scan_appdata_leftovers(software_name, install_location=""):
        """掃蕩已卸載軟體留下的 AppData / ProgramData 深層殘留資料夾"""
        leftover_dirs = []
        user_home = CONFIG.USER_HOME
        search_roots = [
            os.path.join(user_home, "AppData", "Local"),
            os.path.join(user_home, "AppData", "Roaming"),
            r"C:\ProgramData"
        ]

        keywords = [software_name.lower().replace(" ", "")]
        if install_location:
            base_n = os.path.basename(install_location.rstrip("\\/")).lower()
            if base_n and len(base_n) > 2:
                keywords.append(base_n)

        exclude_keys = ["windows", "microsoft", "google", "system32", "program files"]

        for root_dir in search_roots:
            if not os.path.exists(root_dir): continue
            try:
                for item in os.listdir(root_dir):
                    item_path = os.path.join(root_dir, item)
                    if os.path.isdir(item_path):
                        item_lower = item.lower()
                        if any(ex in item_lower for ex in exclude_keys): continue
                        if any(kw in item_lower for kw in keywords if len(kw) >= 3):
                            dir_size = 0
                            try:
                                for r, d, files in os.walk(item_path):
                                    for f in files:
                                        try: dir_size += os.path.getsize(os.path.join(r, f))
                                        except: pass
                            except: pass
                            dir_mb = dir_size / (1024 * 1024)
                            leftover_dirs.append((item_path, dir_mb))
            except: pass

        return leftover_dirs

    @staticmethod
    def execute_uninstall_command(uninstall_string):
        """呼叫官方卸載程式"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(uninstall_string, startupinfo=startupinfo, shell=True)
            return True, "已成功呼叫軟體官方卸載精靈。"
        except Exception as e:
            return False, f"呼叫卸載程式失敗: {str(e)}"
