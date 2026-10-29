using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using SystemOptimizer.Core.Native;

namespace SystemOptimizer.Core.Services;

public static class PrivilegeHelper
{
    public const string ProfileSingleProcessPrivilege = "SeProfileSingleProcessPrivilege";

    public static bool IsElevated()
    {
        try
        {
            using var identity = WindowsIdentity.GetCurrent();
            return new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator);
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// 在目前處理程序權杖上啟用指定特權。帳號未持有該特權（例如未提權）時回傳 false 並說明原因。
    /// </summary>
    public static bool TryEnablePrivilege(string privilegeName, out string? error)
    {
        error = null;
        IntPtr token = IntPtr.Zero;
        try
        {
            if (!NativeMethods.OpenProcessToken(Process.GetCurrentProcess().Handle,
                    NativeMethods.TOKEN_ADJUST_PRIVILEGES | NativeMethods.TOKEN_QUERY, out token))
            {
                error = $"無法開啟處理程序權杖 (Win32 錯誤 {Marshal.GetLastWin32Error()})";
                return false;
            }

            if (!NativeMethods.LookupPrivilegeValue(null, privilegeName, out var luid))
            {
                error = $"無法查詢特權 {privilegeName} (Win32 錯誤 {Marshal.GetLastWin32Error()})";
                return false;
            }

            var state = new NativeMethods.TOKEN_PRIVILEGES
            {
                PrivilegeCount = 1,
                Luid = luid,
                Attributes = NativeMethods.SE_PRIVILEGE_ENABLED,
            };

            // AdjustTokenPrivileges 即使回傳 true，仍須以 GetLastError 判斷特權是否真的被指派。
            var adjusted = NativeMethods.AdjustTokenPrivileges(token, false, ref state, 0, IntPtr.Zero, IntPtr.Zero);
            var lastError = Marshal.GetLastWin32Error();
            if (!adjusted || lastError == NativeMethods.ERROR_NOT_ALL_ASSIGNED)
            {
                error = "目前帳號未持有所需特權，請以系統管理員身分重新啟動";
                return false;
            }

            return true;
        }
        catch (Exception ex)
        {
            error = ex.Message;
            return false;
        }
        finally
        {
            if (token != IntPtr.Zero)
                NativeMethods.CloseHandle(token);
        }
    }
}
