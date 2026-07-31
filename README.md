# ⚡ 系統快取清理與記憶體優化工具 System-Optimizer-Tool (v2.6 UI 美化全能版)

[![Version](https://img.shields.io/badge/version-v2.6-blue.svg)](https://github.com/lianghao02/System-Optimizer-Tool)
[![Win32](https://img.shields.io/badge/API-Win32%20EmptyWorkingSet-red.svg)](https://microsoft.com)
[![UI](https://img.shields.io/badge/UI-CustomTkinter%20v2.6-purple.svg)](https://github.com/TomSchimansky/CustomTkinter)

## 🏆 v2.6 重大里程碑：深紫藍現代 UI 美化、開機啟動批次停用與 Geek 軟體徹底卸載

本工具為專為 Windows 系統設計之效能優化與維護工具，採用 Python `CustomTkinter` 深紫藍現代 UI 介面與 Windows 原生 `Win32 API`。

完全遵循**台灣繁體標準資訊術語**與**直覺語意動作按鈕**，絕無任何廣告、暗藏惡意程式或簡體用語，提供純淨且軍規級安全的優化體驗。

---

## ✨ 四大核心功能模組

### 🧹 1. 快取與記憶體優化 (Cache & RAM Optimizer)
- 🟢 **第一類：無害系統與套件快取**：`%TEMP%` 暫存區、`CrashDumps` 崩潰傾印檔、`WER` 系統錯誤報告、微軟傳遞優化下載快取 (`Delivery Optimization`) 及開發套件包快取 (`pip`, `uv`, `npm`, `pnpm`, `Yarn`, `Poetry`)。
- 🟡 **第二類：輕微影響快取**：多瀏覽器快取 (Chrome / Edge / Brave / Firefox)、顯卡與 DirectX 著色器快取 (DirectX / NVIDIA / AMD)、檔案總管縮圖快取及常用軟體/IDE 快取 (VS Code / JetBrains / Adobe Media Cache)。
- 🚀 **Win32 原生記憶體深度壓縮**：調用 Windows 原生 `EmptyWorkingSet` API，瞬間縮減背景閒置處理程序佔用之記憶體分頁。

### 🚀 2. 開機加速與背景項目管理 (Boot & Startup Manager)
- 📊 **開機健康度監測**：即時讀取系統連續運行時間與開機狀態。
- 🔍 **啟動項目自動盤點**：自動掃描登錄檔 (Registry `Run`/`RunDisabled`)、Startup 啟動資料夾與 Windows 工作排程器 (`Schtasks`)。
- 🔤 **友善繁體中文對照**：解析執行檔 Win32 版本資訊，將難懂的英文登錄檔鍵值轉換為明確的軟體名稱與開機用途說明。
- ☑️ **批次勾選與雙向開關**：提供左側勾選框與「批次停用」功能；停用後項目依然保留在清單中（標示 `🛑 [已關閉]`），隨時可點擊復原。
- 📅 **工作排程器彈性開關**：預設隱藏背景更新排程，提供勾選框供使用者自主展開檢視。
- 📝 **自訂開機腳本延遲啟動**：支援 `.exe`, `.lnk`, `.bat`, `.cmd`, `.py`, `.ps1` 新增與延遲啟動設定，並提供單鍵試跑測試。

### 🗑️ 3. 軟體徹底卸載與殘留清理 (Geek Uninstaller Style)
- 📋 **本機軟體庫盤點**：讀取 Registry 安裝清單，顯示軟體類型標籤 (`📦 [應用軟體]` / `🛡️ [系統必備元件]`)、安裝日期與估算容量。
- 🔍 **即時過濾與安全防護**：提供關鍵字搜尋列，預設開啟「隱藏系統必備元件」切換，防止誤刪系統驅動或核心元件。
- 🗑️ **官方卸載與深層殘留掃蕩**：呼叫官方卸載程序後，自動深度掃描 `AppData\Local`, `AppData\Roaming`, `C:\ProgramData` 殘留資料夾並提供一鍵清理。

### ⚙️ 4. 設定與保護白名單 (Settings & Whitelist)
- 🛡️ 彈性編輯保護白名單關鍵字 (`PROTECTED_KEYWORDS`)，絕對保護關鍵專案檔案、原始碼與系統服務。

---

## 🎨 v2.6 介面視覺與美化重點

1. **深紫藍調色盤**：背景採用深邃藍黑 (`#0F0F17`)、側邊欄 (`#13131E`) 與卡片區塊 (`#1A1A28`)，搭配霓虹藍主色 (`#5B7BFE`) 與翠綠標籤 (`#2ECC8A`)。
2. **圖示與邊界對齊**：修正 emoji 寬度導致按鈕文字對齊偏差問題，側邊欄與頁首佈局重新調配。
3. **清楚語意按鈕**：所有動作按鈕（如 `⚡ 刪除勾選暫存與釋放記憶體`、`🚫 批次停用所有勾選的開機啟動項`、`🗑️ 卸載軟體並清理殘留`）皆明確標註行為。

---

## 🚀 快速啟動方式

1. **安裝相依套件**：
   ```bash
   pip install customtkinter
   ```
2. **執行工具**：
   ```bash
   python main.py
   ```
   或直接雙擊執行 `啟動工具.bat`。