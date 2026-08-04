#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool) - v3.0 全能極速便攜版
主要功能：
  1. 快取與記憶體優化：清理第一類/第二類系統快取、網頁快取、顯卡著色器快取、Win32 Working Set 原生記憶體壓縮與 Smart Cache Finder。
  2. 開機加速與工作排程管理：雙層 Startup 開機資料夾直覺管理 (個人/全機)、一鍵直達本機資料夾、捷徑檔安全備份垃圾桶與軟性停用防護。
  3. 軟體徹底卸載 (Geek 版)：讀取本機安裝軟體清單、顯示軟體容量/日期、殘留掃蕩。
  4. 解耦模組化與極速 0.5ms Win32 Toolhelp 快照，100% 零卡頓便攜架構。
相依套件：Python 3 標準庫 + CustomTkinter (pip install customtkinter)
執行指令：python main.py
"""

import os
import sys
import datetime
import threading
import customtkinter as ctk
from tkinter import messagebox, scrolledtext

from engine.config import CONFIG, get_system_ram_info, format_size_str, load_protected_keywords, save_protected_keywords
from engine.optimizer import OptimizerEngine
from engine.boot import BootOptimizerEngine
from engine.uninstaller import UninstallerEngine
from ui.dialogs import PreviewDialog, AddCustomScriptDialog

# ==============================================================================
# 4. 使用者介面實作 (GUI Interface - 頁籤模組化重構)
# ==============================================================================
class SystemOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{CONFIG.APP_NAME} {CONFIG.VERSION}")
        self.geometry("980x740")
        ctk.set_appearance_mode("dark")

        load_protected_keywords()

        self.default_font = ctk.CTkFont(family="Microsoft JhengHei", size=12)
        self.title_font = ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold")
        self.sec_title_font = ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold")

        self.total_freed_disk_mb = 0.0
        self.total_freed_ram_mb = 0.0

        # 全域無障礙與高效率熱鍵綁定 (AccessLint 指引)
        self.bind("<F5>", lambda e: self._handle_f5_refresh())
        self.bind("<Control-f>", lambda e: self._handle_ctrl_f())
        self.bind("<Control-F>", lambda e: self._handle_ctrl_f())

        # UI 控制變數
        self.var_clean_temp = ctk.BooleanVar(value=True)
        self.var_clean_crash_wer = ctk.BooleanVar(value=True)
        self.var_clean_delivery_opt = ctk.BooleanVar(value=True)
        self.var_clean_pkg_caches = ctk.BooleanVar(value=False)
        self.var_clean_shader = ctk.BooleanVar(value=False)
        self.var_clean_thumbnail = ctk.BooleanVar(value=False)
        self.var_clean_browser = ctk.BooleanVar(value=True)
        self.var_clean_apps = ctk.BooleanVar(value=True)
        self.var_smart_scan = ctk.BooleanVar(value=True)
        self.var_clean_prefetch = ctk.BooleanVar(value=False)
        
        self.var_kill_zombie = ctk.BooleanVar(value=True)
        self.var_ram_limit = ctk.IntVar(value=CONFIG.DEFAULT_PROCESS_RAM_LIMIT)
        self.var_scan_depth = ctk.StringVar(value=CONFIG.DEFAULT_SCAN_DEPTH)
        self.var_dry_run = ctk.BooleanVar(value=CONFIG.DRY_RUN)

        self.var_show_tasks = ctk.BooleanVar(value=False)
        self.var_hide_sys_components = ctk.BooleanVar(value=True)

        self.custom_scripts = BootOptimizerEngine.load_custom_scripts()
        self.startup_check_vars = {}
        self.startup_items_cache = []
        self.cached_installed_software = []

        self.pages = {}
        self.build_main_layout()

        self.append_log(f"✅ {CONFIG.APP_NAME} {CONFIG.VERSION} 已成功啟動。", CONFIG.THEME["SUCCESS"])
        self.append_log("💡 提示：本版本為全能極速便攜版，配備 Win32 原生快照與 0ms 零頓感介面。\n---", CONFIG.THEME["TEXT_MUTED"])

    def build_main_layout(self):
        # 頂部狀態列
        header_frame = ctk.CTkFrame(self, fg_color=CONFIG.THEME["CARD_BG"], height=60)
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        header_frame.pack_propagate(False)

        lbl_title = ctk.CTkLabel(header_frame, text=f"🚀 {CONFIG.APP_NAME}", font=ctk.CTkFont(family="Microsoft JhengHei", size=16, weight="bold"), text_color=CONFIG.THEME["TEXT_LIGHT"])
        lbl_title.pack(side="left", padx=15, pady=15)

        self.lbl_ram_status = ctk.CTkLabel(header_frame, text="💾 讀取 RAM 中...", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"), text_color=CONFIG.THEME["SUCCESS"])
        self.lbl_ram_status.pack(side="left", padx=15, pady=15)

        lbl_ver = ctk.CTkLabel(header_frame, text=CONFIG.VERSION, font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"])
        lbl_ver.pack(side="right", padx=15, pady=18)

        self.update_ram_status()

        # 進度條
        self.progress_bar = ctk.CTkProgressBar(self, height=6, progress_color=CONFIG.THEME["PRIMARY"], fg_color=CONFIG.THEME["CARD_BG"])
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.progress_bar.set(0)

        # 頂部 Navigation Bar
        nav_bar = ctk.CTkFrame(self, fg_color=CONFIG.THEME["SIDEBAR_BG"], height=44, corner_radius=8)
        nav_bar.pack(fill="x", padx=15, pady=(0, 5))

        self.nav_btns = {}
        nav_items = [
            ("clean", "🧹 快取與記憶體優化"),
            ("boot", "🚀 開機加速與工作排程"),
            ("uninstall", "🗑️ 軟體徹底卸載 (Geek)"),
            ("settings", "⚙️ 設定與保護白名單")
        ]

        for key, text in nav_items:
            btn = ctk.CTkButton(
                nav_bar, text=text, font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"),
                fg_color="transparent", text_color=CONFIG.THEME["TEXT_MUTED"], hover_color=CONFIG.THEME["CARD_BG"],
                width=190, height=36, corner_radius=6,
                command=lambda k=key: self.show_page(k)
            )
            btn.pack(side="left", padx=5, pady=4)
            self.nav_btns[key] = btn

        # 主內容區域 (Container)
        self.page_container = ctk.CTkFrame(self, fg_color="transparent")
        self.page_container.pack(fill="both", expand=True, padx=15, pady=5)

        self.build_page_clean()
        self.build_page_boot()
        self.build_page_uninstall()
        self.build_page_settings()

        self.show_page("clean")

    def show_page(self, page_key):
        for key, page in self.pages.items():
            if key == page_key:
                page.pack(fill="both", expand=True)
                self.nav_btns[key].configure(fg_color=CONFIG.THEME["PRIMARY"], text_color=CONFIG.THEME["TEXT_LIGHT"])
            else:
                page.pack_forget()
                self.nav_btns[key].configure(fg_color="transparent", text_color=CONFIG.THEME["TEXT_MUTED"])

    # --------------------------------------------------------------------------
    # 分頁 1：🧹 快取與記憶體優化 (Page Clean)
    # --------------------------------------------------------------------------
    def build_page_clean(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["clean"] = page

        main_container = ctk.CTkFrame(page, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # 左側控制面板 (固定寬度 440px，確保多文字 Checkbox 完全不被截斷)
        left_panel = ctk.CTkFrame(main_container, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10, width=440)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # 底部按鈕與統計卡片 (先 pack 在底部，讓上方 scroll_left 獲得最大彈性高度)
        self.btn_launch = ctk.CTkButton(
            left_panel, text="⚡ 開始一鍵優化", font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color="#2196F3",
            corner_radius=8, height=40, command=self.execute_optimization_flow
        )
        self.btn_launch.pack(side="bottom", fill="x", padx=12, pady=(4, 12))

        stats_card = ctk.CTkFrame(left_panel, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        stats_card.pack(side="bottom", fill="x", padx=12, pady=(4, 6))
        self.lbl_total_stats = ctk.CTkLabel(
            stats_card, text="🧹 暫存已清理容量：0.0 MB\n💾 實體 RAM 已釋出：0.0 MB",
            font=self.sec_title_font, text_color=CONFIG.THEME["SUCCESS"], justify="left"
        )
        self.lbl_total_stats.pack(padx=10, pady=8)

        # 上方可滾動選單區域 (填滿剩餘高度)
        scroll_left = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        scroll_left.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(scroll_left, text="🧹 第一類：無感完全安全清理", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(anchor="w", padx=10, pady=(8, 4))
        ctk.CTkCheckBox(scroll_left, text="清理使用者暫存區 (Temp)", variable=self.var_clean_temp, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="清理崩潰傾印檔與 WER 報告", variable=self.var_clean_crash_wer, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="清理微軟傳遞優化下載快取", variable=self.var_clean_delivery_opt, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="清理開發套件包快取 (pip/uv/npm/Yarn)", variable=self.var_clean_pkg_caches, font=self.default_font).pack(anchor="w", padx=10, pady=4)

        ctk.CTkFrame(scroll_left, fg_color=CONFIG.THEME["BG_DARK"], height=2).pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(scroll_left, text="⚡ 第二類：軟體快取與全碟自動盤點", font=self.title_font, text_color=CONFIG.THEME["WARNING"]).pack(anchor="w", padx=10, pady=(4, 4))
        ctk.CTkCheckBox(scroll_left, text="清理網頁快取 (Chrome / Edge 各 Profile)", variable=self.var_clean_browser, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="清理軟體與 IDE 快取 (VS Code/JetBrains)", variable=self.var_clean_apps, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="🔍 智慧全碟快取自動盤點 (搜尋 > 50MB 快取)", variable=self.var_smart_scan, font=self.default_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="清理顯卡著色器快取 (DirectX / NVIDIA / AMD)", variable=self.var_clean_shader, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="清理檔案總管縮圖快取 (thumbcache_*.db)", variable=self.var_clean_thumbnail, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="清理系統預載歷史 (Prefetch)", variable=self.var_clean_prefetch, font=self.default_font).pack(anchor="w", padx=10, pady=4)

        ctk.CTkFrame(scroll_left, fg_color=CONFIG.THEME["BG_DARK"], height=2).pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(scroll_left, text="⚙️ 處理程序與模擬控制", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=10, pady=(4, 4))
        ctk.CTkCheckBox(scroll_left, text="關閉高記憶體佔用閒置處理程序", variable=self.var_kill_zombie, font=self.default_font).pack(anchor="w", padx=10, pady=4)
        ctk.CTkCheckBox(scroll_left, text="🛡️ 模擬開關 (僅預覽不刪除檔案)", variable=self.var_dry_run, font=self.default_font).pack(anchor="w", padx=10, pady=4)

        lbl_slider_desc = ctk.CTkLabel(scroll_left, text="處理程序記憶體門檻：", font=self.default_font)
        lbl_slider_desc.pack(anchor="w", padx=10, pady=(4, 2))
        self.lbl_unit = ctk.CTkLabel(scroll_left, text=f"當前門檻: {CONFIG.DEFAULT_PROCESS_RAM_LIMIT} MB", font=self.sec_title_font, text_color=CONFIG.THEME["WARNING"])
        self.lbl_unit.pack(anchor="e", padx=10, pady=(0, 2))

        self.ram_slider = ctk.CTkSlider(
            scroll_left, from_=100, to=2000, number_of_steps=38,
            variable=self.var_ram_limit, command=self._on_ram_slider_change,
            progress_color=CONFIG.THEME["PRIMARY"], button_color=CONFIG.THEME["PRIMARY"]
        )
        self.ram_slider.pack(fill="x", padx=10, pady=4)

        # 右側 Console 面板 (與左側控制面板在 main_container 內平行並排)
        right_panel = ctk.CTkFrame(main_container, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
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
    # 分頁 2：🚀 開機加速與工作排程 (Page Boot)
    # --------------------------------------------------------------------------
    def build_page_boot(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["boot"] = page

        card_uptime = ctk.CTkFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        card_uptime.pack(fill="x", pady=(0, 10))

        uptime_text = BootOptimizerEngine.get_last_boot_time_str()
        ctk.CTkLabel(card_uptime, text=f"📊 開機健康度監測：{uptime_text}", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(side="left", padx=15, pady=12)

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
            fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B", width=160,
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
        if not ok: messagebox.showerror("開啟失敗", msg)

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

        file_items = [it for it in visible_items if it["type"] == "file"]
        reg_items = [it for it in visible_items if it["type"] == "registry"]
        task_items = [it for it in visible_items if it["type"] == "task"]

        if file_items:
            sec1_header = ctk.CTkFrame(self.frame_sys_startup_list, fg_color="transparent")
            sec1_header.pack(fill="x", pady=(10, 4))
            ctk.CTkLabel(sec1_header, text="🟢 1. Startup 開機啟動資料夾捷徑區 (直觀且安全刪除/備份)", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(side="left")
            for idx, item in enumerate(file_items):
                self._render_single_startup_row(item, idx)

        if reg_items:
            sec2_header = ctk.CTkFrame(self.frame_sys_startup_list, fg_color="transparent")
            sec2_header.pack(fill="x", pady=(15, 4))
            ctk.CTkLabel(sec2_header, text="🟡 2. Windows 登錄檔 Run 鍵值區 (提供軟性關閉/開啟，不刪除機碼)", font=self.title_font, text_color=CONFIG.THEME["WARNING"]).pack(side="left")
            for idx, item in enumerate(reg_items):
                self._render_single_startup_row(item, idx + 100)

        if task_items:
            sec3_header = ctk.CTkFrame(self.frame_sys_startup_list, fg_color="transparent")
            sec3_header.pack(fill="x", pady=(15, 4))
            ctk.CTkLabel(sec3_header, text="🔵 3. Windows 工作排程器啟動區 (系統背景與定時排程，軟性切換)", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(side="left")
            for idx, item in enumerate(task_items):
                self._render_single_startup_row(item, idx + 200)

    def _render_single_startup_row(self, item, idx):
        row = ctk.CTkFrame(self.frame_sys_startup_list, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        row.pack(fill="x", pady=4)

        chk_var = ctk.BooleanVar(value=False)
        self.startup_check_vars[idx] = (chk_var, item)
        chk = ctk.CTkCheckBox(
            row, text="", variable=chk_var, width=28,
            checkbox_width=18, checkbox_height=18,
            fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
            state="normal" if item["enabled"] else "disabled"
        )
        chk.pack(side="left", padx=(8, 0), pady=10)

        status_text = "🟢 [運行中]" if item["enabled"] else "🛑 [已關閉]"
        status_color = CONFIG.THEME["SUCCESS"] if item["enabled"] else CONFIG.THEME["TEXT_MUTED"]

        frame_left = ctk.CTkFrame(row, fg_color="transparent", width=120)
        frame_left.pack(side="left", padx=(6, 5), pady=8)

        lbl_status = ctk.CTkLabel(frame_left, text=status_text, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=status_color)
        lbl_status.pack(anchor="w")
        lbl_impact = ctk.CTkLabel(frame_left, text=item["impact"], font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["WARNING"])
        lbl_impact.pack(anchor="w")

        frame_info = ctk.CTkFrame(row, fg_color="transparent")
        frame_info.pack(side="left", fill="both", expand=True, padx=5, pady=6)

        title_text = f"✨ {item['friendly_name']}"
        if item.get("scope") == "user": title_text += " [個人帳號]"
        elif item.get("scope") == "common": title_text += " [全機共用]"

        lbl_name = ctk.CTkLabel(frame_info, text=title_text, font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w")
        lbl_name.pack(anchor="w")

        if item.get("is_sys_driver"):
            lbl_sys_warn = ctk.CTkLabel(frame_info, text="⚠️ 系統/驅動必備項目 (建議維持開啟，勿隨意刪除)", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["WARNING"], anchor="w")
            lbl_sys_warn.pack(anchor="w", pady=(1, 0))

        lbl_desc = ctk.CTkLabel(frame_info, text=f"💡 開機用途：{item['description']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["SUCCESS"], anchor="w")
        lbl_desc.pack(anchor="w", pady=(1, 0))

        raw_info = f"登記名稱：{item['raw_name']} | 位置：{item['location']}\n指令：{item['command']}"
        lbl_cmd = ctk.CTkLabel(frame_info, text=raw_info, font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w", justify="left")
        lbl_cmd.pack(anchor="w", pady=(2, 0))

        if item["type"] == "file":
            btn_del_shortcut = ctk.CTkButton(
                row, text="🗑️ 備份並刪除捷徑", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=150, fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
                command=lambda it=item: self._backup_delete_shortcut(it)
            )
            btn_del_shortcut.pack(side="right", padx=10, pady=10)
        else:
            if item["enabled"]:
                btn_txt = "🚫 軟性停用開機啟動"; btn_col = CONFIG.THEME["DANGER"]; btn_hov = "#C0392B"
            else:
                btn_txt = "✅ 復原開啟開機啟動"; btn_col = CONFIG.THEME["SUCCESS"]; btn_hov = "#27AE60"

            btn_toggle = ctk.CTkButton(
                row, text=btn_txt, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=160, fg_color=btn_col, hover_color=btn_hov,
                command=lambda it=item: self._toggle_startup_item(it)
            )
            btn_toggle.pack(side="right", padx=10, pady=10)

        btn_loc = ctk.CTkButton(
            row, text="📂 檔案位置", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            width=100, fg_color=CONFIG.THEME["CARD_BG"], hover_color=CONFIG.THEME["PRIMARY"],
            command=lambda it=item: self._open_startup_item_location(it)
        )
        btn_loc.pack(side="right", padx=(5, 0), pady=10)

    def _open_startup_item_location(self, item):
        ok, msg = BootOptimizerEngine.open_item_location(item)
        if not ok:
            messagebox.showwarning("無法開啟位置", msg)

    def _backup_delete_shortcut(self, item):
        if messagebox.askyesno("備份並刪除捷徑確認", f"確定要將捷徑 [{item['friendly_name']}] 移至安全備份垃圾桶嗎？\n\n這將取消該軟體的開機自動啟動，對軟體本身零影響，隨時可復原。"):
            ok, msg = BootOptimizerEngine.backup_and_delete_shortcut(item)
            if ok:
                messagebox.showinfo("成功刪除捷徑", msg)
                self.load_system_startup_list()
            else: messagebox.showerror("刪除失敗", msg)

    def _batch_disable_checked_items(self):
        checked = [(var, item) for var, item in self.startup_check_vars.values() if var.get() and item["enabled"]]
        if not checked:
            messagebox.showwarning("未選取任何項目", "請先勾選想要停用的開機啟動項目後，再執行批次停用。")
            return
        names = "、".join([item["friendly_name"] for _, item in checked])
        if not messagebox.askyesno("確認批次停用", f"即將停用以下 {len(checked)} 個項目：\n\n{names}\n\n確定執行嗎？"): return
        success_count = 0; fail_msgs = []
        for _, item in checked:
            ok, msg = BootOptimizerEngine.toggle_startup_item_state(item)
            if ok: success_count += 1
            else: fail_msgs.append(f"• {item['friendly_name']}：{msg}")
        result_msg = f"✅ 已成功停用 {success_count} 個項目。"
        if fail_msgs: result_msg += f"\n\n⚠️ 以下項目操作失敗：\n" + "\n".join(fail_msgs)
        messagebox.showinfo("批次停用結果", result_msg)
        self.load_system_startup_list()

    def _toggle_startup_item(self, item):
        success, msg = BootOptimizerEngine.toggle_startup_item_state(item)
        if success:
            messagebox.showinfo("更新成功", msg)
            self.load_system_startup_list()
        else: messagebox.showerror("操作失敗", f"無法修改狀態:\n{msg}")

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

            btn_test = ctk.CTkButton(row_frame, text="🧪 測試", width=70, command=lambda p=item['path'], a=item.get('args',''): self._test_script(p, a))
            btn_test.pack(side="right", padx=6, pady=6)

            btn_del = ctk.CTkButton(row_frame, text="🗑️ 刪除", width=60, fg_color=CONFIG.THEME["DANGER"], command=lambda i=idx: self._delete_custom_script(i))
            btn_del.pack(side="right", padx=6, pady=6)

    def _open_add_script_modal(self):
        AddCustomScriptDialog(self, on_add_callback=self._add_custom_script_item)

    def _add_custom_script_item(self, name, path, args, delay):
        self.custom_scripts.append({"name": name, "path": path, "args": args, "delay": delay})
        BootOptimizerEngine.save_custom_scripts(self.custom_scripts)
        self.refresh_custom_script_list()

    def _delete_custom_script(self, idx):
        if 0 <= idx < len(self.custom_scripts):
            del self.custom_scripts[idx]
            BootOptimizerEngine.save_custom_scripts(self.custom_scripts)
            self.refresh_custom_script_list()

    def _test_script(self, path, args):
        success, msg = BootOptimizerEngine.test_run_script(path, args)
        if success: messagebox.showinfo("測試成功", msg)
        else: messagebox.showerror("測試失敗", msg)

    # --------------------------------------------------------------------------
    # 分頁 3：🗑️ 軟體徹底卸載 (Page Uninstall)
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
            top_bar, text="☑️ 隱藏系統必備元件", variable=self.var_hide_sys_components,
            font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"], command=self.render_uninstall_software_rows
        )
        chk_hide_sys.pack(side="left", padx=10, pady=12)

        btn_reload = ctk.CTkButton(
            top_bar, text="🔄 重新讀取", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            width=110, fg_color=CONFIG.THEME["PRIMARY"], command=self.load_uninstall_software_list
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
        filtered_list = []; total_mb = 0.0

        for item in self.cached_installed_software:
            if hide_sys and item["is_system"]: continue
            if kw and (kw not in item["name"].lower() and kw not in item["publisher"].lower()): continue
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

            badge_text = "🛡️ [系統元件]" if item["is_system"] else "📦 [應用軟體]"
            badge_color = CONFIG.THEME["WARNING"] if item["is_system"] else CONFIG.THEME["PRIMARY"]

            lbl_icon = ctk.CTkLabel(row, text=badge_text, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=badge_color, width=110)
            lbl_icon.pack(side="left", padx=(10, 5), pady=8)

            frame_info = ctk.CTkFrame(row, fg_color="transparent")
            frame_info.pack(side="left", fill="both", expand=True, padx=5, pady=4)

            lbl_name = ctk.CTkLabel(frame_info, text=item["name"], font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w")
            lbl_name.pack(anchor="w")

            size_str = format_size_str(item["size_mb"]) if item["size_mb"] > 0 else "容量未知"
            meta_str = f"發行商：{item['publisher']} | 估算容量：{size_str} | 安裝日期：{item['install_date'] if item['install_date'] else '未知'}"
            lbl_meta = ctk.CTkLabel(frame_info, text=meta_str, font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w")
            lbl_meta.pack(anchor="w")

            btn_uninstall = ctk.CTkButton(
                row, text="🗑️ 卸載並掃蕩殘留", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=150, fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
                command=lambda it=item: self._uninstall_software_flow(it)
            )
            btn_uninstall.pack(side="right", padx=10, pady=8)

            btn_sw_loc = ctk.CTkButton(
                row, text="📂 安裝位置", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=100, fg_color=CONFIG.THEME["CARD_BG"], hover_color=CONFIG.THEME["PRIMARY"],
                command=lambda it=item: self._open_uninstall_item_location(it)
            )
            btn_sw_loc.pack(side="right", padx=(5, 0), pady=8)

    def _open_uninstall_item_location(self, item):
        ok, msg = UninstallerEngine.open_install_location(item)
        if not ok:
            messagebox.showwarning("無法開啟位置", msg)

    def _uninstall_software_flow(self, item):
        sw_name = item["name"]
        un_cmd = item["uninstall_string"]
        inst_loc = item["install_location"]

        if not messagebox.askyesno("確認卸載軟體", f"即將呼叫官方卸載程式進行卸載：\n\n【{sw_name}】\n發行商：{item['publisher']}\n\n確定開始卸載嗎？"):
            return

        ok, msg = UninstallerEngine.execute_uninstall_command(un_cmd)
        if not ok:
            messagebox.showerror("卸載呼叫失敗", msg)
            return

        if messagebox.askyesno("官方卸載精靈啟動", "官方卸載程式已啟動！\n\n請在官方卸載精靈完成後，點擊「是」即可開始掃蕩 AppData / ProgramData 中的殘留資料夾。"):
            leftovers = UninstallerEngine.scan_appdata_leftovers(sw_name, inst_loc)
            if not leftovers:
                messagebox.showinfo("殘留掃蕩結果", f"✅ 【{sw_name}】環境極度乾淨，未發現任何深層殘留資料夾！")
            else:
                l_msg = "\n".join([f"• {p} ({format_size_str(sz)})" for p, sz in leftovers])
                if messagebox.askyesno("發現深層殘留資料夾", f"偵測到以下 {len(leftovers)} 個殘留資料夾：\n\n{l_msg}\n\n確定強制清除這些殘留資料夾嗎？"):
                    del_c = 0
                    for p, _ in leftovers:
                        try:
                            shutil.rmtree(p, ignore_errors=True)
                            del_c += 1
                        except: pass
                    messagebox.showinfo("殘留清理完畢", f"🎉 成功刪除 {del_c} 個深層殘留資料夾！")
            self.load_uninstall_software_list()

    # --------------------------------------------------------------------------
    # 分頁 4：⚙️ 設定與保護白名單 (Page Settings)
    # --------------------------------------------------------------------------
    def build_page_settings(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["settings"] = page

        scroll_set = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        scroll_set.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_set, text="🛡️ 全域安全保護白名單 (絕對禁止清理與刪除)", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(scroll_set, text="💡 提示：本工具內建硬核保護邏輯，包含下列關鍵字之檔案與資料夾將被自動強制跳過，絕不更動系統核心。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=(0, 10))

        # 新增保護關鍵字輸入欄位
        frame_add_kw = ctk.CTkFrame(scroll_set, fg_color="transparent")
        frame_add_kw.pack(fill="x", padx=15, pady=(0, 10))

        self.entry_add_kw = ctk.CTkEntry(frame_add_kw, placeholder_text="輸入自訂保護關鍵字 (例如：mydata / .secret)...", width=340)
        self.entry_add_kw.pack(side="left")

        btn_add_kw = ctk.CTkButton(
            frame_add_kw, text="➕ 新增保護關鍵字", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], hover_color=CONFIG.THEME["SUCCESS_HOVER"], width=150,
            command=self._add_whitelist_keyword
        )
        btn_add_kw.pack(side="left", padx=8)

        btn_reset_kw = ctk.CTkButton(
            frame_add_kw, text="🔄 恢復預設白名單", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["PRIMARY"], hover_color=CONFIG.THEME["PRIMARY_HOVER"], width=150,
            command=self._reset_whitelist_keywords
        )
        btn_reset_kw.pack(side="right")

        self.frame_wl_list = ctk.CTkFrame(scroll_set, fg_color="transparent")
        self.frame_wl_list.pack(fill="x", padx=15, pady=5)

        self.refresh_whitelist_ui()

    def refresh_whitelist_ui(self):
        for widget in self.frame_wl_list.winfo_children(): widget.destroy()
        keywords = load_protected_keywords()

        for kw in keywords:
            row = ctk.CTkFrame(self.frame_wl_list, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
            row.pack(fill="x", pady=3)

            is_default = kw in CONFIG.DEFAULT_PROTECTED_KEYWORDS
            badge = "🔒 [系統預設保護]" if is_default else "👤 [使用者自訂保護]"
            badge_col = CONFIG.THEME["SUCCESS"] if is_default else CONFIG.THEME["PRIMARY"]

            ctk.CTkLabel(row, text=badge, font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=badge_col, width=150).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=kw, font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=10, pady=8)

            if not is_default:
                btn_del = ctk.CTkButton(
                    row, text="🗑️ 移除", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                    width=70, fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
                    command=lambda k=kw: self._remove_whitelist_keyword(k)
                )
                btn_del.pack(side="right", padx=10, pady=6)

    def _add_whitelist_keyword(self):
        kw = self.entry_add_kw.get().strip()
        if not kw:
            messagebox.showwarning("欄位空白", "請輸入要保護的關鍵字！")
            return
        curr = load_protected_keywords()
        if kw.lower() in [k.lower() for k in curr]:
            messagebox.showinfo("關鍵字已存在", f"白名單中已包含此保護關鍵字：{kw}")
            return
        curr.append(kw)
        save_protected_keywords(curr)
        self.entry_add_kw.delete(0, "end")
        self.refresh_whitelist_ui()
        messagebox.showinfo("新增成功", f"已成功新增保護關鍵字：{kw}")

    def _remove_whitelist_keyword(self, kw):
        curr = load_protected_keywords()
        if kw in curr:
            curr.remove(kw)
            save_protected_keywords(curr)
            self.refresh_whitelist_ui()

    def _reset_whitelist_keywords(self):
        if messagebox.askyesno("恢復預設白名單", "確定要清空所有自訂關鍵字，恢復為系統預設保護白名單嗎？"):
            save_protected_keywords(CONFIG.DEFAULT_PROTECTED_KEYWORDS)
            self.refresh_whitelist_ui()

    def _handle_f5_refresh(self):
        self.load_system_startup_list()
        self.load_uninstall_software_list()
        self.append_log("🔄 已觸發 <F5> 熱鍵：系統啟動項與軟體清單已重新整理！", CONFIG.THEME["PRIMARY"])

    def _handle_ctrl_f(self):
        if hasattr(self, 'entry_sw_search'):
            self.show_page("uninstall")
            self.entry_sw_search.focus_set()

    # --------------------------------------------------------------------------
    # 邏輯控制與一鍵優化排程
    # --------------------------------------------------------------------------
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

    def execute_optimization_flow(self):
        self.btn_launch.configure(state="disabled", text="⏳ 優化執行中...")
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])
        self.append_log(f"⏰ 任務啟動時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", CONFIG.THEME["TEXT_LIGHT"])
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])

        is_dry_run = self.var_dry_run.get()
        selected_depth_str = self.var_scan_depth.get()
        max_depth = CONFIG.SCAN_DEPTH_OPTIONS.get(selected_depth_str, 1)

        def _update_progress(val):
            self.after(0, lambda: self.progress_bar.set(val))

        def _thread_task():
            try:
                tot_ram, avail_before, used_before, load_before = get_system_ram_info()
                _update_progress(0.1)
                pending_files = []; pending_pids = []; total_items = 0; freed_ram_from_procs = 0.0

                if self.var_clean_temp.get():
                    res = OptimizerEngine.clean_temp_cache(self.append_log, CONFIG.TEMP_DIR, max_depth=max_depth, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.2)

                if self.var_clean_crash_wer.get():
                    res = OptimizerEngine.clean_crash_dumps_and_wer(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.3)

                if self.var_clean_delivery_opt.get():
                    res = OptimizerEngine.clean_delivery_optimization(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.4)

                if self.var_clean_pkg_caches.get():
                    res = OptimizerEngine.clean_pkg_caches(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.5)

                if self.var_clean_browser.get():
                    res = OptimizerEngine.clean_browser_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.6)

                if self.var_clean_apps.get():
                    res = OptimizerEngine.clean_app_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.7)

                if self.var_smart_scan.get():
                    res = OptimizerEngine.scan_smart_caches(self.append_log, min_size_mb=50.0, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.8)

                if self.var_clean_shader.get():
                    res = OptimizerEngine.clean_shader_caches(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)

                if self.var_clean_thumbnail.get():
                    res = OptimizerEngine.clean_thumbnail_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)

                if self.var_clean_prefetch.get():
                    res = OptimizerEngine.clean_prefetch(self.append_log, CONFIG.PREFETCH_DIR, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.9)

                if self.var_kill_zombie.get():
                    res = OptimizerEngine.kill_zombie_processes(self.append_log, ram_limit_mb=self.var_ram_limit.get(), dry_run=is_dry_run)
                    if is_dry_run: pending_pids.extend(res)
                    else: killed_count, freed_ram_from_procs = res

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
                    self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                    self.after(0, lambda: messagebox.showinfo("優化完成報告", f"一鍵系統優化成功完畢！\n\n🎉 成功釋放實體 RAM: {ram_fmt}\n系統負載已降至 {load_after}%。"))
            except Exception as e:
                self.append_log(f"❌ 執行過程中發生異常: {str(e)}", CONFIG.THEME["DANGER"])
            finally:
                if not is_dry_run or (is_dry_run and total_items == 0):
                    self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 開始一鍵優化"))
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
                    pid = item[0]
                    mem_mb = item[2] if len(item) >= 3 else 0.0
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
                self.append_log(f"🎉 【清理成果】釋出暫存磁碟容量: {disk_fmt} / 實體 RAM: {ram_fmt}！", CONFIG.THEME["SUCCESS"])
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
    except Exception: pass

    app = SystemOptimizerApp()
    app.mainloop()