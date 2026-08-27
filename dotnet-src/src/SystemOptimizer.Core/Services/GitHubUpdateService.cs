using System;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using SystemOptimizer.Core.Models;

namespace SystemOptimizer.Core.Services;

public sealed class GitHubUpdateService
{
    private const string LatestReleaseEndpoint = "https://api.github.com/repos/lianghao02/System-Optimizer-Tool/releases/latest";
    private static readonly HttpClient HttpClient = CreateHttpClient();

    public async Task<LatestReleaseInfo?> GetLatestReleaseAsync(CancellationToken cancellationToken = default)
    {
        using var response = await HttpClient.GetAsync(LatestReleaseEndpoint, cancellationToken);
        if (response.StatusCode == HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();

        await using var content = await response.Content.ReadAsStreamAsync(cancellationToken);
        using var document = await JsonDocument.ParseAsync(content, cancellationToken: cancellationToken);
        var root = document.RootElement;
        var version = VersionInfoService.NormalizeVersion(root.GetProperty("tag_name").GetString() ?? "0.0.0");
        var releaseUrl = root.GetProperty("html_url").GetString() ?? "https://github.com/lianghao02/System-Optimizer-Tool/releases";
        var releaseNotes = root.TryGetProperty("body", out var body) ? body.GetString() ?? "" : "";
        string? downloadUrl = null;

        if (root.TryGetProperty("assets", out var assets) && assets.GetArrayLength() > 0)
            downloadUrl = assets[0].GetProperty("browser_download_url").GetString();

        return new LatestReleaseInfo(version, releaseUrl, downloadUrl, releaseNotes);
    }

    public static bool IsNewerVersion(string latestVersion, string currentVersion)
    {
        return Version.TryParse(VersionInfoService.NormalizeVersion(latestVersion), out var latest) &&
               Version.TryParse(VersionInfoService.NormalizeVersion(currentVersion), out var current) &&
               latest > current;
    }

    private static HttpClient CreateHttpClient()
    {
        var client = new HttpClient { Timeout = TimeSpan.FromSeconds(12) };
        client.DefaultRequestHeaders.UserAgent.ParseAdd("SystemOptimizerTool/6.2");
        client.DefaultRequestHeaders.Accept.ParseAdd("application/vnd.github+json");
        return client;
    }
}
