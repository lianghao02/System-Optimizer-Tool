using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Windows.Threading;
using Brush = System.Windows.Media.Brush;
using Color = System.Windows.Media.Color;
using ColorConverter = System.Windows.Media.ColorConverter;
using SolidColorBrush = System.Windows.Media.SolidColorBrush;
using SystemOptimizer.Core.Models;
using SystemOptimizer.Core.Services;

namespace SystemOptimizer.App.ViewModels;

public class MainViewModel : INotifyPropertyChanged
{
    private readonly MemoryOptimizer _memoryOptimizer = new();
    private readonly CacheCleaner _cacheCleaner = new();
    private readonly StartupManager _startupManager = new();
    private readonly StorageAnalyzer _storageAnalyzer = new();
    private readonly DispatcherTimer _monitorTimer;
    private readonly List<LargeFileInfo> _allLargeFiles = new();

    private string _statusMessage = "系統就緒 (原生 .NET 8 高效能版)";
    private string _memoryUsageText = "載入中...";
    private uint _memoryLoadPercentage;
    private string _availableMemoryText = "";
    private string _lastFreedMemoryText = "";
    private Brush _memoryLoadBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#5E9B79"));
    private int _processCount;
    private bool _isBusy;
    private CancellationTokenSource? _operationCancellation;
    private int _operationProgressPercentage;
    private string _operationProgressText = "";

    // 大檔案透視
    private string _selectedDrivePath = "C:\\";
    private int _minFileSizeMb = 100;
    private LargeFileInfo? _selectedLargeFile;
    private string _largeFileTypeFilter = "全部類型";
    private int _largeFileModifiedWithinDays;
    private int _largeFileFilterMinimumSizeMb;

    public event PropertyChangedEventHandler? PropertyChanged;

    public ObservableCollection<CacheItem> CacheItems { get; } = new();
    public ObservableCollection<StartupItem> StartupItems { get; } = new();
    public ObservableCollection<DriveStorageInfo> DriveInfos { get; } = new();
    public ObservableCollection<LargeFileInfo> LargeFiles { get; } = new();
    public ObservableCollection<string> LargeFileTypeFilters { get; } = new()
    {
        "全部類型", "影片", "壓縮檔", "映像檔", "安裝檔", "文件", "其他"
    };
    public ObservableCollection<TimeRangeOption> LargeFileTimeFilters { get; } = new()
    {
        new("不限時間", 0), new("7 天內", 7), new("30 天內", 30), new("一年內", 365)
    };
    public ObservableCollection<SizeFilterOption> LargeFileSizeFilters { get; } = new()
    {
        new("不限大小", 0), new("至少 100 MB", 100), new("至少 500 MB", 500), new("至少 1 GB", 1024)
    };

    public string StatusMessage
    {
        get => _statusMessage;
        set => SetField(ref _statusMessage, value);
    }

    public string MemoryUsageText
    {
        get => _memoryUsageText;
        set => SetField(ref _memoryUsageText, value);
    }

    public uint MemoryLoadPercentage
    {
        get => _memoryLoadPercentage;
        set
        {
            if (SetField(ref _memoryLoadPercentage, value))
            {
                UpdateMemoryLoadBrush(value);
            }
        }
    }

    public Brush MemoryLoadBrush
    {
        get => _memoryLoadBrush;
        set => SetField(ref _memoryLoadBrush, value);
    }

    public string AvailableMemoryText
    {
        get => _availableMemoryText;
        set => SetField(ref _availableMemoryText, value);
    }

    public string LastFreedMemoryText
    {
        get => _lastFreedMemoryText;
        set => SetField(ref _lastFreedMemoryText, value);
    }

    public int ProcessCount
    {
        get => _processCount;
        set => SetField(ref _processCount, value);
    }

    public bool IsBusy
    {
        get => _isBusy;
        set => SetField(ref _isBusy, value);
    }

    public int OperationProgressPercentage
    {
        get => _operationProgressPercentage;
        set => SetField(ref _operationProgressPercentage, value);
    }

    public string OperationProgressText
    {
        get => _operationProgressText;
        set => SetField(ref _operationProgressText, value);
    }

