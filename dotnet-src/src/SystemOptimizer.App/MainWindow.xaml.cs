using System;
using System.Drawing;
using System.IO;
using System.Windows;
using System.Windows.Forms;
using SystemOptimizer.App.ViewModels;

namespace SystemOptimizer.App;

public partial class MainWindow : Window
{
    private NotifyIcon? _notifyIcon;

    public MainWindow()
    {
        InitializeComponent();
        InitializeSystemTray();
    }

    private void InitializeSystemTray()
    {
        try
        {
            _notifyIcon = new NotifyIcon
            {
                Text = "Windows 系統極速優化工具",
                Visible = true
            };

            var iconUri = new Uri("pack://application:,,,/app_icon.ico");
            var iconStream = System.Windows.Application.GetResourceStream(iconUri)?.Stream;
            if (iconStream != null)
            {
                _notifyIcon.Icon = new Icon(iconStream);
            }
            else
            {
                _notifyIcon.Icon = SystemIcons.Application;
            }

            var contextMenu = new ContextMenuStrip();
            contextMenu.Items.Add("顯示主畫面", null, (s, e) => ShowAndRestore());
            contextMenu.Items.Add("⚡ 立即釋放記憶體", null, async (s, e) =>
            {
                if (DataContext is MainViewModel vm)
                {
                    await vm.OptimizeMemoryAsync();
                    _notifyIcon.ShowBalloonTip(2000, "記憶體優化", vm.StatusMessage, ToolTipIcon.Info);
                }
            });
            contextMenu.Items.Add(new ToolStripSeparator());
            contextMenu.Items.Add("結束程式", null, (s, e) =>
            {
                _notifyIcon.Visible = false;
                _notifyIcon.Dispose();
                System.Windows.Application.Current.Shutdown();
            });

            _notifyIcon.ContextMenuStrip = contextMenu;
            _notifyIcon.DoubleClick += (s, e) => ShowAndRestore();
        }
        catch
        {
            // System tray fallback
        }
    }

    private void ShowAndRestore()
    {
        Show();
        WindowState = WindowState.Normal;
        Activate();
    }

    protected override void OnStateChanged(EventArgs e)
    {
        base.OnStateChanged(e);
        if (WindowState == WindowState.Minimized)
        {
            // 最小化至系統匣
            Hide();
            _notifyIcon?.ShowBalloonTip(1500, "Windows 系統極速優化工具", "應用程式已最小化至右下角系統匣常駐執行。", ToolTipIcon.Info);
        }
    }

    protected override void OnClosed(EventArgs e)
    {
        if (_notifyIcon != null)
        {
            _notifyIcon.Visible = false;
            _notifyIcon.Dispose();
        }
        base.OnClosed(e);
    }
}
