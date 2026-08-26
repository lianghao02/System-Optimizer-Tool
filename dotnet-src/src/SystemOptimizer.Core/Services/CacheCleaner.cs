using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using SystemOptimizer.Core.Models;

namespace SystemOptimizer.Core.Services;

public class CacheCleaner
{
    private readonly SafetyGuard _safetyGuard = new();
    private readonly Func<List<CacheTarget>>? _targetProvider;

    public record CacheTarget(string Category, string Path, string Description, string? AssociatedProcess = null);

    public CacheCleaner(Func<List<CacheTarget>>? targetProvider = null)
    {
        _targetProvider = targetProvider;
    }

    public List<CacheTarget> GetDefaultTargets()
    {
        var list = new List<CacheTarget>();

        var userTemp = Path.GetTempPath();
        if (Directory.Exists(userTemp))
            list.Add(new CacheTarget("使用者暫存檔", userTemp, "應用程式運行暫留檔"));

        var winDir = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
        var winTemp = Path.Combine(winDir, "Temp");
        if (Directory.Exists(winTemp))
            list.Add(new CacheTarget("Windows 系統暫存", winTemp, "系統更新與安裝殘留暫存"));

        var prefetch = Path.Combine(winDir, "Prefetch");
        if (Directory.Exists(prefetch))
            list.Add(new CacheTarget("Windows 預先讀取檔", prefetch, "系統過期預讀快取"));

        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);

        var crashDumps = Path.Combine(localAppData, "CrashDumps");
        if (Directory.Exists(crashDumps))
            list.Add(new CacheTarget("應用程式崩潰傾印 (Dumps)", crashDumps, "程式錯誤紀錄 DUMP"));

        var softDist = Path.Combine(winDir, "SoftwareDistribution", "Download");
        if (Directory.Exists(softDist))
            list.Add(new CacheTarget("Windows Update 安裝快取", softDist, "已安裝之更新快取檔"));

        var deliveryOpt = Path.Combine(winDir, "SoftwareDistribution", "DeliveryOptimization");
        if (Directory.Exists(deliveryOpt))
            list.Add(new CacheTarget("Windows 傳遞最佳化快取", deliveryOpt, "對等更新傳遞快取"));

        var thumbCache = Path.Combine(localAppData, "Microsoft", "Windows", "Explorer");
        if (Directory.Exists(thumbCache))
            list.Add(new CacheTarget("Windows 檔案總管縮圖快取", thumbCache, "圖檔與影片縮圖資料庫"));

        var d3dCache = Path.Combine(localAppData, "D3DSCache");
        if (Directory.Exists(d3dCache))
            list.Add(new CacheTarget("DirectX 著色器快取", d3dCache, "DirectX 3D 圖形著色快取"));

        var nvCache = Path.Combine(localAppData, "NVIDIA", "DXCache");
        if (Directory.Exists(nvCache))
            list.Add(new CacheTarget("NVIDIA 著色器快取", nvCache, "NVIDIA 顯示卡圖形著色快取"));

        var winLogs = Path.Combine(winDir, "Logs");
        if (Directory.Exists(winLogs))
            list.Add(new CacheTarget("Windows 系統記錄檔 (Logs)", winLogs, "系統維護與安裝記錄檔"));

        // Google Chrome
        var chromeCache = Path.Combine(localAppData, "Google", "Chrome", "User Data", "Default", "Cache", "Cache_Data");
        if (Directory.Exists(chromeCache))
            list.Add(new CacheTarget("Google Chrome 網頁快取", chromeCache, "Chrome 瀏覽器暫存檔", "chrome"));

        var chromeCodeCache = Path.Combine(localAppData, "Google", "Chrome", "User Data", "Default", "Code Cache");
        if (Directory.Exists(chromeCodeCache))
            list.Add(new CacheTarget("Google Chrome 代碼快取", chromeCodeCache, "JS/Wasm 編譯快取", "chrome"));

        // Microsoft Edge
        var edgeCache = Path.Combine(localAppData, "Microsoft", "Edge", "User Data", "Default", "Cache", "Cache_Data");
        if (Directory.Exists(edgeCache))
            list.Add(new CacheTarget("Microsoft Edge 網頁快取", edgeCache, "Edge 瀏覽器暫存檔", "msedge"));

