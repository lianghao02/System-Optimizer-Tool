using System;
using System.IO;
using System.Reflection;

namespace SystemOptimizer.Core.Services;

public static class VersionInfoService
{
    public static string GetCurrentVersion()
    {
        var versionPath = Path.Combine(AppContext.BaseDirectory, "version.txt");
        if (File.Exists(versionPath))
        {
            var version = File.ReadAllText(versionPath).Trim();
            if (!string.IsNullOrWhiteSpace(version))
                return NormalizeVersion(version);
        }

        return NormalizeVersion(Assembly.GetEntryAssembly()?.GetName().Version?.ToString() ?? "0.0.0");
    }

    public static string NormalizeVersion(string version) => version.Trim().TrimStart('v', 'V');
}
