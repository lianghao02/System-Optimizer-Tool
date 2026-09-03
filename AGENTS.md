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
- **清理策略與分級原則（防範過度清理）**：
  - **一般清理（低副作用）**：使用者暫存檔（`Temp`）、系統崩潰傾印（`CrashDumps`）、傳遞最佳化快取等。
  - **進階/謹慎清理（需明確提示副作用）**：
    - 瀏覽器快取（Chrome / Edge Cache）：**預設不主動勾選強制清除**，避免造成使用者網頁首次載入延遲或圖片重新讀取。
    - Windows 檔案總管縮圖快取（`Explorer` 縮圖）：清理後開啟資料夾需重新產生縮圖，屬進階維護項目。
    - DirectX / NVIDIA 著色器快取（Shader Cache）：清理後遊戲或 3D 繪圖初期可能出現微頓挫，應明確標示。
- **Win32 安全防線**：
  - 快取清理前必須透過 `SafetyGuard` 進行系統目錄防護與白名單過濾，且嚴格禁止遞迴遍歷目錄連結（Directory Junction）。
  - 遇到鎖定或無存取權限檔案必須安全略過（Catch and Skip），並將略過項目與原因如實呈報。
- **記憶體釋放語意透明性**：
  - Working Set 與 Standby List 釋放僅為輔助診斷與深度釋放，不包裝為「日常必須無止盡執行」的神話功能。
  - 操作完成後必須即時回傳前後記憶體變化數值、略過之系統處理程序數，若 Standby List 無法清除需說明具體原因（如權限或系統調度）。

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

