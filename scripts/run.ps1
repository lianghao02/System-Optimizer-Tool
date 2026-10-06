[CmdletBinding()]
param([switch]$ValidateOnly)

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
try {
    $target = @('dist\standalone\SystemOptimizer.App.exe',
        'dist\slim\SystemOptimizer.App.exe', 'dist\SystemOptimizer.App.exe') |
        ForEach-Object { Join-Path $root $_ } |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
        Select-Object -First 1
    if (-not $target) { throw '找不到發行程式。請執行 dotnet-src\build_release.ps1 建立 dist 成品。' }
    if ($ValidateOnly) { Write-Output $target; return }
    Start-Process -FilePath $target -WorkingDirectory (Split-Path $target -Parent) -WindowStyle Normal
} catch {
    if (-not $ValidateOnly) {
        Add-Type -AssemblyName System.Windows.Forms
        [void][Windows.Forms.MessageBox]::Show($_.Exception.Message, '系統優化工具啟動失敗')
    }
    throw
}
