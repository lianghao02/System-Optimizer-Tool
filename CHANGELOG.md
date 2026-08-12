# 📜 版本變更紀錄 (CHANGELOG)

## [v5.0] - 2026-08-10

### 🏆 v5.0 里程碑：全碟儲存空間診斷儀表板與宣告式快取規則表

- **📊 全碟儲存空間診斷儀表板 (`engine/storage_analyzer.py`)**：
  - **🔍 巨型檔案分析器 (Large File Inspector)**：全自動盤點 >500MB 巨型標的（系統 ISO / 大型壓縮檔 / 影音檔 / 日誌與 Dump / AI `.gguf` 模型）。
  - **🕒 長期未使用檔案分析 (Long Unused File Inspector)**：組合檔案容量、最後修改時間 (Last Modified Time) 與路徑，分類標示 90 / 180 / 365 / 730 天，標註 **「可能長期未使用」**。
  - **👯 三階段 SHA-256 重複檔案分析器 (3-Stage Duplicate Finder)**：容量大小初篩 -> 首尾 64KB 快速 Hash -> 完整 SHA-256 內容比對。預設全部不勾選，絕不單憑檔名判斷。
  - **📥 Downloads 下載資料夾健檢 (Downloads Health Checker)**：診斷放置 >180 天之舊版軟體安裝檔 (`*.exe`, `*.msi`) 與冗餘壓縮檔 (同名資料夾並存者)。
  - **視效互動與精準定位 (`StorageAnalyzerDialog`)**：提供全碟診斷視窗與 `📂 開啟位置` 精準定位。
- **⚙️ 宣告式 Cache Rule 規則表與鎖定檢測 (`engine/cache_rules.py`)**：
  - 導入 `CacheRule` 與 `CacheRuleRegistry` 宣告式規則表，支援瀏覽器與 IDE 執行中實體鎖定檢測 (`requires_closed_app`)。

---

## [v4.0] - 2026-08-10

### 🚀 v4.0 重大更新：三層安全架構、RAM 管理與大型快取分析器

- **職責純化與獨立模組解耦 (Modular Taxonomy)**：
  - 抽離 `engine/memory.py` 與 `engine/cache_inspector.py`。
- **三層安全防禦 UI 介面 (3-Tier Safety UI)**：
  - 🟢 第一層：安全清理 / 🟡 第二層：可重建快取 / 🔴 第三層：進階操作與模擬開關。
- **軟體徹底卸載與多維度信心分數殘留掃蕩 (Uninstaller Refinements)**：
  - 支援兩階段殘留確認與取消卸載防禦機制。

---

## [v1.1.0] - 2026-08-10

- **核心架構更新**：系統清理模組適應 D 碟自適應啟動邏輯。
- **環境優化**：減少 C 碟與 D 碟開發環境衝突，重置 D:\Caches 專用快取（`HF_HOME` / `PIP_CACHE_DIR` / `PLAYWRIGHT_BROWSERS_PATH`）。
- **架構重構**：專案資料夾前綴數字命名法，完全相容全域憲法與 `AGENTS.md`。
