# 🚀 本機系統快取清理與記憶體優化工具 (System Optimizer Tool)

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v3.2-success.svg)

> **參考 BleachBit、Mem Reduct 與 Optimizer 理念** 打造之強健型 Windows 系統清理與記憶體優化工具。  
> **100% 絕不變更任何系統核心設定**，純粹專注於過期暫存檔案清理、軟體快取清理、全碟隱藏快取自動盤點、雙層 Startup 開機資料夾直覺導引與實體 RAM 記憶體深度壓縮。

---

## 🏆 v3.2 精簡極致升級：純粹直覺的開機啟動資料夾直達工具

**v3.2 全面重構「頁籤二 (開機啟動管理)」**：
1. 📂 **純粹直覺，零雜訊選單**：
   - 應使用者需求，全面移除複雜且凌亂的登錄檔、工作排程器與第三方開機掃描清單。
   - 專注於提供最直觀的兩大原生資料夾一鍵直達卡片：
     - **`📂 一鍵開啟【個人】啟動資料夾 (shell:startup)`**
     - **`📂 一鍵開啟【全機共用】啟動資料夾 (shell:common startup)`**
2. 💡 **極簡快捷操作指南卡片**：
   - 內建清晰圖文說明，輕鬆實現拖曳複製捷徑檔一鍵開機啟動與刪除捷徑取消啟動。

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