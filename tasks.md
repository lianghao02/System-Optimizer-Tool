# 原子化工作清單 (tasks.md)

## 📌 當前狀態
- [x] **v6.0.0 核心遷移**：C# .NET 8 原生架構、Win32 記憶體釋放、快取清理、開機自啟動讀取。
- [x] **v6.1.0 功能精進**：
  - [x] 擴充 16+ 快取規則（縮圖、DirectX、NVIDIA、VS Code、Discord、Spotify）
  - [x] 磁碟巨型大檔案透視（Top 50 > 100MB，支援檔案總管定位）
  - [x] Windows 系統匣（NotifyIcon）常駐與右鍵選單
  - [x] 快取 CheckBox 自由勾選與 MB/GB 格式化
  - [x] 記憶體三段式動態警示色彩進度條
- [x] **v6.2.1 發布系統強化**：
  - [x] 支援雙版本發布機制：輕量版 Slim (0.34MB，需 Runtime) 與 零依賴獨立免安裝版 Standalone (68.4MB，內建 Runtime)。
  - [x] 啟動腳本自動優先啟動免安裝獨立版。
- [x] **專案環境與舊資料清理**：清理 2,479 個舊檔案 (55.6MB)，專案庫精簡至 0.63 MB，更新 `.gitignore`。
- [x] **單元測試驗證**：xUnit 3/3 測試通過 (5ms)。

---

## 🎯 Codex 後續迭代待辦事項 (Roadmap)

### Phase 1: 高價值互動與自動化 (High ROI)
- [ ] **開機項「安全停用/啟用」Toggle 開關**：
  - 在 `StartupManager.cs` 實作讀寫 `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run`。
  - 在 UI ListView 加入 Toggle 開關，讓使用者無需刪除即可暫時停用自啟動軟體。
- [ ] **🛡️ UAC 管理員無縫提權模式**：
  - 偵測 `WindowsIdentity.GetCurrent()` 是否為 Admin。
  - 若否，在 Header 提供提權按鈕，點擊後透過 `ProcessStartInfo { Verb = "runas" }` 重啟自身。
- [ ] **記憶體高壓背景自動降壓 (Auto-Pilot)**：
  - 新增設定選項：「當實體記憶體佔用持續 > 85% 超過 10 秒時，自動於背景執行工作集修剪」。

### Phase 2: 深度儲存分析 (Storage Intelligence)
- [ ] **下載資料夾過期體檢**：
  - 專屬掃描 `%USERPROFILE%\Downloads`，列出 > 30 天未存取之安裝包（`.exe`, `.msi`, `.iso`, `.zip`）。
- [ ] **重複大檔案快速篩選 (Duplicate Finder)**：
  - 兩段式比對：檔案大小 ➔ 首尾 4KB Hash ➔ SHA-256。
- [ ] **清理歷史與空間釋放儀表板**：
  - 於 `%LOCALAPPDATA%\SystemOptimizer\stats.json` 記錄累計釋放 GB 數並呈現在介面上。

### Phase 3: 視覺打磨 (Visual Polish)
- [ ] **莫蘭迪深色主題 (Dark Morandi Theme)**：
  - 加入深灰藍配色（`#1E222B`, `#2A303C`），支援一鍵切換或跟隨 Windows 系統外觀。

---

## 目前實作計畫：清理安全與可觀測性

### 目標與驗收條件
- [x] 清理前顯示已選目標、檔案數、預估可釋放空間，並取得明確確認。
- [x] 快取掃描與清理可顯示進度並由使用者取消。
- [x] 略過或失敗的檔案數與原因能回報給使用者。
- [x] 記憶體最佳化明確呈現操作前後數據與非永久釋放限制。
- [x] 以測試暫存資料夾驗證掃描與清理不會穿透目錄連結。

### 不做範圍
- 不新增自動清理、排程、系統管理員提權或刪除既有快取規則。
- 不改變發行模式、全域設定或外部相依套件。

### 風險與驗證
- 目錄連結測試僅操作測試暫存目錄；若環境禁止建立連結，測試必須清楚失敗而非誤報通過。
- 完成後執行 `dotnet test SystemOptimizer.sln --no-restore --nologo` 與 WPF 專案建置。

### 驗證紀錄
- `dotnet build src\\SystemOptimizer.App\\SystemOptimizer.App.csproj --no-restore --nologo`：成功，0 個警告、0 個錯誤。
- `dotnet test SystemOptimizer.sln --no-restore --nologo`：6/6 通過，包含實際建立測試暫存 Junction 後確認掃描與清理皆不會觸及連結外檔案。

---

## 目前實作計畫：掃描效能與結果可用性

### 目標與驗收條件
- [x] 快取掃描完成後完整釋放取消狀態與進度列。
- [x] 大檔案掃描只保留 Top 50 候選檔案，不累積整顆磁碟的結果。
- [x] 掃描略過無法存取目錄，並顯示已掃描目錄與候選檔案數。
- [x] 大檔案結果支援類型、修改時間與最小容量篩選。
- [x] 瀏覽器程序偵測後釋放 `Process` 物件。

### 不做範圍
- 不改變掃描目標、清理規則或發布模式；不新增外部套件。

### 驗證方式
- 執行既有單元測試並新增 Top 50 服務測試；無法存取目錄以 `EnumerationOptions.IgnoreInaccessible` 與建置驗證，未變更實際磁碟 ACL。

### 驗證紀錄
- `dotnet build SystemOptimizer.sln --no-restore --nologo`：成功，0 個警告、0 個錯誤。
- `dotnet test SystemOptimizer.sln --no-restore --nologo`：7/7 通過；新增測試確認 3 個候選檔案以 Top 2 掃描時只保留最大的 2 筆。