    public bool CanCancelOperation => IsBusy && _operationCancellation != null;

    public string SelectedDrivePath
    {
        get => _selectedDrivePath;
        set => SetField(ref _selectedDrivePath, value);
    }

    public int MinFileSizeMb
    {
        get => _minFileSizeMb;
        set => SetField(ref _minFileSizeMb, value);
    }

    public LargeFileInfo? SelectedLargeFile
    {
        get => _selectedLargeFile;
        set => SetField(ref _selectedLargeFile, value);
    }

    public string TotalSelectedCacheSizeFormatted
    {
        get
        {
            var total = CacheItems.Where(i => i.IsSelected).Sum(i => i.FileSizeBytes);
            return CacheItem.FormatBytes(total);
        }
    }

    public ICommand RefreshMemoryCommand { get; }
    public ICommand OptimizeMemoryCommand { get; }
    public ICommand ScanCacheCommand { get; }
    public ICommand CleanCacheCommand { get; }
    public ICommand SelectAllCacheCommand { get; }
    public ICommand UnselectAllCacheCommand { get; }
    public ICommand LoadStartupCommand { get; }
    public ICommand LoadDrivesCommand { get; }
    public ICommand ScanLargeFilesCommand { get; }
    public ICommand OpenInExplorerCommand { get; }
    public ICommand CancelOperationCommand { get; }

