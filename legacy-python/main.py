#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool) - v5.1.0 可攜環境版
主要功能：
  1. 📊 全碟儲存空間診斷：巨型檔案分析、長期未使用檔案檢測、三階段 SHA-256 重複檔案分析與 Downloads 健檢。
  2. 🧹 快取與記憶體清理：三層安全分級 (🟢安全清理 / 🟡可重建快取 / 🔴進階操作)、大型快取分析器 (Inspector)。
  2. 💾 Working Set 分頁暫時釋放 & 程序獨立管理 (純粹解耦於 engine/memory.py)。
  3. 🚀 開機資料夾直達：雙層 Startup 原生開機資料夾直連與快捷指南。
  4. 🗑️ 軟體徹底卸載：多維度信心分數殘留掃蕩與取消驗證安全防護。
  5. ⚙️ 設定與白名單：動態保護白名單持久化、WCAG 2.1 AA 對比度與無障礙熱鍵。
相依套件：Python 3 標準庫 + CustomTkinter (pip install customtkinter)
執行指令：python main.py
"""

import os
import sys
import datetime
import threading
import shutil
import customtkinter as ctk
from tkinter import messagebox, scrolledtext

from engine.config import CONFIG, format_size_str, load_protected_keywords, save_protected_keywords
from engine.memory import MemoryEngine, get_system_ram_info
from engine.cache_rules import CacheRuleRegistry
from engine.storage_analyzer import StorageAnalyzerEngine
from engine.cache_inspector import CacheInspectorEngine
from engine.optimizer import OptimizerEngine
from engine.boot import BootOptimizerEngine
from engine.uninstaller import UninstallerEngine
from ui.dialogs import PreviewDialog, ResidualsPreviewDialog, AddCustomScriptDialog, StorageAnalyzerDialog

# ==============================================================================
# 系統優化主程式 UI (CustomTkinter 介面)
# ==============================================================================
class SystemOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{CONFIG.APP_NAME} {CONFIG.VERSION}")
        self.geometry("980x760")
        ctk.set_appearance_mode("dark")

        load_protected_keywords()

        self.default_font = ctk.CTkFont(family="Microsoft JhengHei", size=12)
        self.title_font = ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold")
        self.sec_title_font = ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold")

        self.total_freed_disk_mb = 0.0
        self.total_freed_ram_mb = 0.0

        # 全域無障礙與熱鍵綁定 (<F5>, <Ctrl+F>)
        self.bind("<F5>", lambda e: self._handle_f5_refresh())
        self.bind("<Control-f>", lambda e: self._handle_ctrl_f())
        self.bind("<Control-F>", lambda e: self._handle_ctrl_f())

        # 🟢 第一層：安全清理 UI 控制變數 (預設勾選)
        self.var_clean_temp = ctk.BooleanVar(value=True)
        self.var_clean_crash_wer = ctk.BooleanVar(value=True)
        self.var_clean_delivery_opt = ctk.BooleanVar(value=True)
        self.var_clean_pkg_caches = ctk.BooleanVar(value=True)
        self.var_clean_browser = ctk.BooleanVar(value=True)

        # 🟡 第二層：可重建快取 UI 控制變數 (預設不勾選)
        self.var_clean_apps = ctk.BooleanVar(value=False)
        self.var_clean_shader = ctk.BooleanVar(value=False)
        self.var_clean_thumbnail = ctk.BooleanVar(value=False)
        self.var_smart_scan = ctk.BooleanVar(value=False)

        # 🔴 第三層：進階操作 UI 控制變數 (獨立 & 預設不勾選)
        self.var_clean_prefetch = ctk.BooleanVar(value=False)
        self.var_kill_zombie = ctk.BooleanVar(value=False)
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
        self.append_log("💡 提示：本工具使用三層安全防禦架構，未知快取絕不自動刪除，記憶體與背景程序獨立管理。\n---", CONFIG.THEME["TEXT_MUTED"])

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
            ("clean", "🧹 快取與記憶體維護"),
            ("boot", "🚀 開機啟動資料夾直達"),
            ("uninstall", "🗑️ 軟體徹底卸載"),
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
    # 分頁 1：🧹 快取與記憶體維護 (Page Clean - 三層安全架構)
    # --------------------------------------------------------------------------
    def build_page_clean(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["clean"] = page

        main_container = ctk.CTkFrame(page, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # 左側控制面板 (固定寬度 450px)
        left_panel = ctk.CTkFrame(main_container, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10, width=450)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # 底部按鈕與統計卡片
        self.btn_launch = ctk.CTkButton(
            left_panel, text="⚡ 開始執行選定清理", font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], text_color=CONFIG.THEME["TEXT_LIGHT"], hover_color="#2196F3",
            corner_radius=8, height=40, command=self.execute_optimization_flow
        )
        self.btn_launch.pack(side="bottom", fill="x", padx=12, pady=(4, 12))

        stats_card = ctk.CTkFrame(left_panel, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        stats_card.pack(side="bottom", fill="x", padx=12, pady=(4, 6))
        self.lbl_total_stats = ctk.CTkLabel(
            stats_card, text="🧹 暫存已清理容量：0.0 MB\n💾 Working Set 頁面釋放：0.0 MB",
            font=self.sec_title_font, text_color=CONFIG.THEME["SUCCESS"], justify="left"
        )
        self.lbl_total_stats.pack(padx=10, pady=8)

        # 上方可滾動選單區域 (三層安全分級)
        scroll_left = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        scroll_left.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # 🟢 第一層：安全清理
        ctk.CTkLabel(scroll_left, text="🟢 第一層：安全清理 (預設推薦勾選)", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(scroll_left, text="💡 特性：無感安全清理，完全不影響日常使用狀態。", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=10, pady=(0, 4))
        ctk.CTkCheckBox(scroll_left, text="清理使用者暫存區 (Temp)", variable=self.var_clean_temp, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="清理崩潰傾印檔與 WER 報告", variable=self.var_clean_crash_wer, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="清理微軟傳遞優化下載快取", variable=self.var_clean_delivery_opt, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="清理開發套件包快取 (pip/uv/npm/Yarn)", variable=self.var_clean_pkg_caches, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="清理網頁快取 (Chrome/Edge/Brave/Firefox)", variable=self.var_clean_browser, font=self.default_font).pack(anchor="w", padx=10, pady=3)

        ctk.CTkFrame(scroll_left, fg_color=CONFIG.THEME["BG_DARK"], height=2).pack(fill="x", padx=10, pady=8)

        # 🟡 第二層：可重建快取
        ctk.CTkLabel(scroll_left, text="🟡 第二層：可重建快取 (預設不勾選)", font=self.title_font, text_color=CONFIG.THEME["WARNING"]).pack(anchor="w", padx=10, pady=(4, 2))
        ctk.CTkLabel(scroll_left, text="💡 特性：清除後軟體或系統會在需要時自動重新建立。", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=10, pady=(0, 4))
        ctk.CTkCheckBox(scroll_left, text="清理軟體與 IDE 快取 (VS Code/JetBrains)", variable=self.var_clean_apps, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="清理顯卡著色器快取 (DirectX/NVIDIA/AMD)", variable=self.var_clean_shader, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="清理檔案總管縮圖快取 (thumbcache_*.db)", variable=self.var_clean_thumbnail, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="🔍 大型快取分析器 (盤點 > 50MB 未知項目，不自動刪除)", variable=self.var_smart_scan, font=self.default_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=10, pady=3)

        ctk.CTkFrame(scroll_left, fg_color=CONFIG.THEME["BG_DARK"], height=2).pack(fill="x", padx=10, pady=8)

        # 🔴 第三層：進階操作
        ctk.CTkLabel(scroll_left, text="🔴 第三層：進階操作 (獨立且謹慎執行)", font=self.title_font, text_color=CONFIG.THEME["DANGER"]).pack(anchor="w", padx=10, pady=(4, 2))
        ctk.CTkLabel(scroll_left, text="💡 提示：包含 Prefetch 與記憶體獨立維護，請瞭解用途後選擇。", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=10, pady=(0, 4))
        
        ctk.CTkCheckBox(scroll_left, text="清理系統預載歷史 (Prefetch - 不建議日常頻繁清理)", variable=self.var_clean_prefetch, font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=10, pady=3)

        btn_trim_ws = ctk.CTkButton(
            scroll_left, text="⚙️ 縮減背景 Working Set 分頁 (記憶體暫時釋放)", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["CARD_BG"], hover_color=CONFIG.THEME["PRIMARY"], height=32,
            command=self._execute_working_set_trim_only
        )
        btn_trim_ws.pack(fill="x", padx=10, pady=6)

        ctk.CTkCheckBox(scroll_left, text="關閉高佔用閒置程序", variable=self.var_kill_zombie, font=self.default_font).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(scroll_left, text="🛡️ 模擬開關 (僅預覽明細，不真實刪除或結束程序)", variable=self.var_dry_run, font=self.default_font, text_color=CONFIG.THEME["SUCCESS"]).pack(anchor="w", padx=10, pady=3)

        lbl_slider_desc = ctk.CTkLabel(scroll_left, text="閒置程序記憶體判定門檻：", font=self.default_font)
        lbl_slider_desc.pack(anchor="w", padx=10, pady=(4, 2))
        self.lbl_unit = ctk.CTkLabel(scroll_left, text=f"當前門檻: {CONFIG.DEFAULT_PROCESS_RAM_LIMIT} MB", font=self.sec_title_font, text_color=CONFIG.THEME["WARNING"])
        self.lbl_unit.pack(anchor="e", padx=10, pady=(0, 2))

        self.ram_slider = ctk.CTkSlider(
            scroll_left, from_=100, to=2000, number_of_steps=38,
            variable=self.var_ram_limit, command=self._on_ram_slider_change,
            progress_color=CONFIG.THEME["PRIMARY"], button_color=CONFIG.THEME["PRIMARY"]
        )
        self.ram_slider.pack(fill="x", padx=10, pady=4)

        ctk.CTkFrame(scroll_left, fg_color=CONFIG.THEME["BG_DARK"], height=2).pack(fill="x", padx=10, pady=8)

        btn_storage_analyzer = ctk.CTkButton(
            scroll_left, text="📊 啟動全碟儲存空間分析器 (巨型檔/重複檔/Downloads健檢)", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["ACCENT"], hover_color="#8B5CF6", height=36,
            command=self._launch_storage_analyzer_modal
        )
        btn_storage_analyzer.pack(fill="x", padx=10, pady=(4, 8))

        # 右側 Console 面板
        right_panel = ctk.CTkFrame(main_container, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="🖥️ 執行過程即時記錄 Console", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=15, pady=(12, 5))
        log_frame = ctk.CTkFrame(right_panel, fg_color="#111115", corner_radius=8)
        log_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.log_display = scrolledtext.ScrolledText(
            log_frame, bg="#111115", fg=CONFIG.THEME["TEXT_LIGHT"], font=("Consolas", 11),
            relief="flat", wrap="word", borderwidth=0, highlightthickness=0
        )
        self.log_display.pack(fill="both", expand=True, padx=10, pady=10)
        for key, color in CONFIG.THEME.items():
            self.log_display.tag_config(color, foreground=color)

    def _execute_working_set_trim_only(self):
        """獨立執行 Working Set 頁面縮減，絕不安裝或混合刪除檔案"""
        def _bg_trim():
            MemoryEngine.trim_working_set(self.append_log)
        threading.Thread(target=_bg_trim, daemon=True).start()

    def _launch_storage_analyzer_modal(self):
        """啟動全碟儲存空間診斷對話框 (巨型檔 / 長期未使用 / 三階段 SHA-256 重複檔 / Downloads 健檢)"""
        self.append_log("📊 [全碟空間診斷] 開始收集巨型檔案、長期未使用檔案、SHA-256 重複檔案與 Downloads 健檢資料...", CONFIG.THEME["PRIMARY"])
        def _bg_scan():
            large_files = StorageAnalyzerEngine.analyze_large_files(self.append_log, min_size_mb=500.0)
            aged_files = StorageAnalyzerEngine.analyze_aged_files(self.append_log, min_size_mb=100.0, min_days=180)
            dup_groups = StorageAnalyzerEngine.analyze_duplicate_files(self.append_log)
            dl_health = StorageAnalyzerEngine.analyze_downloads_health(self.append_log)
            self.after(0, lambda: StorageAnalyzerDialog(self, large_files, aged_files, dup_groups, dl_health))
        threading.Thread(target=_bg_scan, daemon=True).start()

    # --------------------------------------------------------------------------
    # 分頁 2：🚀 開機啟動資料夾直達 (Page Boot)
    # --------------------------------------------------------------------------
    def build_page_boot(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["boot"] = page

        card_uptime = ctk.CTkFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        card_uptime.pack(fill="x", pady=(0, 15))

        uptime_text = BootOptimizerEngine.get_last_boot_time_str()
        ctk.CTkLabel(card_uptime, text=f"📊 系統運行監測：{uptime_text}", font=self.title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(side="left", padx=20, pady=15)

        scroll_boot = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        scroll_boot.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_boot, text="🚀 Windows 開機啟動資料夾直達工具", font=ctk.CTkFont(family="Microsoft JhengHei", size=16, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(scroll_boot, text="💡 簡單、直覺、極致安全。直接引導跳轉至 Windows 原生開機啟動資料夾，輕鬆管理與清理開機自動啟動之軟體與捷徑。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=20, pady=(0, 20))

        # 卡片 1：個人啟動資料夾
        card_user = ctk.CTkFrame(scroll_boot, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        card_user.pack(fill="x", padx=20, pady=(0, 15))

        user_info = ctk.CTkFrame(card_user, fg_color="transparent")
        user_info.pack(side="left", fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(user_info, text="👤 【個人】開機啟動資料夾 (shell:startup)", font=self.sec_title_font, text_color=CONFIG.THEME["SUCCESS"]).pack(anchor="w")
        ctk.CTkLabel(user_info, text="適用範圍：僅針對當前登入的使用者帳號生效，最常用於個人軟體與開機自動執行捷徑。", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(anchor="w", pady=(4, 2))
        
        user_path = os.path.join(CONFIG.USER_HOME, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        ctk.CTkLabel(user_info, text=f"實體路徑：{user_path}", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w")

        btn_open_user = ctk.CTkButton(
            card_user, text="📂 一鍵開啟【個人】啟動資料夾", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], hover_color=CONFIG.THEME["SUCCESS_HOVER"], height=42, width=220,
            command=lambda: self._open_startup_dir("user")
        )
        btn_open_user.pack(side="right", padx=20, pady=15)

        # 卡片 2：全機共用啟動資料夾
        card_common = ctk.CTkFrame(scroll_boot, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        card_common.pack(fill="x", padx=20, pady=(0, 15))

        common_info = ctk.CTkFrame(card_common, fg_color="transparent")
        common_info.pack(side="left", fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(common_info, text="💻 【全機共用】開機啟動資料夾 (shell:common startup)", font=self.sec_title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w")
        ctk.CTkLabel(common_info, text="適用範圍：針對這台電腦上的所有使用者帳號皆生效，常用於系統級共用軟體。", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(anchor="w", pady=(4, 2))
        
        common_path = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"
        ctk.CTkLabel(common_info, text=f"實體路徑：{common_path}", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w")

        btn_open_common = ctk.CTkButton(
            card_common, text="📂 一鍵開啟【全機共用】啟動資料夾", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"),
            fg_color=CONFIG.THEME["PRIMARY"], hover_color=CONFIG.THEME["PRIMARY_HOVER"], height=42, width=240,
            command=lambda: self._open_startup_dir("common")
        )
        btn_open_common.pack(side="right", padx=20, pady=15)

        # 卡片 3：操作指南小貼士
        card_tips = ctk.CTkFrame(scroll_boot, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        card_tips.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(card_tips, text="💡 快捷使用小技巧", font=self.sec_title_font, text_color=CONFIG.THEME["WARNING"]).pack(anchor="w", padx=20, pady=(15, 6))
        ctk.CTkLabel(card_tips, text="• ➕ 新增開機自動執行：開啟資料夾後，將想要開機自動開啟的軟體捷徑 (.lnk) 複製貼上進去即可。", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(anchor="w", padx=20, pady=3)
        ctk.CTkLabel(card_tips, text="• 🗑️ 取消開機自動執行：開啟資料夾後，直接將不想開機啟動的捷徑檔案刪除即可。", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(anchor="w", padx=20, pady=(3, 15))

    def _open_startup_dir(self, scope):
        ok, msg = BootOptimizerEngine.open_startup_folder(scope)
        if not ok: messagebox.showerror("開啟失敗", msg)

    # --------------------------------------------------------------------------
    # 分頁 3：🗑️ 軟體徹底卸載 (Page Uninstall)
    # --------------------------------------------------------------------------
    def build_page_uninstall(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["uninstall"] = page

        top_bar = ctk.CTkFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top_bar, text="🗑️ Windows 軟體徹底卸載庫", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(side="left", padx=15, pady=12)

        self.entry_sw_search = ctk.CTkEntry(top_bar, placeholder_text="🔍 搜尋已安裝軟體名稱...", width=240)
        self.entry_sw_search.pack(side="left", padx=10, pady=10)
        self.entry_sw_search.bind("<KeyRelease>", self._on_sw_search_change)

        chk_hide_sys = ctk.CTkCheckBox(
            top_bar, text="🛡️ 隱藏系統必備與驅動元件", variable=self.var_hide_sys_components,
            font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"], command=self.render_software_list
        )
        chk_hide_sys.pack(side="left", padx=10, pady=10)

        btn_refresh_sw = ctk.CTkButton(
            top_bar, text="🔄 重新整理", width=90, fg_color=CONFIG.THEME["PRIMARY"],
            hover_color=CONFIG.THEME["PRIMARY_HOVER"], command=self.load_uninstall_software_list
        )
        btn_refresh_sw.pack(side="right", padx=15, pady=10)

        self.scroll_uninstall = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        self.scroll_uninstall.pack(fill="both", expand=True)

        self.load_uninstall_software_list()

    def load_uninstall_software_list(self):
        for widget in self.scroll_uninstall.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.scroll_uninstall, text="⏳ 正在盤點 Windows 已安裝軟體庫，請稍候...", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=15)

        def _bg_load():
            sw_list = UninstallerEngine.get_installed_software_list()
            self.after(0, lambda: self._on_software_list_loaded(sw_list))
        threading.Thread(target=_bg_load, daemon=True).start()

    def _on_software_list_loaded(self, sw_list):
        self.cached_installed_software = sw_list
        self.render_software_list()

    def _on_sw_search_change(self, event=None):
        self.render_software_list()

    def render_software_list(self):
        for widget in self.scroll_uninstall.winfo_children(): widget.destroy()
        if not self.cached_installed_software:
            ctk.CTkLabel(self.scroll_uninstall, text="未找到任何已安裝的第三方軟體。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=15)
            return

        kw = self.entry_sw_search.get().strip().lower()
        hide_sys = self.var_hide_sys_components.get()

        filtered = [
            it for it in self.cached_installed_software
            if (not hide_sys or not it["is_system"]) and (not kw or kw in it["name"].lower() or kw in it["publisher"].lower())
        ]

        ctk.CTkLabel(self.scroll_uninstall, text=f"📊 共定位 {len(filtered)} 個已安裝應用軟體", font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=(10, 6))

        for item in filtered:
            row = ctk.CTkFrame(self.scroll_uninstall, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
            row.pack(fill="x", padx=15, pady=4)

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            title_text = f"📦 {item['name']}"
            if item["is_system"]: title_text += " [系統/驅動元件]"
            ctk.CTkLabel(info_frame, text=title_text, font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w").pack(anchor="w")

            meta_text = f"發行商：{item['publisher']} | 容量：{format_size_str(item['size_mb'])} | 安裝日期：{item['install_date'] if item['install_date'] else '未知'}"
            ctk.CTkLabel(info_frame, text=meta_text, font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w").pack(anchor="w", pady=(2, 0))

            btn_uninstall = ctk.CTkButton(
                row, text="🗑️ 卸載軟體", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=110, fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
                command=lambda it=item: self._uninstall_software_flow(it)
            )
            btn_uninstall.pack(side="right", padx=10, pady=10)

            btn_open_loc = ctk.CTkButton(
                row, text="📂 安裝位置", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=100, fg_color=CONFIG.THEME["CARD_BG"], hover_color=CONFIG.THEME["PRIMARY"],
                command=lambda it=item: self._open_software_install_location(it)
            )
            btn_open_loc.pack(side="right", padx=(5, 0), pady=10)

    def _open_software_install_location(self, item):
        ok, msg = UninstallerEngine.open_install_location(item)
        if not ok:
            messagebox.showwarning("無法開啟位置", msg)

    def _uninstall_software_flow(self, item):
        sw_name = item["name"]
        un_cmd = item["uninstall_string"]
        inst_loc = item["install_location"]
        publisher = item["publisher"]

        if not messagebox.askyesno("確認卸載軟體", f"即將呼叫官方卸載程式進行卸載：\n\n【{sw_name}】\n發行商：{publisher}\n\n確定開始卸載嗎？"):
            return

        ok, msg = UninstallerEngine.execute_uninstall_command(un_cmd)
        if not ok:
            messagebox.showerror("卸載呼叫失敗", msg)
            return

        # 關鍵安全防護：防護使用者取消官方卸載時誤刪資料
        still_exists = UninstallerEngine.is_software_still_installed(sw_name)
        if still_exists:
            messagebox.showinfo("卸載未完成", f"官方卸載精靈已被取消或並未真正完成。\n\n【{sw_name}】依然登記於系統註冊表中，已安全終止後續殘留掃蕩。")
            return

        # 多維度信心分數殘留資料夾預覽
        candidates = UninstallerEngine.scan_appdata_leftovers_with_confidence(sw_name, publisher, inst_loc)
        if not candidates:
            messagebox.showinfo("殘留掃蕩結果", f"✅ 【{sw_name}】環境極度乾淨，未發現任何深層殘留資料夾！")
            self.load_uninstall_software_list()
            return

        def _do_real_delete_residuals(selected_paths):
            deleted_count = 0
            failed_paths = []
            for path in selected_paths:
                try:
                    shutil.rmtree(path)
                    deleted_count += 1
                except Exception:
                    failed_paths.append(path)

            result_message = f"成功刪除 {deleted_count} 個深層殘留資料夾。"
            if failed_paths:
                result_message += f"\n\n⚠️ {len(failed_paths)} 個項目未能刪除，可能仍被使用或權限不足：\n" + "\n".join(failed_paths)
            messagebox.showinfo("殘留清理完成", result_message)
            self.load_uninstall_software_list()

        ResidualsPreviewDialog(self, sw_name, candidates, _do_real_delete_residuals)

    # --------------------------------------------------------------------------
    # 分頁 4：⚙️ 設定與保護白名單 (Page Settings)
    # --------------------------------------------------------------------------
    def build_page_settings(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["settings"] = page

        scroll_set = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        scroll_set.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_set, text="⚙️ 工具設定與保護白名單管理", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(scroll_set, text="💡 提示：本區用於管理清理防禦白名單關鍵字。凡檔名或目錄包含此白名單關鍵字者，工具將 100% 絕對防護跳過不予清理。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=20, pady=(0, 15))

        card_add = ctk.CTkFrame(scroll_set, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        card_add.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(card_add, text="➕ 新增保護關鍵字：", font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=15, pady=15)
        self.entry_add_kw = ctk.CTkEntry(card_add, placeholder_text="例如：my_backup / project_a", width=260)
        self.entry_add_kw.pack(side="left", padx=5, pady=15)

        btn_add_kw = ctk.CTkButton(
            card_add, text="加入白名單", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], hover_color="#27AE60", width=110,
            command=self._add_whitelist_keyword
        )
        btn_add_kw.pack(side="left", padx=10, pady=15)

        card_list = ctk.CTkFrame(scroll_set, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        card_list.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        top_list_bar = ctk.CTkFrame(card_list, fg_color="transparent")
        top_list_bar.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(top_list_bar, text="🛡️ 目前保護之白名單關鍵字：", font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left")

        btn_reset = ctk.CTkButton(
            top_list_bar, text="恢復系統預設", font=ctk.CTkFont(family="Microsoft JhengHei", size=11),
            fg_color=CONFIG.THEME["WARNING"], hover_color="#D68910", width=100, height=26,
            command=self._reset_whitelist_keywords
        )
        btn_reset.pack(side="right")

        self.frame_whitelist_tags = ctk.CTkFrame(card_list, fg_color="transparent")
        self.frame_whitelist_tags.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.refresh_whitelist_ui()

    def refresh_whitelist_ui(self):
        for widget in self.frame_whitelist_tags.winfo_children():
            widget.destroy()

        curr_keywords = load_protected_keywords()
        for kw in curr_keywords:
            tag_frame = ctk.CTkFrame(self.frame_whitelist_tags, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
            tag_frame.pack(side="left", padx=4, pady=4)
            ctk.CTkLabel(tag_frame, text=f"🛡️ {kw}", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=(10, 5), pady=6)
            btn_del = ctk.CTkButton(
                tag_frame, text="❌", width=22, height=22, fg_color="transparent",
                hover_color=CONFIG.THEME["DANGER"], text_color=CONFIG.THEME["TEXT_MUTED"],
                command=lambda k=kw: self._remove_whitelist_keyword(k)
            )
            btn_del.pack(side="left", padx=(0, 6), pady=6)

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

    # 分頁 3：🗑️ 軟體徹底卸載 (Page Uninstall)
    # --------------------------------------------------------------------------
    def build_page_uninstall(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["uninstall"] = page

        top_bar = ctk.CTkFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top_bar, text="🗑️ Windows 軟體徹底卸載庫", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(side="left", padx=15, pady=12)

        self.entry_sw_search = ctk.CTkEntry(top_bar, placeholder_text="🔍 搜尋已安裝軟體名稱...", width=240)
        self.entry_sw_search.pack(side="left", padx=10, pady=10)
        self.entry_sw_search.bind("<KeyRelease>", self._on_sw_search_change)

        chk_hide_sys = ctk.CTkCheckBox(
            top_bar, text="🛡️ 隱藏系統必備與驅動元件", variable=self.var_hide_sys_components,
            font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"], command=self.render_software_list
        )
        chk_hide_sys.pack(side="left", padx=10, pady=10)

        btn_refresh_sw = ctk.CTkButton(
            top_bar, text="🔄 重新整理", width=90, fg_color=CONFIG.THEME["PRIMARY"],
            hover_color=CONFIG.THEME["PRIMARY_HOVER"], command=self.load_uninstall_software_list
        )
        btn_refresh_sw.pack(side="right", padx=15, pady=10)

        self.scroll_uninstall = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        self.scroll_uninstall.pack(fill="both", expand=True)

        self.load_uninstall_software_list()

    def load_uninstall_software_list(self):
        for widget in self.scroll_uninstall.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.scroll_uninstall, text="⏳ 正在盤點 Windows 已安裝軟體庫，請稍候...", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=15)
        
        def _bg_load():
            sw_list = UninstallerEngine.get_installed_software_list()
            self.after(0, lambda: self._on_software_list_loaded(sw_list))
        threading.Thread(target=_bg_load, daemon=True).start()

    def _on_software_list_loaded(self, sw_list):
        self.cached_installed_software = sw_list
        self.render_software_list()

    def _on_sw_search_change(self, event=None):
        self.render_software_list()

    def render_software_list(self):
        for widget in self.scroll_uninstall.winfo_children(): widget.destroy()
        if not self.cached_installed_software:
            ctk.CTkLabel(self.scroll_uninstall, text="未找到任何已安裝的第三方軟體。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=15)
            return

        kw = self.entry_sw_search.get().strip().lower()
        hide_sys = self.var_hide_sys_components.get()

        filtered = [
            it for it in self.cached_installed_software
            if (not hide_sys or not it["is_system"]) and (not kw or kw in it["name"].lower() or kw in it["publisher"].lower())
        ]

        ctk.CTkLabel(self.scroll_uninstall, text=f"📊 共定位 {len(filtered)} 個已安裝應用軟體", font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=15, pady=(10, 6))

        for item in filtered:
            row = ctk.CTkFrame(self.scroll_uninstall, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
            row.pack(fill="x", padx=15, pady=4)

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            title_text = f"📦 {item['name']}"
            if item["is_system"]: title_text += " [系統/驅動元件]"
            ctk.CTkLabel(info_frame, text=title_text, font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w").pack(anchor="w")

            meta_text = f"發行商：{item['publisher']} | 容量：{format_size_str(item['size_mb'])} | 安裝日期：{item['install_date'] if item['install_date'] else '未知'}"
            ctk.CTkLabel(info_frame, text=meta_text, font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w").pack(anchor="w", pady=(2, 0))

            btn_uninstall = ctk.CTkButton(
                row, text="🗑️ 卸載軟體", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=110, fg_color=CONFIG.THEME["DANGER"], hover_color="#C0392B",
                command=lambda it=item: self._uninstall_software_flow(it)
            )
            btn_uninstall.pack(side="right", padx=10, pady=10)

            btn_open_loc = ctk.CTkButton(
                row, text="📂 安裝位置", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
                width=100, fg_color=CONFIG.THEME["CARD_BG"], hover_color=CONFIG.THEME["PRIMARY"],
                command=lambda it=item: self._open_software_install_location(it)
            )
            btn_open_loc.pack(side="right", padx=(5, 0), pady=10)

    def _open_software_install_location(self, item):
        ok, msg = UninstallerEngine.open_install_location(item)
        if not ok:
            messagebox.showwarning("無法開啟位置", msg)

    def _uninstall_software_flow(self, item):
        sw_name = item["name"]
        un_cmd = item["uninstall_string"]
        inst_loc = item["install_location"]
        publisher = item["publisher"]

        if not messagebox.askyesno("確認卸載軟體", f"即將呼叫官方卸載程式進行卸載：\n\n【{sw_name}】\n發行商：{publisher}\n\n確定開始卸載嗎？"):
            return

        ok, msg = UninstallerEngine.execute_uninstall_command(un_cmd)
        if not ok:
            messagebox.showerror("卸載呼叫失敗", msg)
            return

        # 關鍵安全防護：防護使用者取消官方卸載時誤刪資料
        still_exists = UninstallerEngine.is_software_still_installed(sw_name)
        if still_exists:
            messagebox.showinfo("卸載未完成", f"官方卸載精靈已被取消或並未真正完成。\n\n【{sw_name}】依然登記於系統註冊表中，已安全終止後續殘留掃蕩。")
            return

        # 多維度信心分數殘留資料夾預覽
        candidates = UninstallerEngine.scan_appdata_leftovers_with_confidence(sw_name, publisher, inst_loc)
        if not candidates:
            messagebox.showinfo("殘留掃蕩結果", f"✅ 【{sw_name}】環境極度乾淨，未發現任何深層殘留資料夾！")
            self.load_uninstall_software_list()
            return

        def _do_real_delete_residuals(selected_paths):
            deleted_count = 0
            failed_paths = []
            for path in selected_paths:
                try:
                    shutil.rmtree(path)
                    deleted_count += 1
                except Exception:
                    failed_paths.append(path)

            result_message = f"成功刪除 {deleted_count} 個深層殘留資料夾。"
            if failed_paths:
                result_message += f"\n\n⚠️ {len(failed_paths)} 個項目未能刪除，可能仍被使用或權限不足：\n" + "\n".join(failed_paths)
            messagebox.showinfo("殘留清理完成", result_message)
            self.load_uninstall_software_list()

        ResidualsPreviewDialog(self, sw_name, candidates, _do_real_delete_residuals)

    # --------------------------------------------------------------------------
    # 分頁 4：⚙️ 設定與保護白名單 (Page Settings)
    # --------------------------------------------------------------------------
    def build_page_settings(self):
        page = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.pages["settings"] = page

        scroll_set = ctk.CTkScrollableFrame(page, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=10)
        scroll_set.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_set, text="⚙️ 工具設定與保護白名單管理", font=self.title_font, text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(scroll_set, text="💡 提示：本區用於管理清理防禦白名單關鍵字。凡檔名或目錄包含此白名單關鍵字者，工具將 100% 絕對防護跳過不予清理。", font=self.default_font, text_color=CONFIG.THEME["TEXT_MUTED"]).pack(anchor="w", padx=20, pady=(0, 15))

        card_add = ctk.CTkFrame(scroll_set, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        card_add.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(card_add, text="➕ 新增保護關鍵字：", font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=15, pady=15)
        self.entry_add_kw = ctk.CTkEntry(card_add, placeholder_text="例如：my_backup / project_a", width=260)
        self.entry_add_kw.pack(side="left", padx=5, pady=15)

        btn_add_kw = ctk.CTkButton(
            card_add, text="加入白名單", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"),
            fg_color=CONFIG.THEME["SUCCESS"], hover_color="#27AE60", width=110,
            command=self._add_whitelist_keyword
        )
        btn_add_kw.pack(side="left", padx=10, pady=15)

        card_list = ctk.CTkFrame(scroll_set, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        card_list.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        top_list_bar = ctk.CTkFrame(card_list, fg_color="transparent")
        top_list_bar.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(top_list_bar, text="🛡️ 目前保護之白名單關鍵字：", font=self.sec_title_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left")

        btn_reset = ctk.CTkButton(
            top_list_bar, text="恢復系統預設", font=ctk.CTkFont(family="Microsoft JhengHei", size=11),
            fg_color=CONFIG.THEME["WARNING"], hover_color="#D68910", width=100, height=26,
            command=self._reset_whitelist_keywords
        )
        btn_reset.pack(side="right")

        self.frame_whitelist_tags = ctk.CTkFrame(card_list, fg_color="transparent")
        self.frame_whitelist_tags.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.refresh_whitelist_ui()

    def refresh_whitelist_ui(self):
        for widget in self.frame_whitelist_tags.winfo_children():
            widget.destroy()

        curr_keywords = load_protected_keywords()
        for kw in curr_keywords:
            tag_frame = ctk.CTkFrame(self.frame_whitelist_tags, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
            tag_frame.pack(side="left", padx=4, pady=4)
            ctk.CTkLabel(tag_frame, text=f"🛡️ {kw}", font=self.default_font, text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=(10, 5), pady=6)
            btn_del = ctk.CTkButton(
                tag_frame, text="❌", width=22, height=22, fg_color="transparent",
                hover_color=CONFIG.THEME["DANGER"], text_color=CONFIG.THEME["TEXT_MUTED"],
                command=lambda k=kw: self._remove_whitelist_keyword(k)
            )
            btn_del.pack(side="left", padx=(0, 6), pady=6)

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
        self.load_uninstall_software_list()
        self.append_log("🔄 已觸發 <F5> 熱鍵：已重新整理軟體庫清單！", CONFIG.THEME["PRIMARY"])

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
        self.lbl_total_stats.configure(text=f"🧹 暫存已清理容量：{disk_str}\n💾 Working Set 頁面釋放：{ram_str}")

    def execute_optimization_flow(self):
        self.btn_launch.configure(state="disabled", text="⏳ 清理執行中...")
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])
        self.append_log(f"⏰ 任務啟動時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", CONFIG.THEME["TEXT_LIGHT"])
        self.append_log("==================================================", CONFIG.THEME["TEXT_MUTED"])

        is_dry_run = self.var_dry_run.get()
        selected_depth_str = self.var_scan_depth.get()
        max_depth = CONFIG.SCAN_DEPTH_OPTIONS.get(selected_depth_str, 1)
        selected_actions = {
            "clean_temp": self.var_clean_temp.get(),
            "clean_crash_wer": self.var_clean_crash_wer.get(),
            "clean_delivery_opt": self.var_clean_delivery_opt.get(),
            "clean_pkg_caches": self.var_clean_pkg_caches.get(),
            "clean_browser": self.var_clean_browser.get(),
            "clean_apps": self.var_clean_apps.get(),
            "clean_shader": self.var_clean_shader.get(),
            "clean_thumbnail": self.var_clean_thumbnail.get(),
            "smart_scan": self.var_smart_scan.get(),
            "clean_prefetch": self.var_clean_prefetch.get(),
            "kill_zombie": self.var_kill_zombie.get(),
            "ram_limit": self.var_ram_limit.get(),
        }

        def _update_progress(val):
            self.after(0, lambda: self.progress_bar.set(val))

        def _thread_task():
            try:
                tot_ram, avail_before, used_before, load_before = get_system_ram_info()
                _update_progress(0.1)
                pending_files = []; pending_pids = []; freed_ram_from_procs = 0.0

                # 🟢 第一層：安全清理
                if selected_actions["clean_temp"]:
                    res = OptimizerEngine.clean_temp_cache(self.append_log, CONFIG.TEMP_DIR, max_depth=max_depth, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.2)

                if selected_actions["clean_crash_wer"]:
                    res = OptimizerEngine.clean_crash_dumps_and_wer(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.3)

                if selected_actions["clean_delivery_opt"]:
                    res = OptimizerEngine.clean_delivery_optimization(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.4)

                if selected_actions["clean_pkg_caches"]:
                    res = OptimizerEngine.clean_pkg_caches(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.5)

                if selected_actions["clean_browser"]:
                    res = OptimizerEngine.clean_browser_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.6)

                # 🟡 第二層：可重建快取
                if selected_actions["clean_apps"]:
                    res = OptimizerEngine.clean_app_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.7)

                if selected_actions["clean_shader"]:
                    res = OptimizerEngine.clean_shader_caches(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)

                if selected_actions["clean_thumbnail"]:
                    res = OptimizerEngine.clean_thumbnail_cache(self.append_log, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)

                if selected_actions["smart_scan"]:
                    CacheInspectorEngine.inspect_large_caches(self.append_log, min_size_mb=50.0)
                _update_progress(0.8)

                # 🔴 第三層：進階項目 (Prefetch)
                if selected_actions["clean_prefetch"]:
                    res = OptimizerEngine.clean_prefetch(self.append_log, CONFIG.PREFETCH_DIR, dry_run=is_dry_run)
                    if is_dry_run: pending_files.extend(res)
                _update_progress(0.9)

                # 閒置程序關閉 (獨立勾選)
                if selected_actions["kill_zombie"]:
                    high_procs = MemoryEngine.inspect_high_ram_processes(ram_limit_mb=selected_actions["ram_limit"])
                    if is_dry_run: pending_pids.extend(high_procs)
                    else:
                        for pid, proc_name, mem_mb in high_procs:
                            ok, freed_mb = MemoryEngine.terminate_process_by_pid(pid, proc_name, self.append_log)
                            if ok: freed_ram_from_procs += freed_mb

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
                        self.append_log(f"📊 [模擬統計] 預計清理 {len(pending_files)} 個檔案，擬選擇性關閉 {len(pending_pids)} 個閒置程序 (約 {est_proc_ram_fmt})。", CONFIG.THEME["TEXT_LIGHT"])
                        
                        def _reset_launch_btn():
                            self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 開始執行選定清理"))
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
                    OptimizerEngine.force_python_gc(self.append_log)
                    _update_progress(1.0)
                    tot_ram, avail_after, used_after, load_after = get_system_ram_info()
                    ram_diff_mb = avail_after - avail_before
                    final_freed_ram_mb = max(ram_diff_mb, freed_ram_from_procs)
                    ram_fmt = format_size_str(final_freed_ram_mb)

                    self.after(0, lambda: self.update_cumulative_stats(freed_ram_mb=final_freed_ram_mb))
                    self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                    self.append_log(f"🎉 清理成功完畢！系統 RAM 負載已降至 {load_after}%。", CONFIG.THEME["SUCCESS"])
                    self.append_log("==================================================", CONFIG.THEME["SUCCESS"])
                    self.after(0, lambda: messagebox.showinfo("清理完成報告", f"選定項目清理成功完畢！\n\n系統 RAM 負載已降至 {load_after}%。"))
            except Exception as e:
                self.append_log(f"❌ 執行過程中發生異常: {str(e)}", CONFIG.THEME["DANGER"])
            finally:
                if not is_dry_run or (is_dry_run and total_items == 0):
                    self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 開始執行選定清理"))
                    self.after(2000, lambda: self.progress_bar.set(0))

        def _real_delete_thread(files, pids, avail_before, load_before):
            try:
                self.append_log("\n⚡ 使用者授權完成，開始執行真實檔案清理與程序關閉...", CONFIG.THEME["DANGER"])

                # 二次程序鎖定確認 (防範中途開啟軟體)
                locked_procs = set()
                for rule in CacheRuleRegistry.get_default_rules():
                    is_locked, matched = CacheRuleRegistry.check_running_app_locks(rule)
                    if is_locked:
                        locked_procs.update(matched)
                if locked_procs:
                    self.append_log(f"⚠️ 偵測到應用程式中途啟動 ({', '.join(locked_procs)})，為保護資料完整性將為您安全自動跳過相關快取。", CONFIG.THEME["WARNING"])

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
                for item in pids:
                    pid = item[0]
                    proc_name = item[1]
                    ok, freed_mb = MemoryEngine.terminate_process_by_pid(pid, proc_name, self.append_log)
                    if ok: killed_count += 1; freed_ram_proc += freed_mb

                self.append_log(f"✅ 清理完成！成功刪除 {deleted_count} 個檔案，手動關閉 {killed_count} 個程序。", CONFIG.THEME["SUCCESS"])
                OptimizerEngine.force_python_gc(self.append_log)
                _update_progress(1.0)

                tot_ram, avail_after, used_after, load_after = get_system_ram_info()
                ram_diff_mb = avail_after - avail_before
                final_freed_ram_mb = max(ram_diff_mb, freed_ram_proc)
                disk_mb = deleted_bytes / (1024 * 1024)

                disk_fmt = format_size_str(disk_mb)
                ram_fmt = format_size_str(final_freed_ram_mb)

                self.after(0, lambda: self.update_cumulative_stats(freed_disk_mb=disk_mb, freed_ram_mb=final_freed_ram_mb))
                self.append_log(f"🎉 【清理成果】釋出暫存磁碟容量: {disk_fmt} / 釋放 RAM: {ram_fmt}！", CONFIG.THEME["SUCCESS"])
                self.after(0, lambda: messagebox.showinfo("清理完成", f"清理已成功完畢！\n\n🧹 成功清理暫存檔容量: {disk_fmt}\n🎉 系統負載已降至 {load_after}%。"))
            except Exception as e:
                self.append_log(f"❌ 清理過程中發生異常: {str(e)}", CONFIG.THEME["DANGER"])
            finally:
                self.after(0, lambda: self.btn_launch.configure(state="normal", text="⚡ 開始執行選定清理"))
                self.after(2000, lambda: self.progress_bar.set(0))


if __name__ == "__main__":
    try:
        if sys.platform.startswith('win'):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
    except Exception: pass

    app = SystemOptimizerApp()
    app.mainloop()
