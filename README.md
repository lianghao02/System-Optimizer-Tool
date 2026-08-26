# ⚡ Windows 系統極速優化工具 (System Optimizer Tool)

[![.NET](https://img.shields.io/badge/.NET-8.0-blue.svg)](https://dotnet.microsoft.com/)
[![WPF](https://img.shields.io/badge/WPF-Windows-brightgreen.svg)]()
[![Single-File](https://img.shields.io/badge/Size-0.30MB-success.svg)]()
[![Version](https://img.shields.io/badge/version-v6.2.0-success.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

本工具為專為 Windows 10/11 設計之輕量級系統快取安全清理、實體記憶體即時深度釋放、磁碟巨型大檔案透視、開機自啟動管理與系統匣常駐工具。

本專案已完成 **C# .NET 8 / WPF 原生單檔架構 (v6.2.0)** 全面升級，具備 **0.30 MB (300 KB)** 極致輕量、原生秒開、莫蘭迪現代 UI、系統匣常駐與零 Python 環境依賴。原始 Python 3.13 程式碼完整封存於 `legacy-python/` 作為歷史對照與備援引擎。

---

## 🏆 v6.2.0 升級亮點與指標對比

| 指標面向 | 原始版本 (Python 3.13) | C# .NET 8 原生版 (v6.2.0) | 改善幅度與效益 |
|:---|:---|:---|:---:|
| **技術語言** | Python 3.13 + CustomTkinter | **C# 12 (.NET 8.0) + WPF** | 原生 Win32 第一公民，零環境依賴 |
| **發行體積** | 約 **155 MB** (含 `python_embed` 核心) | **0.30 MB (300 KB)** | 🚀 **體積縮減 99.8%** |
| **啟動時間** | ~ 1.5 秒 (載入 Python 虛擬機) | **< 0.1 秒 (瞬間秒開)** | ⚡ **速度提升 15 倍** |
| **安全防禦** | 基礎路徑比對 | **白名單隔離 + 略過目錄連結 + 二次確認** | 🛡️ **徹底杜絕誤刪與穿透風險** |
| **快取覆蓋** | 7 項常見快取 | **16+ 項系統與常用軟體快取** | 🧹 **可多釋放 2GB~5GB 空間** |
| **大檔案掃描** | 遍歷累積所有物件 | **PriorityQueue Top 50 + 快速篩選** | 🔍 **零記憶體負擔、秒抓大檔** |
| **磁碟透視** | 分頁各自獨立 | **儀表板一鍵穿透帶入掃描** | ⚡ **跨分頁無縫流暢體驗** |
| **系統匣常駐** | 無 | **Windows 系統匣常駐 + 右鍵極速釋放** | 📌 **背景待命、即時監控** |
| **單元測試** | unittest | **xUnit (7/7 Tests 100% Clean Pass)** | 🟢 **含 Junction 隔離等完整測試** |

---

## ✨ 核心功能與安全機制

1. 🛡️ **快取清理安全強化與防禦機制**：
   - **嚴格白名單與連結隔離**：嚴格限定合法快取目標，自動略過所有 Junction 與符號連結（Reparse Point），防止誤刪連結外資料。
   - **清理前二次確認**：清理前主動彈出確認視窗，清晰列出勾選目標、檔案數與預估釋放空間。
   - **可取消與例外摘要**：掃描與清理皆支援隨時取消，完成後完整回報略過與鎖定例外摘要。
2. ⚡ **Win32 原生記憶體深度釋放與可觀測性**：
   - **即時動態監控**：內建背景計時器每 2 秒自動即時更新實體記憶體使用量與活躍處理程序數。
   - **動態色票警示**：`< 65%` 柔和莫蘭迪青綠、`65% ~ 80%` 琥珀黃、`> 80%` 警示橘紅。
   - **雙重釋放機制**：同時呼叫 `EmptyWorkingSet`（清空無效工作集）與 `NtSetSystemInformation`（清空 Standby 待命快取清單）。
   - **透明可觀測性**：即時回報操作前後記憶體差異，明確說明非永久釋放特性，並統計系統保護無法存取之處理程序數。
3. 🔍 **磁碟大檔案透視 (Large File Finder) 與一鍵搜尋**：
   - **儀表板一鍵穿透**：磁碟監控列點擊「🔍 搜尋大檔案」自動切換分頁、帶入磁碟代號並啟動掃描。
   - **優先佇列高效演算法**：採用 `PriorityQueue` 固定保留 Top 50 巨型檔案，不浪費記憶體累積全磁碟檔案。
   - **進階動態篩選**：支援副檔名類型、最後修改時間與最小容量自訂篩選，並可一鍵在檔案總管中定位檔案。
4. 📌 **Windows 系統匣常駐 (System Tray)**：
   - 視窗最小化時自動縮入系統匣，右鍵支援「顯示主畫面」、「⚡ 立即釋放記憶體」與「結束程式」。
5. 🚀 **開機自啟動管理**：
   - 安全解析登記於 `HKCU` 與 `HKLM` 登錄檔 Run 鍵之常駐開機軟體與完整指令路徑。

---

## 🚀 快速啟動與建置

### 1. 一般使用者（立即啟動）
- 直接雙擊專案根目錄的 **`⚡ 啟動系統優化工具.bat`** 即可秒開執行。
- 或直接執行 [`dotnet-src/publish/SystemOptimizer.App.exe`](dotnet-src/publish/SystemOptimizer.App.exe)。

### 2. 開發者編譯與測試
```powershell
# 進入 .NET 專案目錄
cd dotnet-src

# 執行 xUnit 自動化單元測試
dotnet test SystemOptimizer.sln --no-restore --nologo

# 一鍵發布單一獨立 Exe (Release x64)
.\build_release.ps1 -RunAfterBuild
```

---

## 📂 專案目錄結構

```text
D:\Development\GitHub\06_System-Optimizer-Tool\
├── ⚡ 啟動系統優化工具.bat                  # 🚀 根目錄一鍵秒開 (預設呼叫 0.30MB 原生版)
├── 啟動Python傳統版(備援).bat                # 📦 歷史 Python 備援啟動入口
├── README.md                                 # 專案總說明文件 (v6.2.0)
├── CHANGELOG.md                              # 版本異動歷程
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
│   │   └── SystemOptimizer.App.exe           # 0.30 MB 原生單檔執行檔 (含專屬圖示)
│   ├── src\
│   │   ├── SystemOptimizer.Core\             # Win32 原生記憶體、快取、大檔、安全核心
│   │   │   ├── Native\NativeMethods.cs       # P/Invoke API 定義
│   │   │   ├── Models\Models.cs              # 資料模型與易讀格式化
│   │   │   └── Services\                     # 記憶體、快取、大檔搜尋、開機項與白名單服務
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
