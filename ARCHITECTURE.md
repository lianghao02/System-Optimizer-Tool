# 系統架構說明書 (ARCHITECTURE)

## 1. 系統全貌與目錄結構

專案採用 **單一 Repository 雙引擎分流架構**：

```text
06_System-Optimizer-Tool/
├── ⚡ 啟動系統優化工具.bat                  # 🚀 根目錄一鍵秒開捷徑
├── 啟動Python傳統版(備援).bat                # 📦 歷史 Python 備援啟動入口
├── README.md                                 # 專案總說明文件 (v6.1.0)
├── CHANGELOG.md                              # 版本異動紀錄
├── AGENTS.md                                 # Agent 專案規範
├── ARCHITECTURE.md                           # 本架構說明書
├── MEMORY.md                                 # 關鍵技術決策與踩坑歷史
├── tasks.md                                  # 當前進度與後續待辦清單
│
├── dotnet-src/                               # 🌟【主力發行】C# .NET 8 WPF 原生單檔引擎
│   ├── SystemOptimizer.sln                   # Visual Studio 解決方案檔
│   ├── build_release.ps1                     # 一鍵建置發布腳本
│   ├── publish/
│   │   └── SystemOptimizer.App.exe           # 0.30 MB 原生單檔執行檔
│   ├── src/
│   │   ├── SystemOptimizer.Core/             # Win32 原生記憶體、快取、大檔、白名單核心
│   │   │   ├── Native/NativeMethods.cs       # P/Invoke API 定義 (EmptyWorkingSet, NtSetSystemInformation)
│   │   │   ├── Models/Models.cs              # 系統指標、快取項目 (MB/GB 格式化)、大檔案模型
│   │   │   └── Services/                     # 記憶體、快取、大檔搜尋、開機項與安全服務
│   │   └── SystemOptimizer.App/              # 莫蘭迪現代 WPF UI 介面
│   │       ├── Styles/MorandiTheme.xaml      # 膠囊導航與莫蘭迪樣式庫
│   │       ├── ViewModels/MainViewModel.cs   # 即時監控 (2秒計時器)、大檔搜尋與命令調度層
│   │       ├── MainWindow.xaml.cs            # 系統匣 NotifyIcon 常駐支援
│   │       └── app_icon.ico                  # 多解析度專屬圖示 (256x256 ~ 16x16)
│   └── tests/
│       └── SystemOptimizer.Tests/            # xUnit 自動化單元測試套件
│
└── legacy-python/                            # 📦【歷史備援】原始 Python 3.13 引擎
    ├── main.py                               # 原始 CustomTkinter 入口
    ├── engine/                               # 原始 Python 邏輯模組
    ├── ui/
    ├── requirements.txt
    └── setup_and_run.ps1
```

---

## 2. 核心模組職責劃分

### 2.1 `SystemOptimizer.Core` (純邏輯與 Win32 API 層)
- **`NativeMethods.cs`**：
  - `EmptyWorkingSet(IntPtr hProcess)`：清空指定處理程序的工作集。
  - `NtSetSystemInformation`（呼叫 `SystemMemoryListInformation / MemoryPurgeStandbyList`）：釋放 Windows 待命快取清單（Standby List）。
  - `GlobalMemoryStatusEx`：精確讀取實體記憶體總量、可用量與負載百分比。
- **`MemoryOptimizer.cs`**：
  - 封裝程序遍歷與工作集修剪，自動略過拒絕存取的系統級處理程序，無死鎖風險。
- **`CacheCleaner.cs`**：
  - 宣告 16+ 種常見快取目標（Windows Temp、Prefetch、CrashDumps、更新快取、縮圖快取、DirectX/NVIDIA 著色器快取、Chrome/Edge/VSCode/Discord/Spotify 快取）。
  - 內建處理程序鎖定檢測與安全防刪白名單。
- **`StorageAnalyzer.cs`**：
  - 本機固定磁碟可用容量透視。
  - `ScanLargeFilesAsync`：BFS 遍歷遞迴搜尋巨型大檔案 Top 50，自動略過 Junction / ReparsePoint 與系統隱藏目錄。
- **`SafetyGuard.cs`**：
  - 嚴格防刪白名單機制，禁止對 `C:\Windows`, `C:\Program Files` 根目錄等關鍵路徑進行非快取性刪除。

### 2.2 `SystemOptimizer.App` (WPF MVVM 表現層)
- **`MainViewModel.cs`**：
  - 驅動 2 秒自動即時動態記憶體更新（`DispatcherTimer`）。
  - 動態色票計算（`<65%` 莫蘭迪青綠、`65%~80%` 琥珀黃、`>80%` 警示橘紅）。
  - 大檔案掃描與「在檔案總管中定位」命令。
- **`MainWindow.xaml`**：
  - 現代膠囊分段導航標籤列（Segmented Pills TabControl）。
  - 莫蘭迪淺色調色盤（`#F3F5F8` 底色、`rgba(255,255,255,0.85)` 卡片）。
- **`MainWindow.xaml.cs`**：
  - Windows 系統匣（`NotifyIcon`）常駐與右鍵選單控制。
