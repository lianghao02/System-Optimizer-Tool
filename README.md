# 🚀 本機系統快取清理與記憶體優化工具 (System Optimizer Tool)

![Python Version](https://img.shields.io/badge/Python-3.13-blue.svg)
![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v5.0-success.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular-success.svg)

> **參考 BleachBit、Mem Reduct 與 Optimizer 核心理念** 打造之強健型 Windows 儲存空間分析與安全維護工具。  
> **不修改登錄檔最佳化參數、不停用 Windows 系統服務、不變更電源計畫與核心安全設定。系統維護操作僅限於使用者選定之暫存檔、可重建快取、程序記憶體與已確認卸載殘留項目。**

---

## 🏆 v5.0 里程碑：全碟儲存空間分析器與宣告式快取規則表

本版本完成了全碟儲存空間分析與宣告式 Cache Rule 規則表架構，將工具從單純的快取清理器升級為 **「Windows 儲存空間分析與安全維護專家」**。

### 🌟 五大核心維護分頁與診斷儀表板

#### 1. 📊 全碟儲存空間診斷儀表板 (v5.0 全新功能)
- 🔍 **巨型檔案分析器 (Large File Inspector)**：全自動盤點 >500MB 巨型標的（系統 ISO / 大型壓縮檔 / 影音檔 / 日誌與 Dump / AI `.gguf` 模型）。
- 🕒 **長期未使用檔案分析 (Long Unused File Inspector)**：組合檔案容量、最後修改時間 (Last Modified Time) 與路徑，分類標示 90 / 180 / 365 / 730 天，標註 **「可能長期未使用」**。
- 👯 **三階段 SHA-256 重複檔案分析器 (3-Stage Duplicate Finder)**：
  - 第一階段：檔案容量大小過濾。
  - 第二階段：首尾 64KB 區塊快速雜湊 (Fast Head/Tail Hash)。
  - 第三階段：完整 SHA-256 內容雜湊比對。預設全部不勾選，絕不單憑檔名判斷。
- 📥 **Downloads 下載資料夾健檢 (Downloads Health Checker)**：
  - 診斷放置 >180 天之舊版軟體安裝檔 (`*.exe`, `*.msi`)。
  - 診斷冗餘壓縮檔（同名資料夾已存在於 Downloads 資料夾者）。
- 100% 唯讀分析，提供 `📂 開啟位置` 精準定位。

#### 2. 🧹 快取與記憶體維護 (Page Clean - 三層安全架構)
- 🟢 **第一層：安全清理 (Safe Cleaning - 預設推薦勾選)**
  - 使用者暫存區 (`Temp`) 檔案清理。
  - 系統崩潰傾印檔 (`CrashDumps`) 與微軟錯誤報告 (`WER`) 清除。
  - 微軟傳遞優化下載快取 (`Delivery Optimization`) 清理。
  - 開發套件包快取（`pip` / `uv` / `npm` / `pnpm` / `Yarn` / `Poetry`）掃蕩。
  - 網頁瀏覽器暫存快取（`Chrome` / `Edge` / `Brave` / `Firefox`）。
- 🟡 **第二層：可重建快取 (Rebuildable Cache - 預設不勾選)**
  - 常用軟體與 IDE 索引快取（`VS Code` / `JetBrains` / `Adobe` / `Discord` / `Spotify`）。
  - 顯示卡著色器快取（`DirectX` / `NVIDIA DX & NV` / `AMD`）。
  - 檔案總管縮圖快取（`thumbcache_*.db`）。
  - 🔍 **Smart Cache Inspector 大型快取分析器**：全自動盤點 > 50 MB 隱藏快取，標註風險與建議，**未知項目 100% 只讀不自動刪除**。
- 🔴 **第三層：進階操作 (Advanced Actions - 獨立，預設不勾選)**
  - 系統預載歷史 (`Prefetch` - 不建議日常頻繁清理)。
  - ⚙️ **Working Set 頁面暫時釋放**：獨立按鈕調用 Win32 `EmptyWorkingSet` 原生 API。
  - 閒置高佔用處理程序選擇性結束。
  - 🛡️ **模擬開關 (Dry-Run Preview)**：彈出互動式擬清理與擬關閉處理程序預覽明細。

#### 3. 🚀 開機啟動資料夾直達 (Page Boot)
- 專注提供兩大 Windows 原生開機資料夾一鍵直達按鈕：
  - 🟢 **`📂 一鍵開啟【個人】啟動資料夾 (shell:startup)`**
  - 🔵 **`📂 一鍵開啟【全機共用】啟動資料夾 (shell:common startup)`**
- 內建最清晰的操作引導說明：複製 `.lnk` 捷徑檔貼上即新增開機啟動，刪除捷徑檔即取消啟動。

#### 4. 🗑️ 軟體徹底卸載 (Page Uninstall)
- 盤點 Windows 32-bit / 64-bit 本機已安裝軟體庫，顯示軟體容量、發行商與安裝日期。
- 呼叫官方卸載程式，並於卸載完成後進行多維度信心分數殘留掃蕩。
- 🛡️ **取消卸載防禦機制**：若官方卸載程式被使用者取消或失敗，自動終止殘留掃蕩，絕不安裝誤刪資料。
- 🔍 **兩階段殘留確認視窗**：預覽候選資料夾與信心分級 (🟢高可信 >=90% / 🟡建議確認 70-89% / 🔴低可信)，未經使用者勾選 100% 不刪除。

#### 5. ⚙️ 設定與保護白名單 (Page Settings)
- 🛡️ **WCAG 2.1 AA 護眼高對比視效**：採用對比度 > 4.8:1 的護眼色彩 (`#9DA0C4`)。
- ⌨️ **全域無障礙熱鍵**：支援 `<F5>`（一鍵重新整理）、`<Ctrl+F>`（快速搜尋聚焦）、`<Escape>`（關閉對話框）。
- 🔒 **動態保護白名單管理**：支援介面互動新增/刪除保護關鍵字，持久化同步至 `config/whitelist.json`。

---

## 📂 專案模組架構 (Modular Taxonomy)

```
System-Optimizer-Tool/
├── engine/
│   ├── __init__.py
│   ├── config.py           # 全域配置、常數、路徑、JSON 讀寫與白名單
│   ├── memory.py           # Win32 RAM 狀態、Working Set 縮減與 Toolhelp32 進程快照
│   ├── cache_rules.py      # [v5.0] 宣告式 CacheRule 規則表與鎖定檢測
│   ├── storage_analyzer.py # [v5.0] 巨型檔案、長期未使用、重複檔案 (SHA-256) 與 Downloads 健檢
│   ├── cache_inspector.py  # 大型快取分析器 (掃描、容量、風險評估)
│   ├── optimizer.py        # 已知安全/可重建檔案清理引擎
│   ├── boot.py             # Windows 原生開機資料夾直達與定位
│   └── uninstaller.py      # 軟體庫讀取與多維度信心分數殘留掃蕩
├── ui/
│   ├── __init__.py
│   └── dialogs.py          # 模擬預覽、殘留確認與全碟儲存空間診斷視窗
├── main.py                 # CustomTkinter 主介面與三層安全 UI
├── run.bat                 # Windows 一鍵啟動腳本
├── 啟動工具.bat             # 雙擊啟動捷徑
├── README.md               # 專案說明文件
└── CHANGELOG.md            # 版本演進紀錄
```

---

## 🚀 快速開始

### 1. 使用批次檔一鍵啟動 (推薦)
雙擊專案目錄下的 **`啟動工具.bat`** 或 **`run.bat`** 即可直接開啟軟體介面（自動檢測並安裝所需套件）。

### 2. 手動指令啟動
本專案以 **Python 3.13** 作為主要開發與驗證版本。

```bash
C:\Users\chia-hao\AppData\Local\Programs\Python\Python313\python.exe -m pip install customtkinter
C:\Users\chia-hao\AppData\Local\Programs\Python\Python313\python.exe main.py
```

---

## 📜 授權協議

本專案採用 [MIT License](LICENSE) 授權條款。
