using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using SystemOptimizer.Core.Models;
using SystemOptimizer.Core.Native;

namespace SystemOptimizer.Core.Services;

public class MemoryOptimizer
{
    public int LastWorkingSetSkippedProcessCount { get; private set; }
    public string? LastStandbyPurgeError { get; private set; }

    public SystemMetrics GetMetrics()
    {
        var memStatus = new NativeMethods.MEMORYSTATUSEX();
        memStatus.dwLength = (uint)Marshal.SizeOf(typeof(NativeMethods.MEMORYSTATUSEX));
        
        if (NativeMethods.GlobalMemoryStatusEx(ref memStatus))
        {
            return new SystemMetrics(
                memStatus.ullTotalPhys,
                memStatus.ullAvailPhys,
                memStatus.dwMemoryLoad,
                Process.GetProcesses().Length
            );
        }

        return new SystemMetrics(0, 0, 0, 0);
    }

    public long OptimizeWorkingSets()
    {
        LastWorkingSetSkippedProcessCount = 0;
        var before = GetMetrics().AvailablePhysicalBytes;
        var processes = Process.GetProcesses();

        foreach (var proc in processes)
        {
            try
            {
                if (!proc.HasExited && proc.Id > 4)
                {
                    NativeMethods.EmptyWorkingSet(proc.Handle);
                }
            }
            catch (Exception)
            {
                // 系統處理程序可能拒絕存取，安全略過並保留統計供介面回報。
                LastWorkingSetSkippedProcessCount++;
            }
            finally
            {
                proc.Dispose();
            }
        }

        GC.Collect();
        GC.WaitForPendingFinalizers();

        var after = GetMetrics().AvailablePhysicalBytes;
        return after > before ? (long)(after - before) : 0;
    }

    public bool PurgeStandbyList()
    {
        IntPtr pCommand = IntPtr.Zero;
        LastStandbyPurgeError = null;
        try
        {
            var command = NativeMethods.MemoryPurgeStandbyList;
            pCommand = Marshal.AllocHGlobal(sizeof(int));
            Marshal.WriteInt32(pCommand, command);

            var status = NativeMethods.NtSetSystemInformation(
                NativeMethods.SystemMemoryListInformation,
                pCommand,
                sizeof(int)
            );
            return status == 0;
        }
        catch (Exception ex)
        {
            LastStandbyPurgeError = ex.Message;
            return false;
        }
        finally
        {
            if (pCommand != IntPtr.Zero)
                Marshal.FreeHGlobal(pCommand);
        }
    }
}
