# 06_System-Optimizer-Tool Agent 開發規範

本專案遵循目前有效之全域開發憲法；本檔僅定義專案專屬規則與例外。

---

## 1. 技術棧與建置規範
- **主力引擎**：C# 12 / .NET 8.0 WPF（位於 `dotnet-src/`）。保持原生 Win32、無外部大型依賴與極致秒開架構。
- **發布標準**：`build_release.ps1` 雙版本發布：
  - `publish/standalone/SystemOptimizer.App.exe`：免安裝獨立單檔（內嵌 Runtime，約 68MB，一般使用者優先）。
  - `publish/slim/SystemOptimizer.App.exe`：極致輕量版（< 0.5 MB，需本機 .NET 8 Runtime）。
- **.NET SDK 本機環境**：`.NET 8.0.406 SDK` 位於 `%LOCALAPPDATA%\Microsoft\dotnet`。執行 `dotnet` CLI 時需確保 `DOTNET_ROOT` 指向該目錄，且 `PATH` 優先置入。
- **歷史備援界限**：原始 Python 程式碼封存於 `legacy-python/` 作為歷史功能備援與比對，未經指示請勿隨意修改或刪除。

---

## 2. 安全清理與記憶體優化邊界
- **快取清理防過度清理原則（副作用揭露）**：
  - **一般暫存（低副作用）**：應用程式執行暫留檔（`Temp`）、系統錯誤傾印（`CrashDumps`）、安裝過渡檔等無後續效能代價之項目。
  - **進階快取（具備重建成本與效能代價）**：
    - 任何應用程式或瀏覽器之網頁/媒體快取：**不得視為一般垃圾預設勾選清除**，避免造成使用者後續存取延遲或重新下載卡頓。
    - 縮圖快取與 3D/著色器快取（Shader Cache）：清理後需重新運算產生，可能導致介面滾動或圖形載入初期微頓挫；此類項目應列為進階維護選項，並明確提示潛在副作用。
- **Win32 安全防線**：
  - 快取清理前必須透過系統核心目錄白名單保護，且嚴格禁止遞迴遍歷目錄連結（Directory Junction）。
  - 遇到鎖定或無存取權限檔案必須安全略過（Catch and Skip），並將略過項目與原因如實呈報。
- **記憶體釋放語意透明性**：
  - 工作集（Working Set）與待命快取（Standby List）清理屬輔助性深度釋放，嚴禁包裝為「日常必須頻繁執行」的神化功能。
  - 操作完成後必須如實回報前後記憶體容量變化與略過之系統處理程序數；若系統快取無法清除需說明具體原因（如權限或系統調度）。

---

## 3. UI/UX 狀態語意與驗證
- **狀態回饋原則**：
  - 掃描、清理與記憶體釋放等長時間操作，必須維持非同步背景執行，嚴禁阻塞 UI 主執行緒。
  - 明確反饋：目前掃描目錄、進度百分比、已略過檔案數、操作成功或取消狀態。
- **核心驗證方式**：
  - 修改 Core 或 UI 邏輯後，必須執行單元測試：
    ```powershell
    $env:DOTNET_ROOT = "$env:LOCALAPPDATA\Microsoft\dotnet"
    $env:PATH = "$env:LOCALAPPDATA\Microsoft\dotnet;$env:PATH"
    dotnet test dotnet-src\SystemOptimizer.sln --no-restore --nologo
    ```

