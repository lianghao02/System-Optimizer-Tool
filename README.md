# 🚀 本機系統快取清理與記憶體優化工具 (System Optimizer Tool)

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v2.7-success.svg)

> **參考 BleachBit、Mem Reduct 與 Optimizer 理念** 打造之強健型 Windows 系統清理與記憶體優化工具。  
> **100% 絕不變更任何系統核心設定**，純粹專注於過期暫存檔案清理、軟體快取清理、全碟隱藏快取自動盤點、雙層 Startup 開機資料夾直覺管理與實體 RAM 記憶體深度壓縮。

---

## 🏆 v2.7 重大更新：雙層 Startup 直覺管理與軍規軟性防衛

**v2.7 是一個劃時代的 UX 與安全重構版本**：為解決過往開機啟動項目混雜凌亂的問題，我們全盤重構了「開機啟動與工作排程管理」分頁。

正式引入 **「雙層 Startup 資料夾直覺管理」**（涵蓋個人 `shell:startup` 與全機共用 `shell:common startup`），提供一鍵開機啟動資料夾直達按鈕與安全備份垃圾桶；同時針對登錄檔與排程器引進 **「軍規級軟性停用防護 (Soft-Disable Only)」**，絕不安裝或物理刪除任何系統核心與驅動元件。

---

## ✨ 重點更新特色 (v2.7)

- 📂 **雙層 Startup 資料夾直覺管理與一鍵直達**：
  - **頂部快捷按鈕**：新增 `📂 開啟【個人】啟動資料夾 (shell:startup)` 與 `📂 開啟【全機共用】啟動資料夾 (shell:common startup)`。
  - **捷徑專屬備份垃圾桶**：點擊刪除 Startup 捷徑檔 (.lnk) 時，自動備份至 `%LOCALAPPDATA%\SystemOptimizerTool\backup_shortcuts\`，隨時提供一鍵原路復原，100% 安全對軟體無損。
- 🛡️ **登錄檔與工作排程器「軍規級軟性停用防禦 (Soft-Disable Only)」**：
  - **嚴禁物理刪除**：對於 Registry Run 與 Task Scheduler，100% 不執行物理刪除指令。
  - **狀態動態切換**：採用微軟原生 `/Disable` / `/Enable` 命令與 RunApproved 鍵值備份。
  - **驅動與系統必備標籤 (`⚠️ 系統/驅動必備項目`)**：自動識別 NVIDIA、Realtek、Intel、AMD、Windows Defender 等關鍵項目並打上警告標記，提醒使用者切勿隨意刪除。
- 🎨 **三區塊直覺分層卡片排版**：
  - 🟢 **第一區：`Startup 啟動資料夾捷徑區`**（最直觀，標註 `[個人]` 或 `[全機共用]`）
  - 🟡 **第二區：`Windows 登錄檔 Run 鍵值區`**（軟性開關，附驅動警示標籤）
  - 🔵 **第三區：`Windows 工作排程器啟動區`**（軟性開關，附系統警示標籤）

---

## 📦 技術棧與相依套件

- **程式語言**：Python 3.8+
- **GUI 框架**：[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **標準庫**：`os`, `sys`, `shutil`, `subprocess`, `gc`, `ctypes`, `datetime`, `threading`, `tkinter`, `winreg`

---

## 🚀 快速開始

### 1. 使用批次檔一鍵啟動 (推薦)
雙擊資料夾中的 **`啟動工具.bat`** 或 **`run.bat`** 即可直接開啟軟體介面（自動檢測並安裝所需套件）。

### 2. 手動指令啟動
```bash
pip install customtkinter
python main.py
```

---

## 📜 授權協議

本專案採用 MIT 授權條款。