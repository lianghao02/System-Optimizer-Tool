using System;
using System.Collections.Generic;
using Microsoft.Win32;
using SystemOptimizer.Core.Models;

namespace SystemOptimizer.Core.Services;

public class StartupManager
{
    public List<StartupItem> GetStartupItems()
    {
        var items = new List<StartupItem>();

        // HKCU Run
        ReadRegistryRun(Registry.CurrentUser, @"Software\Microsoft\Windows\CurrentVersion\Run", "當前使用者 (HKCU)", items);

        // HKLM Run
        ReadRegistryRun(Registry.LocalMachine, @"Software\Microsoft\Windows\CurrentVersion\Run", "本機全域 (HKLM)", items);

        return items;
    }

    private void ReadRegistryRun(RegistryKey root, string subKeyPath, string locationName, List<StartupItem> list)
    {
        try
        {
            using var key = root.OpenSubKey(subKeyPath);
            if (key != null)
            {
                foreach (var valueName in key.GetValueNames())
                {
                    var cmd = key.GetValue(valueName)?.ToString() ?? string.Empty;
                    list.Add(new StartupItem(valueName, cmd, locationName, true));
                }
            }
        }
        catch { }
    }
}
