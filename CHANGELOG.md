# 📝 更新紀錄 (CHANGELOG)

---

## [v2.7] - 2026-08-03

### 🏆 v2.7 重大更新：雙層 Startup 直覺管理與軍規軟性防衛

v2.7 是一個劃時代的 UX 與安全重構版本：為解決過往開機啟動項目混雜凌亂的問題，全盤重構了「開機啟動與工作排程管理」分頁。正式引入 **「雙層 Startup 資料夾直覺管理」**（涵蓋個人 `shell:startup` 與全機共用 `shell:common startup`），提供一鍵開啟本機資料夾與捷徑檔安全備份垃圾桶；同時針對登錄檔與排程器引進 **「軍規級軟性停用防護 (Soft-Disable Only)」**，絕不安裝或物理刪除任何系統核心與驅動元件。

#### ✨ 重點更新：
- **雙層 Startup 資料夾直覺管理與一鍵直達**：
  - 新增 `📂 開啟【個人】啟動資料夾 (shell:startup)` 與 `📂 開啟【全機共用】啟動資料夾 (shell:common startup)` 按鈕。
  - 新增 Shortcut 捷徑專屬備份垃圾桶（自動備份至 `%LOCALAPPDATA%\SystemOptimizerTool\backup_shortcuts\`），支援一鍵原路復原。
- **登錄檔與工作排程器「軍規級軟性停用防護 (Soft-Disable Only)」**：
  - 嚴禁物理刪除，採用微軟原生 `/Disable` / `/Enable` 與 RunApproved 機碼轉移。
  - 新增 `⚠️ 系統/驅動必備項目` 警示標籤（自動辨識 NVIDIA, Realtek, Intel, Defender 等）。
- **三區塊直覺分層卡片排版**：
  - 分開展示 🟢 `Startup 捷徑區`、🟡 `登錄檔 Run 鍵值區` 與 🔵 `工作排程器區`。

---

## [v1.3.0] - 2026-07-30

### 🎉 v1.3.0 里程碑：Smart Cache Finder 智慧全碟快取支援

- **新增「Smart Cache Finder」極速全碟快取自動盤點功能**：
  - 全自動精準定位 `%USERPROFILE%`、`AppData\Local`、`AppData\Roaming`、`C:\ProgramData` 及其他本機硬碟（如 `D:\`）。
  - 支援快取資料夾**剪枝優化 (Pruning)**，全流程盤點僅需 3~5 秒。
  - 支援 **> 50 MB 快取巨頭門檻過濾**，避免資訊過載。
- **新增智慧 GB / MB 容量單位動態轉換**。
- **強化 Windows 唯讀檔案權限處置**。

---

## [v1.2.0] - 2026-07-30

### 🚀 開源技術大一統升級 (BleachBit, Mem Reduct, Optimizer 借鏡)

- **新增常用應用軟體快取清理 (`clean_app_cache`)**。
- **新增 Windows 原生 `EmptyWorkingSet` API 深度 RAM 壓縮 (Mem Reduct 借鏡)**。
- **新增模擬細節預覽對話框 (`PreviewDialog` - Optimizer 借鏡)**。

---

## [v1.0.0] - 2026-07-28

### 🎉 專案初始發布 (Initial Release)

- **基礎架構確立**：Python 3 + CustomTkinter 現代化深色 UI。
