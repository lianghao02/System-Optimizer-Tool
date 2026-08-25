using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using SystemOptimizer.Core.Models;
using SystemOptimizer.Core.Native;

namespace SystemOptimizer.Core.Services;

public class MemoryOptimizer
{
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
            catch
            {
                // Access denied on system processes is expected and ignored safely
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
        try
        {
            var command = NativeMethods.MemoryPurgeStandbyList;
            var pCommand = Marshal.AllocHGlobal(sizeof(int));
            Marshal.WriteInt32(pCommand, command);

            var status = NativeMethods.NtSetSystemInformation(
                NativeMethods.SystemMemoryListInformation,
                pCommand,
                sizeof(int)
            );

            Marshal.FreeHGlobal(pCommand);
            return status == 0;
        }
        catch
        {
            return false;
        }
    }
}
