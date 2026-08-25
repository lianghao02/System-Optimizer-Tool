using System;

namespace SystemOptimizer.Core.Models;

public record SystemMetrics(
    ulong TotalPhysicalBytes,
    ulong AvailablePhysicalBytes,
    uint MemoryLoadPercentage,
    int ProcessCount
);

public class CacheItem
{
    public string Category { get; set; }
    public string Path { get; set; }
    public long FileSizeBytes { get; set; }
    public int FileCount { get; set; }
    public bool IsSelected { get; set; } = true;
    public string StatusNote { get; set; } = "";

    public string FormattedSize => FormatBytes(FileSizeBytes);

    public CacheItem(string category, string path, long fileSizeBytes, int fileCount, string statusNote = "")
    {
        Category = category;
        Path = path;
        FileSizeBytes = fileSizeBytes;
        FileCount = fileCount;
        StatusNote = statusNote;
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
    string Message
);
