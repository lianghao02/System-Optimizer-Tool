using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
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

    private string _statusMessage = "系統就緒 (原生 .NET 8 高效能版)";
    private string _memoryUsageText = "載入中...";
    private uint _memoryLoadPercentage;
    private string _availableMemoryText = "";
    private string _lastFreedMemoryText = "";
    private Brush _memoryLoadBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#5E9B79"));
    private int _processCount;
    private bool _isBusy;

    // 大檔案透視
    private string _selectedDrivePath = "C:\\";
    private int _minFileSizeMb = 100;
    private LargeFileInfo? _selectedLargeFile;

    public event PropertyChangedEventHandler? PropertyChanged;

    public ObservableCollection<CacheItem> CacheItems { get; } = new();
    public ObservableCollection<StartupItem> StartupItems { get; } = new();
    public ObservableCollection<DriveStorageInfo> DriveInfos { get; } = new();
    public ObservableCollection<LargeFileInfo> LargeFiles { get; } = new();

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

            await Task.Run(() =>
            {
                _memoryOptimizer.OptimizeWorkingSets();
                _memoryOptimizer.PurgeStandbyList();
            });

            await Task.Delay(300);
            var afterAvail = _memoryOptimizer.GetMetrics().AvailablePhysicalBytes;
            RefreshMemory();

            var freedMb = afterAvail > beforeAvail ? (afterAvail - beforeAvail) / (1024.0 * 1024.0) : 0;
            LastFreedMemoryText = freedMb > 0 ? $"✨ 上次釋放：{freedMb:F1} MB 記憶體空間" : "✨ 已清空所有無效工作集與 Standby 快取";
            StatusMessage = $"記憶體深度清理成功！{LastFreedMemoryText}";
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
        IsBusy = true;
        StatusMessage = "正在掃描系統與 16+ 項常見快取殘留...";
        CacheItems.Clear();

        try
        {
            var progress = new Progress<string>(msg => StatusMessage = msg);
            var results = await _cacheCleaner.ScanTargetsAsync(progress);

            foreach (var item in results)
            {
                CacheItems.Add(item);
            }

            OnPropertyChanged(nameof(TotalSelectedCacheSizeFormatted));
            StatusMessage = $"掃描完成！發現 {CacheItems.Count} 個快取類別，共計 {TotalSelectedCacheSizeFormatted}";
        }
        catch (Exception ex)
        {
            StatusMessage = $"掃描出錯：{ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    public async Task CleanCacheAsync()
    {
        var selectedItems = CacheItems.Where(i => i.IsSelected).ToList();
        if (IsBusy || selectedItems.Count == 0) return;
        IsBusy = true;
        StatusMessage = "正在安全清理已勾選之快取...";

        try
        {
            var progress = new Progress<string>(msg => StatusMessage = msg);
            var result = await _cacheCleaner.CleanTargetsAsync(selectedItems, progress);

            // 清理後重新掃描
            await ScanCacheAsync();
            StatusMessage = result.Message;
        }
        catch (Exception ex)
        {
            StatusMessage = $"清理出錯：{ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
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
        IsBusy = true;
        StatusMessage = $"正在掃描磁碟 {SelectedDrivePath} 中大於 {MinFileSizeMb} MB 的檔案...";
        LargeFiles.Clear();

        try
        {
            var progress = new Progress<string>(msg => StatusMessage = msg);
            var minBytes = (long)MinFileSizeMb * 1024 * 1024;
            var results = await _storageAnalyzer.ScanLargeFilesAsync(SelectedDrivePath, minBytes, 50, progress);

            foreach (var f in results)
            {
                LargeFiles.Add(f);
            }

            StatusMessage = $"大檔案掃描完成！共找出 {LargeFiles.Count} 個肥大檔案排行";
        }
        catch (Exception ex)
        {
            StatusMessage = $"大檔掃描失敗：{ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

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
