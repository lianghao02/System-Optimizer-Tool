# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：對話框與視窗模組 (ui/dialogs.py)
"""

import os
import subprocess
import customtkinter as ctk
from tkinter import scrolledtext, messagebox
from engine.config import CONFIG

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
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.transient(parent)
        self.grab_set()
        
        self.build_ui()

    def build_ui(self):
        lbl_title = ctk.CTkLabel(
            self, text=f"📋 模擬預覽統計：擬清理 {len(self.pending_files)} 個檔案 / 擬關閉 {len(self.pending_pids)} 個閒置處理程序",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]
        )
        lbl_title.pack(anchor="w", padx=15, pady=(15, 10))

        frame_search = ctk.CTkFrame(self, fg_color="transparent")
        frame_search.pack(fill="x", padx=15, pady=(0, 10))
        
        lbl_search = ctk.CTkLabel(frame_search, text="🔍 快速搜尋清單：", font=ctk.CTkFont(family="Microsoft JhengHei", size=11))
        lbl_search.pack(side="left")
        
        self.entry_search = ctk.CTkEntry(frame_search, placeholder_text="輸入檔名或關鍵字過濾...", width=300)
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

class ResidualsPreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, software_name, candidates, on_confirm_delete_callback):
        super().__init__(parent)
        self.title(f"🔍 卸載深層殘留確認 - {software_name}")
        self.geometry("780x520")
        self.software_name = software_name
        self.candidates = candidates
        self.on_confirm_delete_callback = on_confirm_delete_callback
        self.check_vars = {}

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.grab_set()

        self.build_ui()

    def build_ui(self):
        lbl_title = ctk.CTkLabel(
            self, text=f"🔍 【{self.software_name}】官方卸載完成 - 偵測到 {len(self.candidates)} 個疑似深層殘留資料夾",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]
        )
        lbl_title.pack(anchor="w", padx=20, pady=(15, 4))

        lbl_desc = ctk.CTkLabel(
            self, text="💡 安全防禦提示：預設僅會自動勾選 🟢 高可信度 (>=90%) 項目。請您審視下列候選資料夾後，確認勾選欲清理的項目。",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["TEXT_MUTED"]
        )
        lbl_desc.pack(anchor="w", padx=20, pady=(0, 10))

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=8)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        for idx, item in enumerate(self.candidates):
            row = ctk.CTkFrame(scroll_frame, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
            row.pack(fill="x", pady=4)

            var = ctk.BooleanVar(value=item["auto_check"])
            self.check_vars[idx] = (var, item)

            chk = ctk.CTkCheckBox(row, text="", variable=var, width=28, checkbox_width=18, checkbox_height=18)
            chk.pack(side="left", padx=(10, 5), pady=10)

            lbl_conf = ctk.CTkLabel(row, text=item["confidence_label"], font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), width=160)
            lbl_conf.pack(side="left", padx=5)

            info_f = ctk.CTkFrame(row, fg_color="transparent")
            info_f.pack(side="left", fill="both", expand=True, padx=5, pady=6)

            ctk.CTkLabel(info_f, text=f"📂 路徑：{item['path']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_f, text=f"容量大小：{item['size_fmt']} | 匹配得分：{item['score']} 分", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w").pack(anchor="w")

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(fill="x", padx=20, pady=(0, 15))

        btn_cancel = ctk.CTkButton(
            frame_btns, text="🛑 放棄不刪除", fg_color=CONFIG.THEME["CARD_BG"],
            hover_color=CONFIG.THEME["DANGER"], text_color=CONFIG.THEME["TEXT_LIGHT"], command=self.destroy
        )
        btn_cancel.pack(side="right", padx=5)

        btn_confirm = ctk.CTkButton(
            frame_btns, text="🗑️ 清除已勾選殘留資料夾", fg_color=CONFIG.THEME["DANGER"],
            hover_color="#C0392B", text_color=CONFIG.THEME["TEXT_LIGHT"], command=self._on_confirm
        )
        btn_confirm.pack(side="right", padx=5)

    def _on_confirm(self):
        selected_paths = [item["path"] for var, item in self.check_vars.values() if var.get()]
        self.destroy()
        self.on_confirm_delete_callback(selected_paths)

class AddCustomScriptDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_add_callback):
        super().__init__(parent)
        self.title("➕ 新增自訂開機軟體/腳本延遲啟動")
        self.geometry("550x380")
        self.on_add_callback = on_add_callback
        
        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.grab_set()
        
        self.build_ui()

    def build_ui(self):
        lbl_title = ctk.CTkLabel(self, text="📝 新增開機延遲啟動軟體/腳本", font=ctk.CTkFont(family="Microsoft JhengHei", size=14, weight="bold"), text_color=CONFIG.THEME["PRIMARY"])
        lbl_title.pack(anchor="w", padx=20, pady=(15, 10))

        frame_form = ctk.CTkFrame(self, fg_color="transparent")
        frame_form.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(frame_form, text="軟體或腳本名稱：", font=ctk.CTkFont(family="Microsoft JhengHei", size=11)).pack(anchor="w", pady=(5, 2))
        self.entry_name = ctk.CTkEntry(frame_form, placeholder_text="例如：自動備份腳本 / Notion", width=480)
        self.entry_name.pack(anchor="w")

        ctk.CTkLabel(frame_form, text="執行檔或腳本路徑 (.exe / .py / .bat)：", font=ctk.CTkFont(family="Microsoft JhengHei", size=11)).pack(anchor="w", pady=(10, 2))
        frame_path = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_path.pack(fill="x")
        self.entry_path = ctk.CTkEntry(frame_path, placeholder_text="C:\\path\\to\\app.exe", width=400)
        self.entry_path.pack(side="left")
        btn_browse = ctk.CTkButton(frame_path, text="📁 瀏覽", width=70, command=self._browse_file)
        btn_browse.pack(side="left", padx=8)

        ctk.CTkLabel(frame_form, text="啟動參數 (選填)：", font=ctk.CTkFont(family="Microsoft JhengHei", size=11)).pack(anchor="w", pady=(10, 2))
        self.entry_args = ctk.CTkEntry(frame_form, placeholder_text="例如：--minimized / --silent", width=480)
        self.entry_args.pack(anchor="w")

        ctk.CTkLabel(frame_form, text="開機延遲時間：", font=ctk.CTkFont(family="Microsoft JhengHei", size=11)).pack(anchor="w", pady=(10, 2))
        self.cmb_delay = ctk.CTkComboBox(frame_form, values=["立即啟動", "開機延遲 10 秒", "開機延遲 30 秒", "開機延遲 60 秒"], width=200)
        self.cmb_delay.pack(anchor="w")

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(fill="x", padx=20, pady=15)

        btn_cancel = ctk.CTkButton(frame_btns, text="🛑 取消", fg_color=CONFIG.THEME["CARD_BG"], hover_color=CONFIG.THEME["DANGER"], command=self.destroy)
        btn_cancel.pack(side="right", padx=5)

        btn_save = ctk.CTkButton(frame_btns, text="💾 儲存並加入清單", fg_color=CONFIG.THEME["SUCCESS"], hover_color="#2196F3", command=self._save_and_close)
        btn_save.pack(side="right", padx=5)

    def _browse_file(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="選擇要開機執行的軟體或腳本", filetypes=[("可執行檔/腳本", "*.exe *.py *.bat *.cmd"), ("所有檔案", "*.*")])
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, path)

    def _save_and_close(self):
        name = self.entry_name.get().strip()
        path = self.entry_path.get().strip()
        args = self.entry_args.get().strip()
        delay = self.cmb_delay.get()

        if not name or not path:
            messagebox.showwarning("欄位未完成", "請務必填寫「軟體名稱」與「執行檔路徑」！")
            return

        self.on_add_callback(name, path, args, delay)
        self.destroy()

class StorageAnalyzerDialog(ctk.CTkToplevel):
    def __init__(self, parent, large_files, aged_files, dup_groups, downloads_health):
        super().__init__(parent)
        self.title("📊 全碟儲存空間與分析儀表板 (v5.0 空間診斷專頁)")
        self.geometry("880x620")
        self.large_files = large_files
        self.aged_files = aged_files
        self.dup_groups = dup_groups
        self.downloads_health = downloads_health

        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)
        self.grab_set()

        self.build_ui()

    def build_ui(self):
        lbl_title = ctk.CTkLabel(
            self, text="📊 全碟儲存空間診斷與分析報告 (100% 唯讀分析，預設不刪除)",
            font=ctk.CTkFont(family="Microsoft JhengHei", size=15, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]
        )
        lbl_title.pack(anchor="w", padx=20, pady=(15, 5))

        tabview = ctk.CTkTabview(self, corner_radius=8)
        tabview.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        tab_large = tabview.add("🔍 巨型檔案 (>500MB)")
        tab_aged = tabview.add("🕒 長期未使用 (>180天)")
        tab_dup = tabview.add("👯 重複檔案 (SHA-256)")
        tab_dl = tabview.add("📥 Downloads 健檢")

        self._build_large_files_tab(tab_large)
        self._build_aged_files_tab(tab_aged)
        self._build_duplicates_tab(tab_dup)
        self._build_downloads_tab(tab_dl)

    def _build_large_files_tab(self, parent_tab):
        scroll = ctk.CTkScrollableFrame(parent_tab, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        if not self.large_files:
            ctk.CTkLabel(scroll, text="未發現任何 >500MB 之巨型檔案。", font=ctk.CTkFont(family="Microsoft JhengHei", size=12), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(pady=20)
            return

        for item in self.large_files:
            row = ctk.CTkFrame(scroll, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
            row.pack(fill="x", pady=4)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            ctk.CTkLabel(info, text=f"📄 {item['name']} ({item['size_fmt']}) [{item['category']}]", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"), text_color=CONFIG.THEME["TEXT_LIGHT"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=f"路徑：{item['path']} | 修改日期：{item['mtime_str']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w").pack(anchor="w")

            btn_open = ctk.CTkButton(row, text="📂 開啟位置", width=90, command=lambda p=item['path']: self._open_file_location(p))
            btn_open.pack(side="right", padx=10, pady=8)

    def _build_aged_files_tab(self, parent_tab):
        scroll = ctk.CTkScrollableFrame(parent_tab, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        if not self.aged_files:
            ctk.CTkLabel(scroll, text="未發現 >100MB 且超過 180 天未修改之檔案。", font=ctk.CTkFont(family="Microsoft JhengHei", size=12), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(pady=20)
            return

        for item in self.aged_files:
            row = ctk.CTkFrame(scroll, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
            row.pack(fill="x", pady=4)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            ctk.CTkLabel(info, text=f"🕒 {item['name']} ({item['size_fmt']}) - {item['age_tier']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"), text_color=CONFIG.THEME["WARNING"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=f"路徑：{item['path']} | 未修改天數：{item['days_unused']} 天 ({item['aged_label']})", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_MUTED"], anchor="w").pack(anchor="w")

            btn_open = ctk.CTkButton(row, text="📂 開啟位置", width=90, command=lambda p=item['path']: self._open_file_location(p))
            btn_open.pack(side="right", padx=10, pady=8)

    def _build_duplicates_tab(self, parent_tab):
        scroll = ctk.CTkScrollableFrame(parent_tab, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        if not self.dup_groups:
            ctk.CTkLabel(scroll, text="未發現 100% SHA-256 雜湊內容相同之重複檔案。", font=ctk.CTkFont(family="Microsoft JhengHei", size=12), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(pady=20)
            return

        for group in self.dup_groups:
            card = ctk.CTkFrame(scroll, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
            card.pack(fill="x", pady=6, padx=5)

            ctk.CTkLabel(card, text=f"👯 重複群組 (SHA-256: {group['sha256']}) - 單檔: {group['file_size_fmt']} | 可省空間: {group['waste_fmt']}", font=ctk.CTkFont(family="Microsoft JhengHei", size=11, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=10, pady=(6, 4))

            for path in group["paths"]:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(row, text=f"📄 {path}", font=ctk.CTkFont(family="Microsoft JhengHei", size=10), text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left")
                btn_open = ctk.CTkButton(row, text="📂 開啟", width=60, height=22, command=lambda p=path: self._open_file_location(p))
                btn_open.pack(side="right")

    def _build_downloads_tab(self, parent_tab):
        scroll = ctk.CTkScrollableFrame(parent_tab, fg_color=CONFIG.THEME["BG_DARK"], corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        old_inst = self.downloads_health.get("old_installers", [])
        red_arch = self.downloads_health.get("redundant_archives", [])

        if not old_inst and not red_arch:
            ctk.CTkLabel(scroll, text="Downloads 資料夾狀態極佳！未發現舊軟體安裝檔或冗餘壓縮檔。", font=ctk.CTkFont(family="Microsoft JhengHei", size=12), text_color=CONFIG.THEME["TEXT_MUTED"]).pack(pady=20)
            return

        if old_inst:
            ctk.CTkLabel(scroll, text="📦 舊版軟體安裝檔候選 (>180天)", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"), text_color=CONFIG.THEME["WARNING"]).pack(anchor="w", padx=10, pady=(10, 4))
            for item in old_inst:
                row = ctk.CTkFrame(scroll, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=f"📄 {item['name']} ({item['size_fmt']}) - 存放 {item['days_old']} 天", font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=10)
                btn_open = ctk.CTkButton(row, text="📂 開啟", width=60, height=22, command=lambda p=item['path']: self._open_file_location(p))
                btn_open.pack(side="right", padx=6)

        if red_arch:
            ctk.CTkLabel(scroll, text="📦 冗餘壓縮檔 (同名資料夾已存在於 Downloads)", font=ctk.CTkFont(family="Microsoft JhengHei", size=12, weight="bold"), text_color=CONFIG.THEME["PRIMARY"]).pack(anchor="w", padx=10, pady=(15, 4))
            for item in red_arch:
                row = ctk.CTkFrame(scroll, fg_color=CONFIG.THEME["CARD_BG"], corner_radius=6)
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=f"📦 {item['name']} ({item['size_fmt']}) -> 發現資料夾 [{item['matched_folder']}]", font=ctk.CTkFont(family="Microsoft JhengHei", size=11), text_color=CONFIG.THEME["TEXT_LIGHT"]).pack(side="left", padx=10)
                btn_open = ctk.CTkButton(row, text="📂 開啟", width=60, height=22, command=lambda p=item['path']: self._open_file_location(p))
                btn_open.pack(side="right", padx=6)

    def _open_file_location(self, file_path):
        try:
            if os.path.exists(file_path):
                subprocess.Popen(f'explorer.exe /select,"{file_path}"', shell=True)
            else:
                messagebox.showwarning("檔案不存在", f"該檔案已移動或不存在：{file_path}")
        except Exception as e:
            messagebox.showerror("開啟失敗", f"無法開啟位置: {str(e)}")
