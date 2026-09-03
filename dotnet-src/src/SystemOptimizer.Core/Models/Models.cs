using System;

namespace SystemOptimizer.Core.Models;

public record SystemMetrics(
    ulong TotalPhysicalBytes,
    ulong AvailablePhysicalBytes,
    uint MemoryLoadPercentage,
    int ProcessCount
);

public enum CacheRiskLevel
{
    Safe,       // 一般安全清理 (低副作用，適合日常與預設選取)
    Advanced   // 進階快取清理 (具效能與重建代價，預設不選取並揭露副作用)
}

public class CacheItem
{
    public string Category { get; set; }
    public string Path { get; set; }
    public long FileSizeBytes { get; set; }
    public int FileCount { get; set; }
    public bool IsSelected { get; set; } = true;
    public string StatusNote { get; set; } = "";
    public CacheRiskLevel RiskLevel { get; set; } = CacheRiskLevel.Safe;
    public string SideEffectNotice { get; set; } = "";

    public string RiskLevelBadge => RiskLevel switch
    {
        CacheRiskLevel.Safe => "一般安全",
        CacheRiskLevel.Advanced => "⚠️ 進階快取",
        _ => "一般"
    };

    public string FormattedSize => FormatBytes(FileSizeBytes);

    public CacheItem(
        string category, 
        string path, 
        long fileSizeBytes, 
        int fileCount, 
        string statusNote = "",
        CacheRiskLevel riskLevel = CacheRiskLevel.Safe,
        string sideEffectNotice = "")
    {
        Category = category;
        Path = path;
        FileSizeBytes = fileSizeBytes;
        FileCount = fileCount;
        StatusNote = statusNote;
        RiskLevel = riskLevel;
        SideEffectNotice = sideEffectNotice;
        IsSelected = (riskLevel == CacheRiskLevel.Safe);
    }

    public static string FormatBytes(long bytes)
    {
        if (bytes <= 0) return "0 B";
        string[] suffixes = { "B", "KB", "MB", "GB", "TB" };
        int i = 0;
        double d = bytes;
        while (d >= 1024 && i < suffixes.Length - 1)
        {
            d /= 1024;
            i++;
        }
        return $"{d:0.##} {suffixes[i]}";
    }
}

public class LargeFileInfo
{
    public string FileName { get; set; }
    public string Extension { get; set; }
    public long FileSizeBytes { get; set; }
    public string FormattedSize => CacheItem.FormatBytes(FileSizeBytes);
    public string FilePath { get; set; }
    public string DirectoryPath { get; set; }
    public DateTime LastModified { get; set; }

    public LargeFileInfo(string fileName, string extension, long fileSizeBytes, string filePath, string directoryPath, DateTime lastModified)
    {
        FileName = fileName;
        Extension = extension;
        FileSizeBytes = fileSizeBytes;
        FilePath = filePath;
        DirectoryPath = directoryPath;
        LastModified = lastModified;
    }
}

public record StartupItem(
    string Name,
    string Command,
    string Location,
    bool IsEnabled
);

public record DriveStorageInfo(
    string DriveLetter,
    string VolumeLabel,
    long TotalBytes,
    long FreeBytes,
    double FreePercentage
)
{
    public string FormattedTotal => CacheItem.FormatBytes(TotalBytes);
    public string FormattedFree => CacheItem.FormatBytes(FreeBytes);
    public string FormattedUsed => CacheItem.FormatBytes(TotalBytes - FreeBytes);
}

public record OptimizationResult(
    long BytesFreed,
    int FilesDeleted,
    long MemoryFreedBytes,
    TimeSpan Duration,
    string Message,
    int SkippedFiles = 0,
    int ErrorCount = 0,
    bool WasCanceled = false,
    string? ErrorSummary = null
);

public record OperationProgress(int Percentage, string Message);

public record CacheScanResult(
    IReadOnlyList<CacheItem> Items,
    int SkippedFiles,
    int ErrorCount,
    bool WasCanceled,
    string? ErrorSummary = null
);

public record StorageScanProgress(
    int ScannedDirectoryCount,
    int CandidateFileCount,
    string CurrentDirectory
);

public record StorageScanResult(
    IReadOnlyList<LargeFileInfo> Items,
    int ScannedDirectoryCount,
    int CandidateFileCount,
    int SkippedDirectoryCount,
    bool WasCanceled
);

public record TimeRangeOption(string DisplayName, int Days);
public record SizeFilterOption(string DisplayName, int Megabytes);

public record LatestReleaseInfo(string Version, string ReleaseUrl, string? DownloadUrl, string ReleaseNotes);