    public MainViewModel()
    {
        RefreshMemoryCommand = new RelayCommand(RefreshMemory);
        OptimizeMemoryCommand = new RelayCommand(async () => await OptimizeMemoryAsync());
        ScanCacheCommand = new RelayCommand(async () => await ScanCacheAsync());
        CleanCacheCommand = new RelayCommand(async () => await CleanCacheAsync());
        SelectAllCacheCommand = new RelayCommand(SelectAllCache);
        UnselectAllCacheCommand = new RelayCommand(UnselectAllCache);
        LoadStartupCommand = new RelayCommand(LoadStartupItems);
        LoadDrivesCommand = new RelayCommand(LoadDriveInfos);
        ScanLargeFilesCommand = new RelayCommand(async () => await ScanLargeFilesAsync());
        OpenInExplorerCommand = new RelayCommand(OpenSelectedInExplorer);
        CancelOperationCommand = new RelayCommand(CancelOperation, () => CanCancelOperation);

        RefreshMemory();
        LoadDriveInfos();
        LoadStartupItems();

        if (DriveInfos.Count > 0)
        {
            SelectedDrivePath = DriveInfos[0].DriveLetter;
        }

        // 啟動實時記憶體即時監控計時器 (每 2 秒自動更新)
        _monitorTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(2)
        };
        _monitorTimer.Tick += (s, e) =>
        {
            if (!_isBusy)
            {
                RefreshMemory();
            }
        };
        _monitorTimer.Start();
    }

    private void UpdateMemoryLoadBrush(uint loadPercentage)
    {
        if (loadPercentage < 65)
        {
            MemoryLoadBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#5E9B79")); // 綠色/莫蘭迪青
        }
        else if (loadPercentage <= 80)
        {
            MemoryLoadBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#D4A373")); // 琥珀黃
        }
        else
        {
            MemoryLoadBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#D05353")); // 警示橘紅
        }
    }

    public void RefreshMemory()
    {
        var metrics = _memoryOptimizer.GetMetrics();
        MemoryLoadPercentage = metrics.MemoryLoadPercentage;
        ProcessCount = metrics.ProcessCount;
        var totalGb = metrics.TotalPhysicalBytes / (1024.0 * 1024.0 * 1024.0);
        var availGb = metrics.AvailablePhysicalBytes / (1024.0 * 1024.0 * 1024.0);
        var usedGb = totalGb - availGb;

        MemoryUsageText = $"{usedGb:F1} GB / {totalGb:F1} GB ({metrics.MemoryLoadPercentage}%)";
        AvailableMemoryText = $"{availGb:F2} GB 可用 ｜ {metrics.ProcessCount} 個活躍處理程序";
    }

    public async Task OptimizeMemoryAsync()
    {
        if (IsBusy) return;
        IsBusy = true;
        StatusMessage = "正在執行 Win32 原生記憶體深度釋放 (WorkingSet + Standby List)...";

        try
        {
            var beforeAvail = _memoryOptimizer.GetMetrics().AvailablePhysicalBytes;

            var memoryOperation = await Task.Run(() =>
            {
                _memoryOptimizer.OptimizeWorkingSets();
                var standbyListPurged = _memoryOptimizer.PurgeStandbyList();
                return (standbyListPurged, _memoryOptimizer.LastWorkingSetSkippedProcessCount, _memoryOptimizer.LastStandbyPurgeError);
            });

            await Task.Delay(300);
            var afterAvail = _memoryOptimizer.GetMetrics().AvailablePhysicalBytes;
            RefreshMemory();

            var freedMb = afterAvail > beforeAvail ? (afterAvail - beforeAvail) / (1024.0 * 1024.0) : 0;
            LastFreedMemoryText = freedMb > 0
                ? $"本次可用記憶體增加：{freedMb:F1} MB"
                : "本次可用記憶體未增加；Windows 會依需要自行回收。";
            var skippedProcessText = memoryOperation.LastWorkingSetSkippedProcessCount > 0
                ? $" 已安全略過 {memoryOperation.LastWorkingSetSkippedProcessCount} 個無法存取的系統處理程序。"
                : "";
            StatusMessage = memoryOperation.standbyListPurged
                ? $"記憶體整理完成。{LastFreedMemoryText}{skippedProcessText}"
                : $"已完成工作集整理，但無法清除 Standby 快取：{memoryOperation.LastStandbyPurgeError ?? "Windows 未回傳詳細原因"}。{LastFreedMemoryText}{skippedProcessText}";
        }
        catch (Exception ex)
        {
            StatusMessage = $"優化失敗：{ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    public async Task ScanCacheAsync()
    {
        if (IsBusy) return;
        var cancellation = BeginOperation();
        StatusMessage = "正在掃描系統與 16+ 項常見快取殘留...";
        CacheItems.Clear();

        try
        {
            var progress = CreateProgress();
            var scanResult = await _cacheCleaner.ScanTargetsAsync(progress, cancellation.Token);

            foreach (var item in scanResult.Items)
            {
                CacheItems.Add(item);
            }

            OnPropertyChanged(nameof(TotalSelectedCacheSizeFormatted));
            StatusMessage = scanResult.WasCanceled
                ? "已取消快取掃描。"
                : $"掃描完成！發現 {CacheItems.Count} 個快取類別，共計 {TotalSelectedCacheSizeFormatted}{FormatOperationIssues(scanResult.SkippedFiles, scanResult.ErrorCount, scanResult.ErrorSummary)}";
        }
        catch (Exception ex)
        {
            StatusMessage = $"掃描出錯：{ex.Message}";
        }
        finally
        {
            EndOperation(cancellation);
        }
    }

    public async Task CleanCacheAsync()
    {
        var selectedItems = CacheItems.Where(i => i.IsSelected).ToList();
        if (IsBusy || selectedItems.Count == 0) return;
        var preview = CreateCleanPreview(selectedItems);
        var confirmation = System.Windows.MessageBox.Show(
            $"即將安全清理 {selectedItems.Count} 個快取類別，約 {CacheItem.FormatBytes(preview.Bytes)}、{preview.FileCount:N0} 個檔案。\n\n目標：\n{preview.TargetSummary}\n\n系統或正在使用的檔案將安全略過。是否繼續？",
            "確認安全清理",
            System.Windows.MessageBoxButton.OKCancel,
            System.Windows.MessageBoxImage.Warning);
        if (confirmation != System.Windows.MessageBoxResult.OK) return;

        var cancellation = BeginOperation();
        StatusMessage = "正在安全清理已勾選之快取...";
        OptimizationResult? result = null;

        try
        {
            var progress = CreateProgress();
            result = await _cacheCleaner.CleanTargetsAsync(selectedItems, progress, cancellation.Token);
        }
        catch (Exception ex)
        {
            StatusMessage = $"清理出錯：{ex.Message}";
        }
        finally
        {
            EndOperation(cancellation);
        }

        if (result != null)
        {
            await ScanCacheAsync();
            StatusMessage = $"{result.Message}{FormatOperationIssues(result.SkippedFiles, result.ErrorCount, result.ErrorSummary)}";
        }
    }

    public string LargeFileTypeFilter
    {
        get => _largeFileTypeFilter;
        set
        {
            if (SetField(ref _largeFileTypeFilter, value))
                ApplyLargeFileFilters();
        }
    }

    public int LargeFileModifiedWithinDays
    {
        get => _largeFileModifiedWithinDays;
        set
        {
            if (SetField(ref _largeFileModifiedWithinDays, value))
                ApplyLargeFileFilters();
        }
    }

    public int LargeFileFilterMinimumSizeMb
    {
        get => _largeFileFilterMinimumSizeMb;
        set
        {
            if (SetField(ref _largeFileFilterMinimumSizeMb, Math.Max(0, value)))
                ApplyLargeFileFilters();
        }
    }

    public void CancelOperation()
    {
        _operationCancellation?.Cancel();
        StatusMessage = "正在取消目前工作，請稍候...";
    }

    private CancellationTokenSource BeginOperation()
    {
        var cancellation = new CancellationTokenSource();
        _operationCancellation = cancellation;
        IsBusy = true;
        OperationProgressPercentage = 0;
        OperationProgressText = "準備中...";
        OnPropertyChanged(nameof(CanCancelOperation));
        CommandManager.InvalidateRequerySuggested();
        return cancellation;
    }

    private void EndOperation(CancellationTokenSource cancellation)
    {
        if (ReferenceEquals(_operationCancellation, cancellation))
            _operationCancellation = null;
        cancellation.Dispose();
        IsBusy = false;
        OperationProgressPercentage = 0;
        OperationProgressText = "";
        OnPropertyChanged(nameof(CanCancelOperation));
        CommandManager.InvalidateRequerySuggested();
    }

    private IProgress<OperationProgress> CreateProgress() => new Progress<OperationProgress>(progress =>
    {
        OperationProgressPercentage = progress.Percentage;
        OperationProgressText = progress.Message;
        StatusMessage = progress.Message;
    });

    private static string FormatOperationIssues(int skippedFiles, int errorCount, string? errorSummary)
    {
        if (skippedFiles == 0 && errorCount == 0) return "";
        var summary = $"（略過 {skippedFiles} 項，記錄 {errorCount} 個例外）";
        return string.IsNullOrWhiteSpace(errorSummary) ? summary : $"{summary} {errorSummary}";
    }

    private static (long Bytes, int FileCount, string TargetSummary) CreateCleanPreview(IReadOnlyList<CacheItem> items)
    {
        var targetNames = items.Take(5).Select(item => $"• {item.Category}");
        var summary = string.Join("\n", targetNames);
        if (items.Count > 5) summary += $"\n• 及其他 {items.Count - 5} 項";
        return (items.Sum(item => item.FileSizeBytes), items.Sum(item => item.FileCount), summary);
    }

    public void SelectAllCache()
    {
        foreach (var item in CacheItems) item.IsSelected = true;
        OnPropertyChanged(nameof(TotalSelectedCacheSizeFormatted));
    }

    public void UnselectAllCache()
    {
        foreach (var item in CacheItems) item.IsSelected = false;
        OnPropertyChanged(nameof(TotalSelectedCacheSizeFormatted));
    }

    public async Task ScanLargeFilesAsync()
    {
        if (IsBusy) return;
        var cancellation = BeginOperation();
        StatusMessage = $"正在掃描磁碟 {SelectedDrivePath} 中大於 {MinFileSizeMb} MB 的檔案...";
        LargeFiles.Clear();
        _allLargeFiles.Clear();

        try
        {
            var progress = new Progress<StorageScanProgress>(report =>
            {
                OperationProgressText = $"已掃描 {report.ScannedDirectoryCount:N0} 個資料夾｜找到 {report.CandidateFileCount:N0} 個候選檔案";
                StatusMessage = $"正在掃描：{report.CurrentDirectory}";
            });
            var minBytes = (long)MinFileSizeMb * 1024 * 1024;
            var scanResult = await _storageAnalyzer.ScanLargeFilesAsync(SelectedDrivePath, minBytes, 50, progress, cancellation.Token);

            _allLargeFiles.AddRange(scanResult.Items);
            ApplyLargeFileFilters();

            StatusMessage = scanResult.WasCanceled
                ? $"已取消大檔案掃描（已掃描 {scanResult.ScannedDirectoryCount:N0} 個資料夾）。"
                : $"大檔案掃描完成！已掃描 {scanResult.ScannedDirectoryCount:N0} 個資料夾，在 {scanResult.CandidateFileCount:N0} 個候選檔案中保留 Top {scanResult.Items.Count}。";
        }
        catch (Exception ex)
        {
            StatusMessage = $"大檔掃描失敗：{ex.Message}";
        }
        finally
        {
            EndOperation(cancellation);
        }
    }

    private void ApplyLargeFileFilters()
    {
        IEnumerable<LargeFileInfo> filtered = _allLargeFiles;

        if (LargeFileTypeFilter != "全部類型")
            filtered = filtered.Where(file => MatchesLargeFileType(file.Extension, LargeFileTypeFilter));

        if (LargeFileModifiedWithinDays > 0)
        {
            var cutoff = DateTime.Now.AddDays(-LargeFileModifiedWithinDays);
            filtered = filtered.Where(file => file.LastModified >= cutoff);
        }

        if (LargeFileFilterMinimumSizeMb > 0)
        {
            var minimumBytes = (long)LargeFileFilterMinimumSizeMb * 1024 * 1024;
            filtered = filtered.Where(file => file.FileSizeBytes >= minimumBytes);
        }

        var filteredFiles = filtered.OrderByDescending(file => file.FileSizeBytes).ToList();
        LargeFiles.Clear();
        foreach (var file in filteredFiles)
            LargeFiles.Add(file);

        if (SelectedLargeFile != null && !filteredFiles.Contains(SelectedLargeFile))
            SelectedLargeFile = null;
    }

    private static bool MatchesLargeFileType(string extension, string filter) => filter switch
    {
        "影片" => extension is ".MP4" or ".MKV" or ".AVI" or ".MOV" or ".WMV" or ".M4V",
        "壓縮檔" => extension is ".ZIP" or ".RAR" or ".7Z" or ".TAR" or ".GZ",
        "映像檔" => extension is ".ISO" or ".IMG" or ".VHD" or ".VHDX",
        "安裝檔" => extension is ".EXE" or ".MSI" or ".MSIX" or ".APPX",
        "文件" => extension is ".PDF" or ".DOCX" or ".XLSX" or ".PPTX" or ".PST" or ".OST",
        "其他" => !MatchesLargeFileType(extension, "影片") && !MatchesLargeFileType(extension, "壓縮檔") &&
                   !MatchesLargeFileType(extension, "映像檔") && !MatchesLargeFileType(extension, "安裝檔") &&
                   !MatchesLargeFileType(extension, "文件"),
        _ => true,
    };

    public void OpenSelectedInExplorer()
    {
        if (SelectedLargeFile == null || string.IsNullOrWhiteSpace(SelectedLargeFile.FilePath))
            return;

        try
        {
            if (File.Exists(SelectedLargeFile.FilePath))
            {
                Process.Start("explorer.exe", $"/select,\"{SelectedLargeFile.FilePath}\"");
                StatusMessage = $"已在檔案總管中定位：{SelectedLargeFile.FileName}";
            }
            else if (Directory.Exists(SelectedLargeFile.DirectoryPath))
            {
                Process.Start("explorer.exe", $"\"{SelectedLargeFile.DirectoryPath}\"");
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"開啟失敗：{ex.Message}";
        }
    }

    public void LoadStartupItems()
    {
        StartupItems.Clear();
        var items = _startupManager.GetStartupItems();
        foreach (var item in items)
        {
            StartupItems.Add(item);
        }
    }

    public void LoadDriveInfos()
    {
        DriveInfos.Clear();
        var drives = _storageAnalyzer.GetDrives();
        foreach (var d in drives)
        {
            DriveInfos.Add(d);
        }
    }

    protected bool SetField<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (System.Collections.Generic.EqualityComparer<T>.Default.Equals(field, value)) return false;
        field = value;
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        return true;
    }

    protected void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
