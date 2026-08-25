using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using SystemOptimizer.Core.Models;

namespace SystemOptimizer.Core.Services;

public class CacheCleaner
{
    private readonly SafetyGuard _safetyGuard = new();

    public record CacheTarget(string Category, string Path, string Description, string? AssociatedProcess = null);

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

    public async Task<List<CacheItem>> ScanTargetsAsync(IProgress<string>? progress = null, CancellationToken ct = default)
    {
        return await Task.Run(() =>
        {
            var results = new List<CacheItem>();
            var targets = GetDefaultTargets();

            foreach (var target in targets)
            {
                if (ct.IsCancellationRequested) break;
                progress?.Report($"正在掃描：{target.Category}...");

                if (!_safetyGuard.IsSafeTarget(target.Path) || !Directory.Exists(target.Path))
                    continue;

                long size = 0;
                int count = 0;

                try
                {
                    var dirInfo = new DirectoryInfo(target.Path);
                    foreach (var file in dirInfo.EnumerateFiles("*", SearchOption.AllDirectories))
                    {
                        if (ct.IsCancellationRequested) break;
                        try
                        {
                            size += file.Length;
                            count++;
                        }
                        catch { }
                    }
                }
                catch { }

                if (count > 0)
                {
                    string note = "";
                    if (!string.IsNullOrEmpty(target.AssociatedProcess))
                    {
                        if (Process.GetProcessesByName(target.AssociatedProcess).Length > 0)
                        {
                            note = $"⚠️ 應用程式執行中 (鎖定檔將安全略過)";
                        }
                    }

                    results.Add(new CacheItem(target.Category, target.Path, size, count, note));
                }
            }

            return results;
        }, ct);
    }

    public async Task<OptimizationResult> CleanTargetsAsync(IEnumerable<CacheItem> items, IProgress<string>? progress = null, CancellationToken ct = default)
    {
        var sw = Stopwatch.StartNew();
        long freedBytes = 0;
        int deletedFiles = 0;

        await Task.Run(() =>
        {
            foreach (var item in items)
            {
                if (ct.IsCancellationRequested) break;
                if (!item.IsSelected) continue; // 僅清理勾選項

                progress?.Report($"正在清理：{item.Category}...");

                if (!_safetyGuard.IsSafeTarget(item.Path) || !Directory.Exists(item.Path))
                    continue;

                try
                {
                    var dirInfo = new DirectoryInfo(item.Path);
                    foreach (var file in dirInfo.EnumerateFiles("*", SearchOption.AllDirectories))
                    {
                        if (ct.IsCancellationRequested) break;
                        try
                        {
                            var len = file.Length;
                            file.Delete();
                            freedBytes += len;
                            deletedFiles++;
                        }
                        catch
                        {
                            // In-use locked files are safely skipped
                        }
                    }

                    foreach (var dir in dirInfo.EnumerateDirectories("*", SearchOption.AllDirectories))
                    {
                        try
                        {
                            if (dir.Exists && dir.GetFileSystemInfos().Length == 0)
                            {
                                dir.Delete();
                            }
                        }
                        catch { }
                    }
                }
                catch { }
            }
        }, ct);

        sw.Stop();
        return new OptimizationResult(freedBytes, deletedFiles, 0, sw.Elapsed, $"清理完成，共釋放 {CacheItem.FormatBytes(freedBytes)} 空間！");
    }
}
