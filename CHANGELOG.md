# 📝 更新紀錄 (CHANGELOG)

---

## [v4.0] - 2026-08-10

### 🏆 v4.0 重大升級：三層安全架構、RAM 獨立管理與大型快取分析器

- **職責純化與獨立模組拆分 (Modular Taxonomy)**：
  - 新增 `engine/memory.py`：完全解耦記憶體狀態查詢、Working Set 頁面縮減與 Toolhelp32 進程快照。
  - 新增 `engine/cache_inspector.py`：獨立收容 `Smart Cache Inspector` 大型快取分析器，未知項目 100% 只讀不自動刪除。
  - 純化 `engine/config.py`：回歸 100% 設定、常數、路徑、JSON 與白名單管理，不執行系統操作。

- **三層安全防禦與 UI 重構 (3-Tier Safety UI)**：
  - 🟢 **第一層：安全清理 (預設推薦勾選)**：使用者 Temp、CrashDumps、WER、Delivery Optimization、瀏覽器與開發套件快取。
  - 🟡 **第二層：可重建快取 (預設不勾選)**：顯示卡 Shader Cache、縮圖快取、IDE 索引快取與大型快取分析器。
  - 🔴 **第三層：進階操作 (獨立執行與預設不勾選)**：Prefetch 系統預載、Working Set 分頁暫時釋放按鈕、閒置進程關閉。

- **軟體卸載多維度信心分數與取消防禦 (Uninstaller Refinements)**：
  - 實作多維度信心分數 (Confidence Score) 殘留分析算法 (名稱匹配+40、InstallLocation+25、Publisher+15、主程式名+10)。
  - **取消防禦機制**：官方卸載精靈若遭取消，重新比對註冊表後自動終止殘留掃蕩，絕不誤刪資料。
  - **兩階段預覽確認**：彈出 `ResidualsPreviewDialog` 視窗，未經使用者勾選 100% 不直接刪除資料夾。

- **README 客觀用語收斂**：
  - 嚴格聲明「不修改登錄檔最佳化參數、不停用 Windows 系統服務、不變更電源計畫與核心安全設定」。

---

## [v3.2] - 2026-08-04

### 🏆 v3.2 精簡極致升級：純粹直覺的開機啟動資料夾直達工具

- **頁籤二全面極簡重構**：
  - 移除過度複雜的登錄檔與排程器區塊，專注兩大 Windows 原生開機資料夾一鍵直達。
