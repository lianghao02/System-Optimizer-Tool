# 🚀 本機系統快取清理與記憶體優化工具 (System Optimizer Tool)

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![UI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v4.0-success.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular-success.svg)

> **參考 BleachBit、Mem Reduct 與 Optimizer 核心理念** 打造之強健型 Windows 系統快取維護與記憶體暫時釋放工具。  
> **不修改登錄檔最佳化參數、不停用 Windows 系統服務、不變更電源計畫與核心安全設定。系統維護操作僅限於使用者選定之暫存檔、可重建快取、程序記憶體與已確認卸載殘留項目。**

---

## 🏆 v4.0 劃時代升級：三層安全架構、RAM 獨立管理與大型快取分析器

本版本完成全專案職責純化解耦（`config.py` / `memory.py` / `cache_inspector.py` / `optimizer.py` / `boot.py` / `uninstaller.py`），並奠定防禦性設計標準。

### 🌟 四大核心維護分頁

#### 1. 🧹 快取與記憶體維護 (Page Clean - 三層安全架構)
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

#### 2. 🚀 開機啟動資料夾直達 (Page Boot)
- **純粹直覺，零選單雜訊**：
  - 專注提供兩大 Windows 原生開機資料夾一鍵直達按鈕：
    - 🟢 **`📂 一鍵開啟【個人】啟動資料夾 (shell:startup)`**
    - 🔵 **`📂 一鍵開啟【全機共用】啟動資料夾 (shell:common startup)`**
  - 內建最清晰的操作引導說明：複製 `.lnk` 捷徑檔貼上即新增開機啟動，刪除捷徑檔即取消啟動。

#### 3. 🗑️ 軟體徹底卸載 (Page Uninstall)
- 盤點 Windows 32-bit / 64-bit 本機已安裝軟體庫，顯示軟體容量、發行商與安裝日期。
- 呼叫官方卸載程式，並於卸載完成後進行多維度信心分數殘留掃蕩。
- 🛡️ **取消卸載防禦機制**：若官方卸載程式被使用者取消或失敗，自動終止殘留掃蕩，絕不安裝誤刪資料。
- 🔍 **兩階段殘留確認視窗**：預覽候選資料夾與信心分級 (🟢高可信 >=90% / 🟡建議確認 70-89% / 🔴低可信)，未經使用者勾選 100% 不刪除。

#### 4. ⚙️ 設定與保護白名單 (Page Settings)
- 🛡️ **WCAG 2.1 AA 護眼高對比視效**：採用對比度 > 4.8:1 的護眼色彩 (`#9DA0C4`)。
- ⌨️ **全域無障礙熱鍵**：支援 `<F5>`（一鍵重新整理）、`<Ctrl+F>`（快速搜尋聚焦）、`<Escape>`（關閉對話框）。
- 🔒 **動態保護白名單管理**：支援介面互動新增/刪除保護關鍵字，持久化同步至 `config/whitelist.json`。

---

## 📂 專案模組架構 (Modular Taxonomy)

```
System-Optimizer-Tool/
├── engine/
│   ├── __init__.py
│   ├── config.py          # 全域配置、常數、路徑、JSON 讀寫與白名單
│   ├── memory.py          # Win32 RAM 狀態、Working Set 縮減與 Toolhelp32 進程快照
│   ├── cache_inspector.py # 大型快取分析器 (掃描、容量、風險評估)
│   ├── optimizer.py       # 已知安全/可重建檔案清理引擎
│   ├── boot.py            # Windows 原生開機資料夾直達與定位
│   └── uninstaller.py     # 軟體庫讀取與多維度信心分數殘留掃蕩
├── ui/
│   ├── __init__.py
│   └── dialogs.py         # 模擬預覽與兩階段殘留確認視窗對話框
├── main.py                # CustomTkinter 主介面與三層安全 UI
├── run.bat                # Windows 一鍵啟動腳本
├── 啟動工具.bat            # 雙擊啟動捷徑
├── README.md              # 專案說明文件
└── CHANGELOG.md           # 版本演進紀錄
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