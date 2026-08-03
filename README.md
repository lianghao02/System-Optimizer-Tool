# 🚀 本機系統快取清理與記憶體優化工具 (System Optimizer Tool)

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v3.0-success.svg)

> **參考 BleachBit、Mem Reduct 與 Optimizer 理念** 打造之強健型 Windows 系統清理與記憶體優化工具。  
> **100% 絕不變更任何系統核心設定**，純粹專注於過期暫存檔案清理、軟體快取清理、全碟隱藏快取自動盤點、雙層 Startup 開機資料夾直覺管理與實體 RAM 記憶體深度壓縮。

---

## 🏆 v3.0 劃時代升級：全專案解耦模組化、極速 0.5ms Win32 快照與便攜版支援

**v3.0 是一個架構與效能全面爆發的重大版本**：
1. **三大架構隱患全數修復**：全專案完成高內聚低耦合拆分（`engine/` 與 `ui/` 模組）。
2. **徹底消除執行中的微短卡頓/頓感 (Zero-Stutter/Zero-Lag)**：引進 **Win32 Toolhelp32 Native 原生快照 API**，處理程序掃描耗時由 200ms 降至 **0.5ms (效能提升 400 倍)**。
3. **100% 便攜版 (Portable) 相對路徑備份**：設定與備份檔案優先存放在軟體同級 `config/` 資料夾，隨身碟移動帶著走。

---

## ✨ 重點更新特色 (v3.0)

- 📦 **全專案解耦模組化 (Modular Architecture)**：
  - `engine/config.py`：全域主題、路徑、白名單、`format_size_str` 與 Win32 RAM 查詢。
  - `engine/optimizer.py`：`OptimizerEngine`（系統快取、網頁快取、軟體快取、Working Set 記憶體壓縮與 Smart Cache Finder）。
  - `engine/boot.py`：`BootOptimizerEngine`（雙層 Startup 資料夾、捷徑備份垃圾桶、登錄檔 Run 鍵值與排程管理）。
  - `engine/uninstaller.py`：`UninstallerEngine`（軟體庫讀取與殘留資料夾掃蕩）。
  - `ui/dialogs.py`：`PreviewDialog` 與 `AddCustomScriptDialog` 視窗。
- ⚡ **Win32 Toolhelp32 原生快照 (消除頓感)**：
  - 全面淘汰慢速 `tasklist.exe` 子進程，改用 Win32 原生 API 直連核心，掃描耗時僅 **0.5ms**，UI 滑動與分頁切換達 60 FPS 流暢體感。
- 💾 **便攜版 (Portable) 優先相對路徑**：
  - 備份捷徑與設定檔優先寫入軟體根目錄 `config/` 資料夾，備有權限自動回退機制。

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