        var edgeCodeCache = Path.Combine(localAppData, "Microsoft", "Edge", "User Data", "Default", "Code Cache");
        if (Directory.Exists(edgeCodeCache))
            list.Add(new CacheTarget("Microsoft Edge 代碼快取", edgeCodeCache, "Edge JS/Wasm 快取", "msedge"));

        // VS Code
        var vscodeCache = Path.Combine(appData, "Code", "Cache");
        if (Directory.Exists(vscodeCache))
            list.Add(new CacheTarget("VS Code 編輯器快取", vscodeCache, "Visual Studio Code 暫存", "Code"));

        // Discord
        var discordCache = Path.Combine(appData, "discord", "Cache", "Cache_Data");
        if (Directory.Exists(discordCache))
            list.Add(new CacheTarget("Discord 通訊軟體快取", discordCache, "Discord 圖片與語音快取", "Discord"));

        // Spotify
        var spotifyCache = Path.Combine(localAppData, "Spotify", "Storage");
        if (Directory.Exists(spotifyCache))
            list.Add(new CacheTarget("Spotify 音樂串流快取", spotifyCache, "本機離線串流快取", "Spotify"));

        return list;
    }

    public async Task<CacheScanResult> ScanTargetsAsync(IProgress<OperationProgress>? progress = null, CancellationToken ct = default)
    {
        if (ct.IsCancellationRequested)
            return new CacheScanResult(Array.Empty<CacheItem>(), 0, 0, true);

        return await Task.Run(() =>
        {
            var results = new List<CacheItem>();
            var issues = new List<string>();
            var targets = GetActiveTargets();
            var approvedPaths = targets.Select(target => target.Path).ToHashSet(StringComparer.OrdinalIgnoreCase);
            var skippedFiles = 0;
            var errorCount = 0;

            for (var targetIndex = 0; targetIndex < targets.Count; targetIndex++)
            {
                if (ct.IsCancellationRequested)
                    return new CacheScanResult(results, skippedFiles, errorCount, true, CreateErrorSummary(issues));

                var target = targets[targetIndex];
                progress?.Report(new OperationProgress(GetProgress(targetIndex, targets.Count), $"正在掃描：{target.Category}..."));

                if (!_safetyGuard.IsApprovedCacheTarget(target.Path, approvedPaths) || !Directory.Exists(target.Path))
                    continue;

                long size = 0;
                int count = 0;

                try
                {
                    var dirInfo = new DirectoryInfo(target.Path);
                    if ((dirInfo.Attributes & FileAttributes.ReparsePoint) != 0)
                    {
                        AddIssue(issues, $"略過目錄連結：{target.Category}");
                        skippedFiles++;
                        continue;
                    }

                    foreach (var file in dirInfo.EnumerateFiles("*", SafeEnumerationOptions))
                    {
                        if (ct.IsCancellationRequested)
                            return new CacheScanResult(results, skippedFiles, errorCount, true, CreateErrorSummary(issues));
                        try
                        {
                            size += file.Length;
                            count++;
                        }
                        catch (Exception ex)
                        {
                            skippedFiles++;
                            errorCount++;
                            AddIssue(issues, $"無法讀取 {file.Name}：{ex.Message}");
                        }
                    }
                }
                catch (Exception ex)
                {
                    errorCount++;
                    AddIssue(issues, $"無法掃描 {target.Category}：{ex.Message}");
                }

                if (count > 0)
                {
                    string note = "";
                    if (!string.IsNullOrEmpty(target.AssociatedProcess))
                    {
                        var processes = Process.GetProcessesByName(target.AssociatedProcess);
                        try
                        {
                            if (processes.Length > 0)
                                note = $"⚠️ 應用程式執行中 (鎖定檔將安全略過)";
                        }
                        finally
                        {
                            foreach (var process in processes)
                                process.Dispose();
                        }
                    }

                    results.Add(new CacheItem(target.Category, target.Path, size, count, note));
                }
            }

            progress?.Report(new OperationProgress(100, "快取掃描完成"));
            return new CacheScanResult(results, skippedFiles, errorCount, false, CreateErrorSummary(issues));
        }, ct);
    }

    public async Task<OptimizationResult> CleanTargetsAsync(IEnumerable<CacheItem> items, IProgress<OperationProgress>? progress = null, CancellationToken ct = default)
    {
        var sw = Stopwatch.StartNew();
        long freedBytes = 0;
        int deletedFiles = 0;
        int skippedFiles = 0;
        int errorCount = 0;
        var issues = new List<string>();
        var selectedItems = items.Where(item => item.IsSelected).ToList();

        if (!ct.IsCancellationRequested)
            await Task.Run(() =>
        {
            var approvedPaths = GetActiveTargets().Select(target => target.Path).ToHashSet(StringComparer.OrdinalIgnoreCase);
            for (var itemIndex = 0; itemIndex < selectedItems.Count; itemIndex++)
            {
                if (ct.IsCancellationRequested) break;
                var item = selectedItems[itemIndex];

                progress?.Report(new OperationProgress(GetProgress(itemIndex, selectedItems.Count), $"正在清理：{item.Category}..."));

                if (!_safetyGuard.IsApprovedCacheTarget(item.Path, approvedPaths) || !Directory.Exists(item.Path))
                    continue;

                try
                {
                    var dirInfo = new DirectoryInfo(item.Path);
                    if ((dirInfo.Attributes & FileAttributes.ReparsePoint) != 0)
                    {
                        skippedFiles++;
                        AddIssue(issues, $"略過目錄連結：{item.Category}");
                        continue;
                    }

                    foreach (var file in dirInfo.EnumerateFiles("*", SafeEnumerationOptions))
                    {
                        if (ct.IsCancellationRequested) break;
                        try
                        {
                            var len = file.Length;
                            file.Delete();
                            freedBytes += len;
                            deletedFiles++;
                        }
                        catch (Exception ex)
                        {
                            skippedFiles++;
                            errorCount++;
                            AddIssue(issues, $"略過 {file.Name}：{ex.Message}");
                        }
                    }

                    foreach (var dir in dirInfo.EnumerateDirectories("*", SafeEnumerationOptions)
                                               .OrderByDescending(dir => dir.FullName.Length))
                    {
                        try
                        {
                            if (dir.Exists && dir.GetFileSystemInfos().Length == 0)
                            {
                                dir.Delete();
                            }
                        }
                        catch (Exception ex)
                        {
                            errorCount++;
                            AddIssue(issues, $"無法移除空目錄 {dir.Name}：{ex.Message}");
                        }
                    }
                }
                catch (Exception ex)
                {
                    errorCount++;
                    AddIssue(issues, $"無法清理 {item.Category}：{ex.Message}");
                }
            }
        });

        sw.Stop();
        var wasCanceled = ct.IsCancellationRequested;
        var message = wasCanceled
            ? $"已取消清理，已釋放 {CacheItem.FormatBytes(freedBytes)} 空間。"
            : $"清理完成，共釋放 {CacheItem.FormatBytes(freedBytes)} 空間。";
        progress?.Report(new OperationProgress(100, message));
        return new OptimizationResult(freedBytes, deletedFiles, 0, sw.Elapsed, message, skippedFiles, errorCount, wasCanceled, CreateErrorSummary(issues));
    }

    private List<CacheTarget> GetActiveTargets() => _targetProvider?.Invoke() ?? GetDefaultTargets();

    private static int GetProgress(int completed, int total) => total == 0 ? 100 : completed * 100 / total;

    private static void AddIssue(List<string> issues, string message)
    {
        if (issues.Count < 3)
            issues.Add(message);
    }

    private static string? CreateErrorSummary(List<string> issues) => issues.Count == 0 ? null : string.Join("；", issues);

    private static readonly EnumerationOptions SafeEnumerationOptions = new()
    {
        RecurseSubdirectories = true,
        IgnoreInaccessible = true,
        AttributesToSkip = FileAttributes.ReparsePoint,
    };
}
