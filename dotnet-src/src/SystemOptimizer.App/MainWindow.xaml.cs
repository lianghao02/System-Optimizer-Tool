using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net.Http;
using System.Windows;
using System.Windows.Forms;
using SystemOptimizer.App.ViewModels;
using SystemOptimizer.Core.Models;
using SystemOptimizer.Core.Services;

namespace SystemOptimizer.App;

public partial class MainWindow : Window
{
    private NotifyIcon? _notifyIcon;
    private readonly GitHubUpdateService _updateService = new();

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

    private async void SearchLargeFilesFromDrive_Click(object sender, RoutedEventArgs e)
    {
        if (DataContext is not MainViewModel viewModel || sender is not FrameworkElement { DataContext: DriveStorageInfo drive } || viewModel.IsBusy)
            return;

        viewModel.SelectedDrivePath = drive.DriveLetter;
        MainTabControl.SelectedIndex = 2;
        await viewModel.ScanLargeFilesAsync();
    }

    private async void CheckUpdates_Click(object sender, RoutedEventArgs e)
    {
        CheckUpdatesButton.IsEnabled = false;
        CheckUpdatesButton.Content = "⏳ 檢查中...";

        try
        {
            var release = await _updateService.GetLatestReleaseAsync();
            var currentVersion = VersionInfoService.GetCurrentVersion();
            if (release == null)
            {
                System.Windows.MessageBox.Show("GitHub 尚未建立可用的 Release，暫時無法檢查更新。", "檢查更新", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            if (!GitHubUpdateService.IsNewerVersion(release.Version, currentVersion))
            {
                System.Windows.MessageBox.Show($"目前使用 v{currentVersion}，已是最新版。", "檢查更新", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var notes = string.IsNullOrWhiteSpace(release.ReleaseNotes) ? "請至 GitHub Release 查看完整更新內容。" : release.ReleaseNotes;
            if (notes.Length > 700) notes = $"{notes[..700]}…";
            var choice = System.Windows.MessageBox.Show(
                $"發現新版本 v{release.Version}（目前 v{currentVersion}）。\n\n{notes}\n\n是否前往 GitHub Release 下載更新？",
                "發現新版本",
                MessageBoxButton.YesNo,
                MessageBoxImage.Information);

            if (choice == MessageBoxResult.Yes)
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = release.ReleaseUrl,
                    UseShellExecute = true,
                });
            }
        }
        catch (HttpRequestException ex)
        {
            System.Windows.MessageBox.Show($"無法連線至 GitHub Release，請確認網路連線後再試。\n\n{ex.Message}", "檢查更新失敗", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
        catch (TaskCanceledException)
        {
            System.Windows.MessageBox.Show("連線至 GitHub Release 逾時，請稍後再試。", "檢查更新失敗", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
        catch (Exception ex)
        {
            System.Windows.MessageBox.Show($"檢查更新時發生錯誤：{ex.Message}", "檢查更新失敗", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            CheckUpdatesButton.IsEnabled = true;
            CheckUpdatesButton.Content = "🔄 檢查更新";
        }
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
