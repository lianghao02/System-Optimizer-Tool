using System;
using System.Collections.Generic;
using Microsoft.Win32;
using SystemOptimizer.Core.Models;

namespace SystemOptimizer.Core.Services;

public class StartupManager
{
    private const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
    private const string ApprovedRunKey = @"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run";

    public List<StartupItem> GetStartupItems()
    {
        var items = new List<StartupItem>();

        ReadRegistryRun(Registry.CurrentUser, "當前使用者 (HKCU)", items);
        ReadRegistryRun(Registry.LocalMachine, "本機全域 (HKLM)", items);

        return items;
    }

    /// <summary>
    /// StartupApproved 的值為二進位資料，第一個位元組最低位為 1 代表使用者已在工作管理員停用；缺少紀錄視為啟用。
    /// </summary>
    public static bool IsApprovedFlag(object? approvedValue)
    {
        return approvedValue is not byte[] data || data.Length == 0 || (data[0] & 1) == 0;
    }

    private void ReadRegistryRun(RegistryKey root, string locationName, List<StartupItem> list)
    {
        try
        {
            using var key = root.OpenSubKey(RunKey);
            if (key == null) return;

            using var approvedKey = root.OpenSubKey(ApprovedRunKey);
            foreach (var valueName in key.GetValueNames())
            {
                var cmd = key.GetValue(valueName)?.ToString() ?? string.Empty;
                var enabled = IsApprovedFlag(approvedKey?.GetValue(valueName));
                list.Add(new StartupItem(valueName, cmd, locationName, enabled));
            }
        }
        catch { }
    }
}
