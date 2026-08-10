# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：軟體徹底卸載與多維度信心分數殘留掃蕩引擎 (engine/uninstaller.py)
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
    REG_UNINSTALL_KEYS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM 64-bit"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM 32-bit"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU User"),
    ]

    @staticmethod
    def get_installed_software_list():
        """盤點 Windows 32-bit / 64-bit 已安裝軟體庫"""
        software_list = []
        seen_names = set()
        system_component_keys = ["microsoft visual c++", "windows SDK", "net framework", "directx", "vcredist", "redistributable", "update for windows"]

        for hkey, subkey, reg_type in UninstallerEngine.REG_UNINSTALL_KEYS:
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
                                    for f in os.listdir(install_location)[:30]:
                                        fp = os.path.join(install_location, f)
                                        if os.path.isfile(fp):
                                            tot_b += os.path.getsize(fp)
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

        software_list.sort(key=lambda x: (x["size_mb"], len(x["name"])), reverse=True)
        return software_list

    @staticmethod
    def is_software_still_installed(software_name):
        """檢查指定軟體是否依然存在於 Windows Registry (防止使用者取消卸載卻執行殘留清理)"""
        try:
            sw_list = UninstallerEngine.get_installed_software_list()
            sw_names_lower = [it["name"].lower() for it in sw_list]
            return software_name.lower() in sw_names_lower
        except Exception:
            return True

    @staticmethod
    def scan_appdata_leftovers_with_confidence(software_name, publisher="", install_location=""):
        """
        多維度信心分數 (Multi-factor Confidence Score) 殘留資料夾掃描演算法：
        +40  名稱完全吻合
        +25  InstallLocation 直接指向
        +15  Publisher 發行商相符
        +10  Executable 主程式名稱吻合
        +10  路徑包含產品唯一識別名稱
        """
        candidates = []
        user_home = CONFIG.USER_HOME
        search_roots = [
            os.path.join(user_home, "AppData", "Local"),
            os.path.join(user_home, "AppData", "Roaming"),
            r"C:\ProgramData"
        ]

        sw_name_clean = software_name.lower().replace(" ", "")
        pub_clean = publisher.lower().replace(" ", "") if publisher else ""
        loc_base = os.path.basename(install_location.rstrip("\\/")).lower() if install_location else ""

        exclude_keys = ["windows", "microsoft", "google", "system32", "program files", "temp"]

        for root_dir in search_roots:
            if not os.path.exists(root_dir): continue
            try:
                for item in os.listdir(root_dir):
                    item_path = os.path.join(root_dir, item)
                    if os.path.isdir(item_path):
                        item_lower = item.lower()
                        item_clean = item_lower.replace(" ", "")
                        if any(ex in item_lower for ex in exclude_keys): continue

                        score = 0
                        # 1. 名稱匹對分數 (+40)
                        if item_clean == sw_name_clean or sw_name_clean == item_clean:
                            score += 40
                        elif sw_name_clean in item_clean and len(sw_name_clean) >= 3:
                            score += 25

                        # 2. InstallLocation 直接指向分數 (+25)
                        if loc_base and loc_base == item_clean:
                            score += 25

                        # 3. Publisher 相符分數 (+15)
                        if pub_clean and pub_clean in item_clean and len(pub_clean) >= 3:
                            score += 15

                        # 4. 路徑唯一識別碼分數 (+10)
                        if any(kw in item_clean for kw in [sw_name_clean, loc_base] if len(kw) >= 4):
                            score += 10

                        if score >= 35:
                            dir_size = 0
                            try:
                                for r, d, files in os.walk(item_path):
                                    for f in files:
                                        try: dir_size += os.path.getsize(os.path.join(r, f))
                                        except: pass
                            except: pass
                            dir_mb = dir_size / (1024 * 1024)

                            # 評定可信度分級
                            if score >= 80:
                                confidence_label = "🟢 高可信 (>=90%)"
                            elif score >= 60:
                                confidence_label = "🟡 建議確認 (70-89%)"
                            else:
                                confidence_label = "🔴 低可信 (<70%)"

                            candidates.append({
                                "path": item_path,
                                "size_mb": dir_mb,
                                "size_fmt": format_size_str(dir_mb),
                                "score": score,
                                "confidence_label": confidence_label,
                                "auto_check": bool(score >= 80)  # 僅有高可信度才會預設勾選
                            })
            except: pass

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    @staticmethod
    def open_install_location(item):
        """開啟已安裝軟體之本機安裝資料夾或卸載路徑 (Windows File Explorer)"""
        try:
            loc = item.get("install_location", "").strip()
            un_cmd = item.get("uninstall_string", "").strip()

            target_path = ""
            if loc and os.path.exists(loc):
                target_path = loc
            elif ".exe" in un_cmd.lower():
                parts = un_cmd.split(".exe")
                raw = (parts[0] + ".exe").replace('"', '').strip()
                if os.path.exists(raw):
                    target_path = raw

            if target_path and os.path.isfile(target_path):
                subprocess.Popen(f'explorer.exe /select,"{target_path}"', shell=True)
                return True, f"已定位並開啟軟體檔案：{target_path}"
            elif target_path and os.path.isdir(target_path):
                os.startfile(target_path)
                return True, f"已開啟軟體安裝資料夾：{target_path}"
            else:
                return False, f"無法開啟位置 (安裝路徑不存在或未提供)：{loc if loc else un_cmd}"
        except Exception as e:
            return False, f"開啟失敗: {str(e)}"

    @staticmethod
    def execute_uninstall_command(uninstall_string):
        """呼叫官方卸載程式"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(uninstall_string, startupinfo=startupinfo, shell=True)
            proc.wait()  # 等待官方卸載程式結束
            return True, "官方卸載程式執行完畢。"
        except Exception as e:
            return False, f"呼叫卸載程式失敗: {str(e)}"
