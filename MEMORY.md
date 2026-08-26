# 專案記憶庫 (MEMORY)

## 1. 重大架構演進決策

### 決策 1：從 Python 3.13 全面重構遷移為 C# .NET 8 WPF
- **日期**：2026-08-24
- **背景**：原 Python 版需攜帶 150MB 的 `python_embed` 內嵌虛擬機，啟動需 1.5 秒，且調用 Win32 底層 API 時受限於 Python GIL 與 ctypes 封裝。
- **決策**：改採 C# 12 / .NET 8 WPF 重寫，發布為單一獨立執行檔。
- **效益**：體積驟降至 **0.30 MB** (99.8% 減重)，啟動時間提升至 **< 0.1 秒秒開**，記憶體釋放效率與系統相容性大幅提升。

### 決策 2：單一 Repository 雙引擎整併模式
- **日期**：2026-08-24
- **決策**：不建立第二個 GitHub Repo，將 C# .NET 原始碼置於 `dotnet-src/` 作為主力發布引擎，原始 Python 原始碼封存於 `legacy-python/` 作為歷史對照與備援。
- **清理成果**：刪除 `legacy-python/python_embed/` 與中間 `bin/obj` 檔案共 2,479 個雜訊檔，專案庫由 56.2MB 瘦身至 **0.63 MB**。

---

## 2. 重要技術坑洞與踩坑解法 (Bug & Gotchas)

### 坑洞 1：WPF XAML 圖示解析與 `Resource` 宣告
- **現象**：單檔發布後點擊 `SystemOptimizer.App.exe` 閃退，捕捉到 `XamlParseException: 找不到資源 'app_icon.ico'`。
- **原因**：在 XAML 中指定 `Icon="app_icon.ico"` 時，除了在 csproj 宣告 `<ApplicationIcon>` 外，必須同時在 csproj 加入 `<Resource Include="app_icon.ico" />`，WPF 的 BAML 解析器才能以 Pack URI 正確載入圖示。

### 坑洞 2：.NET SDK 本機環境路徑
- **現象**：在命令列執行 `dotnet` 時可能呼叫到 `C:\Program Files\dotnet`（無 SDK 的空 host）。
- **解法**：在建置腳本中明確設定：
  - `DOTNET_ROOT = C:\Users\chia-hao\AppData\Local\Microsoft\dotnet`
  - `PATH` 優先置入 `%LOCALAPPDATA%\Microsoft\dotnet`。

### 坑洞 3：`<UseWindowsForms>true</UseWindowsForms>` 導致命名空間衝突
- **現象**：啟用 Windows Forms 以使用 `NotifyIcon` 系統匣時，`Application`、`Brush`、`Color`、`ColorConverter` 出現型別二義性。
- **解法**：在 `App.xaml.cs` 中顯式繼承 `System.Windows.Application`；在 `MainViewModel.cs` 中以 alias `using Brush = System.Windows.Media.Brush;` 明確消歧義。
