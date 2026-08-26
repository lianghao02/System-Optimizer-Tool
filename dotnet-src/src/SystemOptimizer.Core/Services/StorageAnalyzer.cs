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
    private static readonly EnumerationOptions SafeEnumerationOptions = new()
    {
        IgnoreInaccessible = true,
        RecurseSubdirectories = false,
        ReturnSpecialDirectories = false,
        AttributesToSkip = FileAttributes.ReparsePoint,
    };

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
                    list.Add(new DriveStorageInfo(drive.Name,
                        string.IsNullOrWhiteSpace(drive.VolumeLabel) ? "本機磁碟" : drive.VolumeLabel,
                        drive.TotalSize, drive.TotalFreeSpace, freePct));
                }
            }
            catch
            {
                // 卸除中的磁碟可能無法讀取，安全略過。
            }
        }
        return list;
    }

    public async Task<StorageScanResult> ScanLargeFilesAsync(
        string rootPath,
        long minSizeBytes = 104857600,
        int topCount = 50,
        IProgress<StorageScanProgress>? progress = null,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(rootPath) || !Directory.Exists(rootPath) || topCount <= 0)
            return new StorageScanResult(Array.Empty<LargeFileInfo>(), 0, 0, 0, ct.IsCancellationRequested);

        return await Task.Run(() =>
        {
            var topFiles = new PriorityQueue<LargeFileInfo, long>();
            var queue = new Queue<string>();
            queue.Enqueue(rootPath);
            var scannedDirectories = 0;
            var candidateFiles = 0;
            var skippedDirectories = 0;

            while (queue.Count > 0 && !ct.IsCancellationRequested)
            {
                var current = queue.Dequeue();
                scannedDirectories++;
                if (scannedDirectories % 20 == 0)
                    progress?.Report(new StorageScanProgress(scannedDirectories, candidateFiles, current));

                try
                {
                    var directory = new DirectoryInfo(current);
                    if ((directory.Attributes & FileAttributes.ReparsePoint) != 0)
                    {
                        skippedDirectories++;
                        continue;
                    }

                    foreach (var file in directory.EnumerateFiles("*", SafeEnumerationOptions))
                    {
                        if (ct.IsCancellationRequested) break;
                        try
                        {
                            if (file.Length < minSizeBytes) continue;
                            candidateFiles++;
                            AddTopFile(topFiles, new LargeFileInfo(file.Name, file.Extension.ToUpperInvariant(), file.Length,
                                file.FullName, file.DirectoryName ?? "", file.LastWriteTime), topCount);
                        }
                        catch
                        {
                            // 檔案可能剛被移除或遭鎖定，安全略過。
                        }
                    }

                    foreach (var subDirectory in directory.EnumerateDirectories("*", SafeEnumerationOptions))
                    {
                        if (ct.IsCancellationRequested) break;
                        try
                        {
                            if (ShouldScanDirectory(subDirectory))
                                queue.Enqueue(subDirectory.FullName);
                            else
                                skippedDirectories++;
                        }
                        catch
                        {
                            skippedDirectories++;
                        }
                    }
                }
                catch
                {
                    skippedDirectories++;
                }
            }

            progress?.Report(new StorageScanProgress(scannedDirectories, candidateFiles, rootPath));
            var items = topFiles.UnorderedItems.Select(entry => entry.Element)
                .OrderByDescending(file => file.FileSizeBytes).ToList();
            return new StorageScanResult(items, scannedDirectories, candidateFiles, skippedDirectories, ct.IsCancellationRequested);
        });
    }

    private static void AddTopFile(PriorityQueue<LargeFileInfo, long> topFiles, LargeFileInfo item, int topCount)
    {
        if (topFiles.Count < topCount)
        {
            topFiles.Enqueue(item, item.FileSizeBytes);
            return;
        }

        topFiles.TryPeek(out _, out var smallestSize);
        if (item.FileSizeBytes <= smallestSize) return;
        topFiles.Dequeue();
        topFiles.Enqueue(item, item.FileSizeBytes);
    }

    private static bool ShouldScanDirectory(DirectoryInfo directory) =>
        (directory.Attributes & (FileAttributes.ReparsePoint | FileAttributes.Hidden)) == 0 &&
        !directory.Name.StartsWith("$", StringComparison.OrdinalIgnoreCase) &&
        !directory.Name.Equals("System Volume Information", StringComparison.OrdinalIgnoreCase) &&
        !directory.Name.Equals("Windows", StringComparison.OrdinalIgnoreCase);
}
