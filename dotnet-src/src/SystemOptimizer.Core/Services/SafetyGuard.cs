using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace SystemOptimizer.Core.Services;

public class SafetyGuard
{
    private static readonly HashSet<string> ProtectedFolders = new(StringComparer.OrdinalIgnoreCase)
    {
        Environment.GetFolderPath(Environment.SpecialFolder.System),
        Environment.GetFolderPath(Environment.SpecialFolder.Windows),
        Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
        Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
    };

    /// <summary>
    /// 清理目標必須同時滿足：非磁碟根目錄、非系統關鍵資料夾本身，且精確命中核准清單。
    /// 核准清單內的子資料夾（如 Windows\Temp）不受影響，但清單被誤植為 Windows、System32 等根層時一律拒絕。
    /// </summary>
    public bool IsApprovedCacheTarget(string path, IEnumerable<string> approvedPaths)
    {
        if (string.IsNullOrWhiteSpace(path)) return false;

        try
        {
            var fullPath = Path.GetFullPath(path);
            var root = Path.GetPathRoot(fullPath);
            if (string.Equals(fullPath, root, StringComparison.OrdinalIgnoreCase)) return false;

            var trimmed = fullPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            if (ProtectedFolders.Any(folder => !string.IsNullOrWhiteSpace(folder) &&
                    string.Equals(trimmed, folder.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar), StringComparison.OrdinalIgnoreCase)))
                return false;

            return approvedPaths.Any(approvedPath =>
                !string.IsNullOrWhiteSpace(approvedPath) &&
                string.Equals(fullPath, Path.GetFullPath(approvedPath), StringComparison.OrdinalIgnoreCase));
        }
        catch
        {
            return false;
        }
    }
}
