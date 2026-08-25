using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using SystemOptimizer.Core.Models;

namespace SystemOptimizer.Core.Services;

public class StorageAnalyzer
{
    public List<DriveStorageInfo> GetDrives()
    {
        var list = new List<DriveStorageInfo>();
        foreach (var drive in DriveInfo.GetDrives())
        {
            try
            {
                if (drive.IsReady && drive.DriveType == DriveType.Fixed)
                {
                    var freePct = (double)drive.TotalFreeSpace / drive.TotalSize * 100.0;
                    list.Add(new DriveStorageInfo(
                        drive.Name,
                        string.IsNullOrWhiteSpace(drive.VolumeLabel) ? "本機磁碟" : drive.VolumeLabel,
                        drive.TotalSize,
                        drive.TotalFreeSpace,
                        freePct
                    ));
                }
            }
            catch { }
        }
        return list;
    }

    public async Task<List<LargeFileInfo>> ScanLargeFilesAsync(
        string rootPath,
        long minSizeBytes = 104857600, // 預設 > 100MB
        int topCount = 50,
        IProgress<string>? progress = null,
        CancellationToken ct = default)
    {
        return await Task.Run(() =>
        {
            var result = new List<LargeFileInfo>();
            if (string.IsNullOrWhiteSpace(rootPath) || !Directory.Exists(rootPath))
                return result;

            var queue = new Queue<string>();
            queue.Enqueue(rootPath);

            int scannedDirs = 0;

            while (queue.Count > 0 && !ct.IsCancellationRequested)
            {
                var current = queue.Dequeue();
                scannedDirs++;
                if (scannedDirs % 20 == 0)
                {
                    progress?.Report($"正在掃描目錄：{current}");
                }

                try
                {
                    var dir = new DirectoryInfo(current);
                    if ((dir.Attributes & FileAttributes.ReparsePoint) != 0)
                        continue;

                    foreach (var file in dir.EnumerateFiles())
                    {
                        if (ct.IsCancellationRequested) break;
                        try
                        {
                            if (file.Length >= minSizeBytes)
                            {
                                result.Add(new LargeFileInfo(
                                    file.Name,
                                    file.Extension.ToUpperInvariant(),
                                    file.Length,
                                    file.FullName,
                                    file.DirectoryName ?? "",
                                    file.LastWriteTime
                                ));
                            }
                        }
                        catch { }
                    }

                    foreach (var subDir in dir.EnumerateDirectories())
                    {
                        if (ct.IsCancellationRequested) break;
                        try
                        {
                            if ((subDir.Attributes & FileAttributes.ReparsePoint) == 0 &&
                                (subDir.Attributes & FileAttributes.Hidden) == 0 &&
                                !subDir.Name.StartsWith("$", StringComparison.OrdinalIgnoreCase) &&
                                !subDir.Name.Equals("System Volume Information", StringComparison.OrdinalIgnoreCase) &&
                                !subDir.Name.Equals("Windows", StringComparison.OrdinalIgnoreCase))
                            {
                                queue.Enqueue(subDir.FullName);
                            }
                        }
                        catch { }
                    }
                }
                catch { }
            }

            result.Sort((a, b) => b.FileSizeBytes.CompareTo(a.FileSizeBytes));
            return result.Take(topCount).ToList();
        }, ct);
    }
}
