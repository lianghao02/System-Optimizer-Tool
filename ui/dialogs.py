# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
模組名稱：對話框與視窗模組 (ui/dialogs.py)
"""

import customtkinter as ctk
from tkinter import scrolledtext
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

class AddCustomScriptDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_add_callback):
        super().__init__(parent)
        self.title("➕ 新增自訂開機軟體/腳本延遲啟動")
        self.geometry("550x380")
        self.on_add_callback = on_add_callback
        
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
            from tkinter import messagebox
            messagebox.showwarning("欄位未完成", "請務必填寫「軟體名稱」與「執行檔路徑」！")
            return

        self.on_add_callback(name, path, args, delay)
        self.destroy()
