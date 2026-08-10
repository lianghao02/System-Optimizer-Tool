# 🚀 本機系統快取清理與記憶體優化工具 (System Optimizer Tool)

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v3.2-success.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular-success.svg)

> **參考 BleachBit、Mem Reduct 與 Optimizer 核心理念** 打造之極致強健型 Windows 系統快取清理、開機引導與實體記憶體優化工具。  
> **100% 絕不變更任何系統核心設定**，專注於暫存檔清除、隱藏快取自動盤點、雙層 Startup 開機資料夾直覺導引、Win32 Working Set 原生記憶體深度壓縮與 Geek 級軟體徹底卸載。

---

## 🏆 v3.2 精簡極致升級：純粹直覺的開機啟動資料夾直達工具

本專案經過多次版本疊代，完成了全專案解耦模組化拆分（`engine/` 與 `ui/`）與 Win32 原生快照極速優化。

### 🌟 四大核心功能分頁

#### 1. 🧹 快取與記憶體優化 (Page Clean)
- **第一類：無感完全安全清理**
  - 使用者暫存區 (`Temp`) 檔案清理。
  - 系統崩潰傾印檔 (`CrashDumps`) 與微軟錯誤報告 (`WER`) 清除。
  - 微軟傳遞優化下載快取 (`Delivery Optimization`) 清理。
  - 開發者套件包快取（`pip` / `uv` / `npm` / `pnpm` / `Yarn` / `Poetry`）掃蕩。
- **第二類：軟體快取與全碟自動盤點**
  - 網頁瀏覽器暫存快取（`Chrome` / `Edge` / `Brave` / `Firefox` 各 Profile）。
  - 常用軟體與 IDE 索引快取（`VS Code` / `JetBrains` / `Adobe` / `Discord` / `Spotify`）。
  - 🔍 **Smart Cache Finder 智慧全碟快取自動盤點**：全自動搜尋 > 50 MB 隱藏快取巨頭。
  - 顯示卡著色器快取（`DirectX` / `NVIDIA DX & NV` / `AMD`）。
  - 檔案總管縮圖快取（`thumbcache_*.db`）與系統預載歷史（`Prefetch`）。
- **實體 RAM 記憶體回收引擎**
  - ⚡ **Win32 Toolhelp32 Native 原生快照 (0.5ms 極速)**：秒級關閉高能耗背景閒置處理程序。
  - 🚀 **EmptyWorkingSet 原生 API 深度回收**：寫入層級回收處理程序閒置 Working Set 分頁記憶體。
  - 🛡️ **模擬開關 (Dry-Run Preview)**：彈出互動式擬清理與擬關閉處理程序預覽明細。

#### 2. 🚀 開機啟動資料夾直達 (Page Boot)
- **純粹直覺，零選單雜訊**：
  - 應使用者體驗需求，全盤簡化過度複雜的登錄檔與排程器掃描。
  - 專注提供兩大 Windows 原生開機資料夾一鍵直達按鈕：
    - 🟢 **`📂 一鍵開啟【個人】啟動資料夾 (shell:startup)`**
    - 🔵 **`📂 一鍵開啟【全機共用】啟動資料夾 (shell:common startup)`**
  - 內建最清晰的操作引導說明：複製 `.lnk` 捷徑檔貼上即新增開機啟動，刪除捷徑檔即取消啟動。

#### 3. 🗑️ 軟體徹底卸載 (Geek 版 - Page Uninstall)
- 盤點 Windows 32-bit / 64-bit 本機已安裝軟體庫，顯示軟體容量、發行商與安裝日期。
- 支援快速關鍵字過濾搜尋與「隱藏系統必備元件」切換。
- 呼叫官方卸載程式，並於卸載後自動掃蕩 `%LOCALAPPDATA%` / `%APPDATA%` / `%ProgramData%` 深層殘留資料夾。
- 📂 **一鍵定位開啟安裝資料夾**：點擊 `📂 安裝位置` 自動開啟 Windows 檔案總管並選擇標的檔案。

#### 4. ⚙️ 設定與動態保護白名單 (Page Settings)
- 🛡️ **WCAG 2.1 AA 護眼高對比視效**：採用對比度 > 4.8:1 的護眼色彩 (`#9DA0C4`)。
- ⌨️ **全域無障礙熱鍵**：支援 `<F5>`（一鍵重新整理）、`<Ctrl+F>`（快速搜尋聚焦）、`<Escape>`（關閉對話框）。
- 🔒 **動態保護白名單管理**：支援介面互動新增/刪除保護關鍵字，並自動持久化同步至 `config/whitelist.json`。

---

## 📂 專案模組架構 (Modular Taxonomy)

```
System-Optimizer-Tool/
├── engine/
│   ├── __init__.py
│   ├── config.py         # 全域配置、路徑、白名單與 Win32 RAM 工具
│   ├── optimizer.py      # 快取清理與 Working Set 記憶體壓縮引擎
│   ├── boot.py           # 開機啟動資料夾直達與本機定位工具
│   └── uninstaller.py    # 軟體卸載庫與深層殘留掃蕩引擎
├── ui/
│   ├── __init__.py
│   └── dialogs.py        # 模擬預覽與自訂視窗對話框
├── main.py               # CustomTkinter 主介面與啟動進入點
├── run.bat               # Windows 一鍵啟動腳本
├── 啟動工具.bat           # 雙擊啟動捷徑
├── README.md             # 專案說明文件
└── CHANGELOG.md          # 版本演進與對外 Release Notes
```

---

## 🚀 快速開始

### 1. 使用批次檔一鍵啟動 (推薦)
雙擊專案目錄下的 **`啟動工具.bat`** 或 **`run.bat`** 即可直接開啟軟體介面（自動檢測並安裝所需套件）。

### 2. 手動指令啟動
```bash
pip install customtkinter
python main.py
```

---

## 📜 授權協議

本專案採用 [MIT License](LICENSE) 授權條款。