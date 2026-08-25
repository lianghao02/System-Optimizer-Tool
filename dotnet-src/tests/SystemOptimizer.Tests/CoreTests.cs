using System;
using System.IO;
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
}
