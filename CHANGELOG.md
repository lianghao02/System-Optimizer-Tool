# 📝 更新紀錄 (CHANGELOG)

---

## [v1.3.0] - 2026-07-30

### 🎉 v1.3.0 里程碑：Smart Cache Finder 智慧全碟快取支援

v1.3.0 是一個重大里程碑版本：除了既有系統 Temp、Chrome/Edge 網頁與常用開發軟體快取清理外，正式加入 **Smart Cache Finder (智慧全碟快取極速自動盤點引擎)**。

過往傳統清理工具僅能抓取固定預設路徑，容易漏掉隱藏在各處的巨大快取。本版新增獨立盤點流程，可在 3 ~ 5 秒鐘內全自動挖掘出硬碟中大於 50 MB 的隱藏快取巨頭（如 CapCut 剪映視訊快取、新版 Outlook 快取、Adobe 閱讀器快取、VS Code 擴充套件快取等），並提供透明化預覽與一鍵真實清理。

#### ✨ 重點更新：
- **新增「Smart Cache Finder」極速全碟快取自動盤點功能**：
  - 全自動精準定位 `%USERPROFILE%`、`AppData\Local`、`AppData\Roaming`、`C:\ProgramData` 及其他本機硬碟（如 `D:\`）。
  - 支援快取資料夾**剪枝優化 (Pruning)**，全流程盤點僅需 3~5 秒。
  - 支援 **> 50 MB 快取巨頭門檻過濾**，避免資訊過載。
- **新增智慧 GB / MB 容量單位動態轉換**：
  - 統計卡片與清理完成報告自動將大於 1024 MB 轉換為 GB 顯示。
- **強化 Windows 唯讀檔案權限處置**：
  - 刪除前自動解除唯讀標記（`os.chmod`），解決權限不足導致清理跳過問題。
- **修復 PreviewDialog 視窗取消與關閉機制**：
  - 修正關閉或取消對話框時，主介面「開始一鍵優化」按鈕狀態自動復原。
- **優化整體日誌 Console 呈現風格與色彩標記**。

---

## [v1.2.0] - 2026-07-30

### 🚀 開源技術大一統升級 (BleachBit, Mem Reduct, Optimizer 借鏡)

- **新增常用應用軟體快取清理 (`clean_app_cache`)**：
  - 支援清理 VS Code (快取與程式碼快取)、Discord、Spotify 及 npm/Yarn 快取。
- **新增 Windows 原生 `EmptyWorkingSet` API 深度 RAM 壓縮 (Mem Reduct 借鏡)**：
  - 調用 Win32 `psapi.dll` 進行工作集壓縮，不關閉程式即可瞬間釋放 1GB~3GB 可用 RAM。
- **新增模擬細節預覽對話框 (`PreviewDialog` - Optimizer 借鏡)**：
  - 提供即時關鍵字搜尋與擬清理清單明細過濾。
- **新增二行式動態累計統計卡片**。

---

## [v1.1.0] - 2026-07-29

### 🌐 網頁快取與實時 RAM 監控升級

- **新增網頁暫存快取清理 (`clean_browser_cache`)**：
  - 支援 Chrome 與 Edge 靜態快取檔 (Cache & Code Cache)，承諾不影響瀏覽紀錄與密碼。
- **新增 Windows 原生 `GlobalMemoryStatusEx` API 實時 RAM 監控**。
- **新增 ANSI/Big5 相容雙擊啟動檔 (`啟動工具.bat` 與 `run.bat`)**。

---

## [v1.0.0] - 2026-07-28

### 🎉 專案初始發布 (Initial Release)

- **基礎架構確立**：Python 3 + CustomTkinter 現代化深色 UI。
- **系統 Temp 暫存區清理**（支援保護白名單防護）。
- **高能耗閒置 Python / Node 處理程序盤點與關閉**。
- **Python 記憶體垃圾回收 (`gc.collect`)**。
