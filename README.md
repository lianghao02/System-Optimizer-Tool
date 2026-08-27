# ⚡ Windows 系統極速優化工具 (System Optimizer Tool)

[![.NET](https://img.shields.io/badge/.NET-8.0-blue.svg)](https://dotnet.microsoft.com/)
[![WPF](https://img.shields.io/badge/WPF-Windows-brightgreen.svg)]()
[![Releases](https://img.shields.io/badge/Release-v6.2.1-success.svg)](https://github.com/lianghao02/System-Optimizer-Tool/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

本工具為專為 Windows 10/11 設計之輕量級系統快取安全清理、實體記憶體即時深度釋放、磁碟巨型大檔案透視、開機自啟動管理與系統匣常駐工具。

本專案已完成 **C# .NET 8 / WPF 原生單檔架構 (v6.2.1)** 全面升級，提供**零環境依賴免安裝版**與**極致輕量版**雙版本，原生秒開、莫蘭迪現代 UI、系統匣常駐與安全白名單防禦。

---

## 📥 下載與安裝指引 (Download & Quick Start)

前往 👉 **[GitHub Releases 最新版本發布頁](https://github.com/lianghao02/System-Optimizer-Tool/releases)** 下載適合您的版本：

| 下載檔案名稱 | 檔案大小 | 適用情境與說明 | 推薦度 |
|:---|:---:|:---|:---:|
| **`SystemOptimizer-v6.2.1-Standalone-x64.exe`** | ≈ **68 MB** | **【免安裝獨立完整版】** 內嵌完整 .NET 8 執行階段，**任何 Windows 電腦下載後直接雙擊執行**，完全不需安裝任何額外套件或環境。 | 🌟 **強烈推薦** |
| **`SystemOptimizer-v6.2.1-Slim-x64.exe`** | ≈ **0.34 MB** | **【極致輕量版】** 僅 340 KB，需電腦已安裝 [.NET 8 Desktop Runtime](https://dotnet.microsoft.com/download/dotnet/8.0)。適合開發者或已具備執行環境的電腦。 | 💡 自行選用 |

> [!TIP]
> **一般使用者建議直接下載 `SystemOptimizer-v6.2.1-Standalone-x64.exe`**，單一檔案免安裝、即開即用，放到桌面或任何資料夾點擊即可執行。

---

## 📖 核心功能與使用教學

### 1. 🧹 系統快取清理
- 進入「快取清理」分頁，點擊「開始掃描快取」。
- 工具會自動搜尋 16+ 項系統快取（包含 Windows 縮圖快取、DirectX 著色器、NVIDIA 快取、VS Code、Discord、Spotify 等）。
- 勾選欲清理的項目，點擊「執行清理」。清理前系統會跳出**二次確認視窗**，確認後即安全執行（自動跳過鎖定檔案與 Junction 連結）。

### 2. ⚡ Win32 記憶體深度釋放
- 在儀表板或系統匣右鍵選單點擊「⚡ 立即釋放記憶體」。
- 原生呼叫 Win32 底層 API 同時清理無效工作集（Working Set）與待命快取清單（Standby List），操作後即時回報釋放容量。

### 3. 🔍 磁碟大檔案透視 (Large File Finder)
- 進入「大檔案透視」分頁，選擇磁碟機代號並點擊「開始掃描大檔案」。
- 採用高效 PriorityQueue 演算法，秒速抓出磁碟中 Top 50 巨型檔案（> 100MB）。
- 可依副檔名類型、修改時間與容量快速篩選，並支援點擊「在檔案總管中定位」直接前往目標資料夾。

### 4. 📌 Windows 系統匣常駐 (System Tray)
- 點擊視窗右上角「最小化」時，程式會自動縮入右下角 Windows 系統匣。
- 在系統匣圖示點擊滑鼠右鍵，可快速開啟主畫面、立即釋放記憶體或結束程式。

### 5. 🔄 版本與更新檢查
- 主視窗標題列會顯示目前執行版本；版本來源為根目錄 `version.txt`，並會隨建置與發布檔一併帶入。
- 點擊「🔄 檢查更新」會透過 GitHub Release API 非同步查詢最新正式版本：已是最新版會顯示確認訊息；有新版時可直接前往 Release 頁面下載。
- 此功能只讀取公開 Release 資訊，不會自動下載、覆寫或安裝任何檔案。

---

## 🛠️ 開發者編譯與測試

如果您希望從原始碼自行編譯：

```powershell
# 1. 複製專案
git clone https://github.com/lianghao02/System-Optimizer-Tool.git
cd System-Optimizer-Tool/dotnet-src

# 2. 執行 xUnit 自動化單元測試
dotnet test SystemOptimizer.sln --no-restore --nologo

# 3. 一鍵編譯產出雙版本發布檔
.\build_release.ps1
```

---

## 📂 專案目錄結構

```text
D:\Development\GitHub\06_System-Optimizer-Tool\
├── ⚡ 啟動系統優化工具.bat                  # 🚀 根目錄一鍵秒開 (預設呼叫 0.30MB 原生版)
├── 啟動Python傳統版(備援).bat                # 📦 歷史 Python 備援啟動入口
├── README.md                                 # 專案總說明文件 (v6.2.1)
├── CHANGELOG.md                              # 版本異動歷程
├── version.txt                               # 應用程式與 Release 比對版本來源
├── LICENSE                                   # MIT 開源授權條款
├── AGENTS.md                                 # Agent 專屬規範
├── ARCHITECTURE.md                           # 系統架構說明書
├── MEMORY.md                                 # 核心決策與踩坑記憶
├── tasks.md                                  # 原子化工作清單
│
├── dotnet-src\                               # 🌟【主力發行】C# .NET 8 / WPF 原生單檔引擎
│   ├── SystemOptimizer.sln                   # Visual Studio 解決方案檔
│   ├── build_release.ps1                     # 一鍵建置發布腳本
│   ├── publish\
│   │   ├── standalone\SystemOptimizer.App.exe # 約 68 MB、免安裝獨立版
│   │   └── slim\SystemOptimizer.App.exe      # 約 0.34 MB、需 .NET 8 Runtime
│   ├── src\
│   │   ├── SystemOptimizer.Core\             # Win32 原生記憶體、快取、大檔、安全核心
│   │   │   ├── Native\NativeMethods.cs       # P/Invoke API 定義
│   │   │   ├── Models\Models.cs              # 資料模型與易讀格式化
│   │   │   └── Services\                     # 記憶體、快取、大檔搜尋、開機項、白名單與 GitHub 更新服務
│   │   └── SystemOptimizer.App\              # 莫蘭迪現代 WPF UI 介面
│   │       ├── Styles\MorandiTheme.xaml      # 膠囊導航與莫蘭迪樣式庫
│   │       ├── ViewModels\MainViewModel.cs   # 即時監控、大檔搜尋與命令調度層
│   │       ├── MainWindow.xaml               # 現代化主介面配置
│   │       ├── MainWindow.xaml.cs            # 系統匣 NotifyIcon 常駐支援
│   │       └── app_icon.ico                  # 多解析度專屬圖示 (256x256 ~ 16x16)
│   └── tests\
│       └── SystemOptimizer.Tests\            # xUnit 自動化單元測試套件
│
└── legacy-python\                            # 📦【歷史封存】原始 Python 3.13 引擎 (不再維護)
    ├── README.md                             # 歷史封存說明文件
    ├── main.py                               # 原始 CustomTkinter 入口
    ├── engine\                               # 原始 Python 邏輯模組
    ├── ui\
    ├── requirements.txt
    └── setup_and_run.ps1
```

詳細版本異動請參閱 [CHANGELOG.md](CHANGELOG.md)。
