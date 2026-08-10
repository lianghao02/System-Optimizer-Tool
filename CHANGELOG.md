# 📝 更新紀錄 (CHANGELOG)

---

## [v5.0] - 2026-08-10

### 🏆 v5.0 里程碑：全碟儲存空間分析器與宣告式快取規則表

- **全碟儲存空間診斷與分析儀表板 (`engine/storage_analyzer.py`)**：
  - **🔍 巨型檔案分析器 (Large File Inspector)**：全自動盤點 >500MB 巨型標的（系統 ISO / 大型壓縮檔 / 影音檔 / 日誌與 Dump / AI `.gguf` 模型）。
  - **🕒 長期未使用檔案分析 (Long Unused File Inspector)**：組合檔案容量、最後修改時間 (Last Modified Time) 與路徑，分類標示 90 / 180 / 365 / 730 天，標註 **「可能長期未使用」**。
  - **👯 三階段 SHA-256 重複檔案分析器 (3-Stage Duplicate Finder)**：容量初篩 -> 首尾 64KB 快速 Hash -> 完整 SHA-256 雜湊比對。預設全部不勾選，絕不單憑檔名判斷。
  - **📥 Downloads 下載資料夾健檢 (Downloads Health Checker)**：診斷放置 >180 天之舊版軟體安裝檔 (`*.exe`, `*.msi`) 與冗餘同名解壓封存檔。
  - **視窗互動與精準定位 (`StorageAnalyzerDialog`)**：彈出多分頁診斷視窗，提供 `📂 開啟位置` 精準定位。

- **宣告式 Cache Rule 規則表機制 (`engine/cache_rules.py`)**：
  - 新增 `CacheRule` 與 `CacheRuleRegistry` 宣告式規則表，支援瀏覽器與 IDE 執行中軟體鎖定檢測 (`requires_closed_app`)。

---

## [v4.0] - 2026-08-10

### 🏆 v4.0 重大升級：三層安全架構、RAM 獨立管理與大型快取分析器

- **職責純化與獨立模組拆分 (Modular Taxonomy)**：
  - 新增 `engine/memory.py` 與 `engine/cache_inspector.py`。
- **三層安全防禦與 UI 重構 (3-Tier Safety UI)**：
  - 🟢 第一層：安全清理 / 🟡 第二層：可重建快取 / 🔴 第三層：進階操作。
- **軟體卸載多維度信心分數與取消防禦 (Uninstaller Refinements)**。
