# 🚀 本機系統快取清理與記憶體優化工具 (System Optimizer Tool)

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v3.1-success.svg)

> **參考 BleachBit、Mem Reduct 與 Optimizer 理念** 打造之強健型 Windows 系統清理與記憶體優化工具。  
> **100% 絕不變更任何系統核心設定**，純粹專注於過期暫存檔案清理、軟體快取清理、全碟隱藏快取自動盤點、雙層 Startup 開機資料夾直覺管理與實體 RAM 記憶體深度壓縮。

---

## 🏆 v3.1 重大更新：AccessLint 無障礙對比度、AddyOsmani 效能優化與動態白名單

**v3.1 結合 AccessLint 與 AddyOsmani-Perf 技能升級**：
1. ♿ **AccessLint 高對比度與無障礙熱鍵 (WCAG 4.5:1 AA 達標)**：
   - 提升次要文字與說明文字色彩 (`#9DA0C4`)，大幅增強視覺閱讀舒適度。
   - 新增全域熱鍵：`<F5>`（一鍵重新整理清單）、`<Ctrl+F>`（快速聚焦搜尋欄位）、`<Escape>`（快速關閉對話框）。
2. ⚡ **AddyOsmani-Perf 軟體庫零阻塞 (INP < 50ms)**：
   - 軟體庫讀取採用非同步速查模式，徹底消除讀取大型軟體資料夾時的硬碟 I/O 阻塞。
3. 📂 **一鍵定位開啟實體檔案位置 (Open File Location)**：
   - 開機啟動清單與已安裝軟體項目旁均新增 **`📂 檔案位置`** / **`📂 安裝位置`** 按鈕，自動開啟 Windows 檔案總管並精準定位目標檔。
4. 🛡️ **動態白名單持久化管理**：
   - 「設定與保護白名單」分頁支援動態新增與刪除自訂保護關鍵字，自動寫入便攜式 `config/whitelist.json`。

---

## ✨ 重點更新特色 (v3.1)

- ♿ **WCAG 2.1 AA 護眼高對比色彩**：提升小字號與細節描述對比度，長久使用不傷眼。
- ⌨️ **全域快捷熱鍵**：支援 F5 / Ctrl+F / Escape 全鍵盤順暢操作。
- 📂 **實體檔案位置一鍵直達**：支援 `.exe` 或 `.lnk` 精準定位。
- 🛡️ **便攜動態白名單**：自動同步自訂白名單至 `config/whitelist.json`。

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