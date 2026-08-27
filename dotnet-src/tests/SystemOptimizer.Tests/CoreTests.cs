using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using SystemOptimizer.Core.Services;

namespace SystemOptimizer.Tests;

public class CoreTests
{
    [Fact]
    public void SafetyGuard_BlocksRootAndSystemFolders()
    {
        var guard = new SafetyGuard();
        var sysDir = Environment.GetFolderPath(Environment.SpecialFolder.System);
        var winDir = Environment.GetFolderPath(Environment.SpecialFolder.Windows);

        Assert.False(guard.IsSafeTarget("C:\\"));
        Assert.False(guard.IsSafeTarget(sysDir));
        Assert.False(guard.IsSafeTarget(winDir));
        Assert.False(guard.IsSafeTarget(Path.Combine(winDir, "Temp")));
    }

    [Fact]
    public void SafetyGuard_AllowsOnlyRegisteredCacheTarget()
    {
        var guard = new SafetyGuard();
        var approvedPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), "Temp");
        var unrelatedPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), "Logs");

        Assert.True(guard.IsApprovedCacheTarget(approvedPath, new[] { approvedPath }));
        Assert.False(guard.IsApprovedCacheTarget(unrelatedPath, new[] { approvedPath }));
    }

    [Fact]
    public void MemoryOptimizer_RetrievesValidMetrics()
    {
        var optimizer = new MemoryOptimizer();
        var metrics = optimizer.GetMetrics();

        Assert.True(metrics.TotalPhysicalBytes > 0);
        Assert.True(metrics.AvailablePhysicalBytes > 0);
        Assert.True(metrics.MemoryLoadPercentage > 0 && metrics.MemoryLoadPercentage <= 100);
        Assert.True(metrics.ProcessCount > 0);
    }

    [Fact]
    public void CacheCleaner_ReturnsDefaultTargets()
    {
        var cleaner = new CacheCleaner();
        var targets = cleaner.GetDefaultTargets();

        Assert.NotEmpty(targets);
    }

    [Fact]
    public async Task CacheCleaner_DoesNotTraverseDirectoryJunction()
    {
        var root = Path.Combine(Path.GetTempPath(), $"SystemOptimizerTests-{Guid.NewGuid():N}");
        var externalDirectory = Path.Combine(Path.GetTempPath(), $"SystemOptimizerExternal-{Guid.NewGuid():N}");
        Directory.CreateDirectory(root);
        Directory.CreateDirectory(externalDirectory);

        var localFile = Path.Combine(root, "local-cache.tmp");
        var protectedFile = Path.Combine(externalDirectory, "must-not-delete.tmp");
        var junctionPath = Path.Combine(root, "external-link");
        File.WriteAllText(localFile, "local");
        File.WriteAllText(protectedFile, "external");

        try
        {
            CreateJunction(junctionPath, externalDirectory);
            var cleaner = new CacheCleaner(() => new List<CacheCleaner.CacheTarget>
            {
                new("測試快取", root, "測試用目錄")
            });

            var scanResult = await cleaner.ScanTargetsAsync();
            var item = Assert.Single(scanResult.Items);
            Assert.Equal(new FileInfo(localFile).Length, item.FileSizeBytes);
            Assert.Equal(1, item.FileCount);

            var cleanResult = await cleaner.CleanTargetsAsync(new[] { item });
            Assert.False(File.Exists(localFile));
            Assert.True(File.Exists(protectedFile));
            Assert.Equal(1, cleanResult.FilesDeleted);
        }
        finally
        {
            if (Directory.Exists(junctionPath)) Directory.Delete(junctionPath);
            if (Directory.Exists(root)) Directory.Delete(root, true);
            if (Directory.Exists(externalDirectory)) Directory.Delete(externalDirectory, true);
        }
    }

    [Fact]
    public async Task CacheCleaner_ReportsCanceledScan()
    {
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();
        var cleaner = new CacheCleaner();

        var result = await cleaner.ScanTargetsAsync(ct: cancellation.Token);

        Assert.True(result.WasCanceled);
    }

    [Fact]
    public async Task StorageAnalyzer_KeepsOnlyLargestRequestedFiles()
    {
        var root = Path.Combine(Path.GetTempPath(), $"SystemOptimizerStorage-{Guid.NewGuid():N}");
        Directory.CreateDirectory(root);

        try
        {
            CreateFileWithLength(Path.Combine(root, "small.bin"), 100);
            CreateFileWithLength(Path.Combine(root, "medium.bin"), 200);
            CreateFileWithLength(Path.Combine(root, "large.bin"), 300);

            var analyzer = new StorageAnalyzer();
            var result = await analyzer.ScanLargeFilesAsync(root, 1, 2);

            Assert.Equal(3, result.CandidateFileCount);
            Assert.Equal(2, result.Items.Count);
            Assert.Equal(new[] { 300L, 200L }, result.Items.Select(file => file.FileSizeBytes));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }
    }

    [Theory]
    [InlineData("v6.2.2", "6.2.1", true)]
    [InlineData("6.2.1", "6.2.1", false)]
    [InlineData("6.2.0", "6.2.1", false)]
    public void GitHubUpdateService_ComparesReleaseVersions(string latestVersion, string currentVersion, bool expected)
    {
        Assert.Equal(expected, GitHubUpdateService.IsNewerVersion(latestVersion, currentVersion));
    }

    private static void CreateFileWithLength(string path, long length)
    {
        using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write);
        stream.SetLength(length);
    }

    private static void CreateJunction(string junctionPath, string targetPath)
    {
        using var process = Process.Start(new ProcessStartInfo
        {
            FileName = "cmd.exe",
            Arguments = $"/c mklink /J \"{junctionPath}\" \"{targetPath}\"",
            CreateNoWindow = true,
            UseShellExecute = false,
        });
        process!.WaitForExit();
        Assert.True(process.ExitCode == 0 && Directory.Exists(junctionPath), "無法建立測試用目錄 Junction。");
    }
}
