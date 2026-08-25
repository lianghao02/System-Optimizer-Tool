# ⚡ Windows 系統極速優化工具 (System Optimizer Tool)

[![.NET](https://img.shields.io/badge/.NET-8.0-blue.svg)](https://dotnet.microsoft.com/)
[![WPF](https://img.shields.io/badge/WPF-Windows-brightgreen.svg)]()
[![Single-File](https://img.shields.io/badge/Size-0.30MB-success.svg)]()
[![Version](https://img.shields.io/badge/version-v6.1.0-success.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

本工具為專為 Windows 10/11 設計之輕量級系統快取清理、實體記憶體即時深度釋放、磁碟巨型大檔案透視、開機自啟動管理與系統匣常駐工具。

本專案已完成 **C# .NET 8 / WPF 原生單檔架構 (v6.1.0)** 全面升級，具備 **0.30 MB (300 KB)** 極致輕量、原生秒開、莫蘭迪現代 UI、系統匣常駐與零 Python 環境依賴。原始 Python 3.13 程式碼完整封存於 `legacy-python/` 作為歷史對照與備援引擎。

## 技術架構與發行模式（2026-08-24）

- 主力版已完成 **Python／CustomTkinter → C#／.NET 8／WPF** 遷移；現行程式位於 `dotnet-src/`，Python 僅保留於 `legacy-python/` 作歷史備援。
- 目前 `dotnet-src/build_release.ps1` 採 **Framework-dependent** 單檔發行（`--self-contained false`），因此 0.30 MB 執行檔需目標電腦已安裝相容的 .NET 8 Desktop Runtime。
- 若需完全免安裝，必須改用 Self-Contained 發行；該模式的體積會顯著大於目前 0.30 MB，不能同時宣稱兩者。

---

## 🏆 v6.1.0 升級亮點與指標對比

| 指標面向 | 原始版本 (Python 3.13) | C# .NET 8 原生版 (v6.1.0) | 改善幅度與效益 |
|:---|:---|:---|:---:|
| **技術語言** | Python 3.13 + CustomTkinter | **C# 12 (.NET 8.0) + WPF** | 原生 Win32 第一公民 |
| **發行體積** | 約 **155 MB** (含 `python_embed` 核心) | **0.30 MB (300 KB)** | 🚀 **體積縮減 99.8%** |
| **啟動時間** | ~ 1.5 秒 (載入 Python 虛擬機) | **< 0.1 秒 (瞬間秒開)** | ⚡ **速度提升 15 倍** |
| **快取覆蓋** | 7 項常見快取 | **16+ 項系統與常用軟體快取** | 🧹 **可多釋放 2GB~5GB 空間** |
| **大檔案透視** | 簡易清單 | **遍歷巨型肥大檔案 Top 50 (支援定位總管)** | 🔍 **秒抓塞爆磁碟元凶** |
| **系統匣常駐** | 無 | **Windows 系統匣常駐 + 右鍵極速釋放** | 📌 **背景待命、即時監控** |
| **記憶體負載** | 單色進度條 | **三段式健康/負載/警示動態色彩** | 🎨 **視覺即時感知負載** |
| **單元測試** | unittest | **xUnit (3/3 Tests 100% Clean Pass)** | 🟢 **核心安全防禦保障** |

---

## ✨ 七大重點核心功能

1. ⚡ **Win32 原生記憶體深度釋放**：
   - **即時動態監控**：內建背景計時器每 2 秒自動即時更新實體記憶體使用量與活躍處理程序數。
   - **三段式動態警示色票**：
     - `< 65%`：柔和莫蘭迪青綠（健康）
     - `65% ~ 80%`：琥珀黃（負載中）
     - `> 80%`：警示橘紅（高壓警示）
   - **雙重釋放機制**：同時呼叫 `EmptyWorkingSet`（清空無效工作集）與 `NtSetSystemInformation`（清空 Standby 待命快取清單），並即時回饋釋放容量。

2. 🧹 **16+ 項系統與常用軟體快取清理**：
   - **涵蓋類別**：Windows 系統暫存 (`Temp`)、預先讀取檔 (`Prefetch`)、錯誤傾印 (`CrashDumps`)、Windows Update 安裝快取、傳遞最佳化快取、檔案總管縮圖快取、DirectX / NVIDIA 著色器快取、系統記錄檔 (`Logs`)，以及 Google Chrome、Microsoft Edge、VS Code、Discord、Spotify 等快取。
   - **自由勾選機制**：內建 CheckBox 勾選欄位，支援「全選」與「取消全選」，自由決定欲清除類別。
   - **人性化容量轉換**：自動轉換為 `MB` / `GB` / `KB` 易讀格式。
   - **應用程式運行鎖定預警**：自動檢測 Chrome/Edge/Discord 是否執行中，若有鎖定檔案自動安全略過並友善提示。

3. 🔍 **磁碟大檔案透視 (Large File Finder)**：
   - 遍歷搜尋指定磁碟中的巨型肥大檔案排行 Top 50（預設 > 100MB）。
   - 支援「在檔案總管中定位選取檔案」，一鍵開啟所在目錄。

4. 📌 **Windows 系統匣常駐 (System Tray)**：
   - 視窗最小化時自動縮至右下角系統匣。
   - 系統匣右鍵選單支援「顯示主畫面」、「⚡ 立即釋放記憶體」與「結束程式」。

5. 🚀 **開機自啟動管理**：
   - 安全解析並列出目前登記於 `HKCU` 與 `HKLM` 登錄檔 Run 鍵之常駐開機軟體與完整指令路徑。

6. 💾 **磁碟分區容量監控**：
   - 即時透視本機所有固定硬碟分區之總容量、剩餘空間與可用百分比。

7. 🎨 **莫蘭迪現代 UI 與專屬圖示**：
   - 膠囊分段標籤導航（Segmented Pills Navigation）、去除焦點虛線框、圓角微浮雕卡片。
   - 內建 256x256 ~ 16x16 多解析度專屬圖示 `app_icon.ico`。

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
dotnet test tests/SystemOptimizer.Tests

# 一鍵發布單一獨立 Exe (Release x64)
.\build_release.ps1 -RunAfterBuild
```

---

## 📂 專案目錄結構

```text
D:\Development\GitHub\06_System-Optimizer-Tool\
├── ⚡ 啟動系統優化工具.bat                  # 🚀 根目錄一鍵秒開 (預設呼叫 0.30MB 原生版)
├── 啟動Python傳統版(備援).bat                # 📦 歷史 Python 備援啟動入口
├── README.md                                 # 專案總說明文件
├── CHANGELOG.md                              # 版本異動歷程
│
├── dotnet-src\                               # 🌟【主力發行】C# .NET 8 / WPF 原生單檔引擎
│   ├── SystemOptimizer.sln                   # Visual Studio 解決方案檔
│   ├── build_release.ps1                     # 一鍵建置發布腳本
│   ├── publish\
│   │   └── SystemOptimizer.App.exe           # 0.30 MB 原生單檔執行檔 (含專屬圖示)
│   ├── src\
│   │   ├── SystemOptimizer.Core\             # Win32 原生記憶體、快取、大檔、白名單核心
│   │   │   ├── Native\NativeMethods.cs       # P/Invoke API 定義
│   │   │   ├── Models\Models.cs              # 資料模型定義 (含 MB/GB 格式化)
│   │   │   └── Services\                     # 記憶體、快取、大檔分析與安全服務
│   │   └── SystemOptimizer.App\              # 莫蘭迪現代 WPF UI 介面
│   │       ├── Styles\MorandiTheme.xaml      # 膠囊導航與莫蘭迪樣式庫
│   │       ├── ViewModels\MainViewModel.cs   # 即時監控、大檔搜尋與命令調度層
│   │       ├── MainWindow.xaml.cs            # 系統匣 NotifyIcon 常駐支援
│   │       └── app_icon.ico                  # 多解析度專屬圖示 (256x256 ~ 16x16)
│   └── tests\
│       └── SystemOptimizer.Tests\            # xUnit 自動化單元測試套件
│
└── legacy-python\                            # 📦【歷史備援】原始 Python 3.13 引擎
    ├── main.py                               # 原始 CustomTkinter 入口
    ├── engine\                               # 原始 Python 邏輯模組
    ├── ui\
    ├── requirements.txt
    └── setup_and_run.ps1
```

詳細版本異動請參閱 [CHANGELOG.md](CHANGELOG.md)。
