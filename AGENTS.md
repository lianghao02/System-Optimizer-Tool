# 06_System-Optimizer-Tool Agent 開發規範

本檔為 `06_System-Optimizer-Tool` 專屬邊界限制；全域開發憲法請參閱 `00_home\configs\AGENTS.md`。

---

## 1. 技術棧與建置規範
- **主力引擎**：C# 12 / .NET 8.0 WPF（位於 `dotnet-src/`）。
- **發布標準**：必須維持單檔免安裝獨立執行檔（`PublishSingleFile=true`，體積維持在 **< 0.5 MB**）。
- **.NET SDK 本機路徑**：`.NET 8.0.406 SDK` 安裝於 `%LOCALAPPDATA%\Microsoft\dotnet`。在執行 `dotnet` CLI 指令時需確保 `DOTNET_ROOT` 指向該目錄，且 `PATH` 優先於 `C:\Program Files\dotnet`。
- **建置腳本**：一鍵建置發布請執行 `dotnet-src\build_release.ps1`。

---

## 2. 架構與防禦原則
- **雙引擎分流**：C# 為主力（`dotnet-src/`）；原始 Python 程式碼完整封存於 `legacy-python/` 作為備援對照，未經指示請勿隨意刪除。
- **Win32 安全第一**：所有快取清理與工作集修剪必須經過 `SafetyGuard` 系統核心目錄白名單保護，遇到鎖定中的檔案必須安全略過（Catch and Skip），嚴禁造成系統異常。
- **100% 台灣繁體中文**：所有註解、UI 字串、Commit 訊息一律使用標準繁體中文（如：即時、處理程序/程式、專案、登錄檔、記憶體、快取）。
