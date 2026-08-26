using System;
using System.Collections.Generic;
using System.IO;

namespace SystemOptimizer.Core.Services;

public class SafetyGuard
{
    private static readonly HashSet<string> ProtectedFolders = new(StringComparer.OrdinalIgnoreCase)
    {
        Environment.GetFolderPath(Environment.SpecialFolder.System),
        Environment.GetFolderPath(Environment.SpecialFolder.Windows),
        Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
        Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
    };

    public bool IsSafeTarget(string path)
    {
        if (string.IsNullOrWhiteSpace(path)) return false;
        try
        {
            var fullPath = Path.GetFullPath(path);
            var root = Path.GetPathRoot(fullPath);
            if (string.Equals(fullPath, root, StringComparison.OrdinalIgnoreCase)) return false;

            return !ProtectedFolders.Any(protectedFolder => IsSameOrChildPath(fullPath, protectedFolder));
        }
        catch
        {
            return false;
        }
    }

    public bool IsApprovedCacheTarget(string path, IEnumerable<string> approvedPaths)
    {
        if (string.IsNullOrWhiteSpace(path)) return false;

        try
        {
            var fullPath = Path.GetFullPath(path);
            var root = Path.GetPathRoot(fullPath);
            if (string.Equals(fullPath, root, StringComparison.OrdinalIgnoreCase)) return false;

            return approvedPaths.Any(approvedPath =>
                !string.IsNullOrWhiteSpace(approvedPath) &&
                string.Equals(fullPath, Path.GetFullPath(approvedPath), StringComparison.OrdinalIgnoreCase));
        }
        catch
        {
            return false;
        }
    }

    private static bool IsSameOrChildPath(string path, string parentPath)
    {
        var normalizedPath = path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        var normalizedParent = parentPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        return string.Equals(normalizedPath, normalizedParent, StringComparison.OrdinalIgnoreCase) ||
               normalizedPath.StartsWith(normalizedParent + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase);
    }
}
