[CmdletBinding()]
param(
    [ValidateSet('all', 'slim', 'standalone')]
    [string]$Target = 'all',
    [switch]$RunAfterBuild
)

$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
$dotnet = "dotnet"

$localDotnet = Join-Path $env:LOCALAPPDATA 'Microsoft\dotnet\dotnet.exe'
if (Test-Path $localDotnet) {
    $dotnet = $localDotnet
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "【SystemOptimizer.App】C# .NET 8 原生單檔編譯與雙版本發布系統" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

$appCsproj = Join-Path $projectDir 'src\SystemOptimizer.App\SystemOptimizer.App.csproj'
$baseOutputDir = Join-Path $projectDir 'publish'
$slimDir = Join-Path $baseOutputDir 'slim'
$standaloneDir = Join-Path $baseOutputDir 'standalone'

# 1. 輕量版 (需要 .NET 8 Desktop Runtime，體積 < 0.5 MB)
if ($Target -in @('all', 'slim')) {
    Write-Host "[1/2] 正在編譯發布【輕量版 (Slim)】(依賴 .NET 8 Desktop Runtime)..." -ForegroundColor Green
    & $dotnet publish $appCsproj -c Release -r win-x64 --self-contained false -o $slimDir -p:PublishSingleFile=true
    
    $slimExe = Join-Path $slimDir 'SystemOptimizer.App.exe'
    if (Test-Path $slimExe) {
        $size = (Get-Item $slimExe).Length / 1MB
        Write-Host "      ✓ 輕量版產出：$slimExe" -ForegroundColor Gray
        Write-Host "      ✓ 檔案體積：$([math]::Round($size, 2)) MB (極致輕量)" -ForegroundColor Green
        
        # 複製一份到 publish 根目錄維持舊版捷徑相容
        Copy-Item -Path $slimExe -Destination (Join-Path $baseOutputDir 'SystemOptimizer.App.exe') -Force
    }
}

# 2. 獨立版 (零依賴免安裝 Standalone，內建 .NET 8 Runtime，即開即用)
if ($Target -in @('all', 'standalone')) {
    Write-Host "[2/2] 正在編譯發布【獨立完整版 (Standalone)】(內建 Runtime，零依賴即開即用)..." -ForegroundColor Green
    & $dotnet publish $appCsproj -c Release -r win-x64 --self-contained true -o $standaloneDir -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true
    
    $standaloneExe = Join-Path $standaloneDir 'SystemOptimizer.App.exe'
    if (Test-Path $standaloneExe) {
        $size = (Get-Item $standaloneExe).Length / 1MB
        Write-Host "      ✓ 獨立版產出：$standaloneExe" -ForegroundColor Gray
        Write-Host "      ✓ 檔案體積：$([math]::Round($size, 2)) MB (零環境依賴免安裝)" -ForegroundColor Green
    }
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "🎉 發布流程完成！" -ForegroundColor Cyan
Write-Host "   - 輕量版 (Slim)：$slimDir\SystemOptimizer.App.exe" -ForegroundColor White
Write-Host "   - 獨立版 (Standalone)：$standaloneDir\SystemOptimizer.App.exe" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan

if ($RunAfterBuild) {
    $targetExe = Join-Path $standaloneDir 'SystemOptimizer.App.exe'
    if (-not (Test-Path $targetExe)) {
        $targetExe = Join-Path $slimDir 'SystemOptimizer.App.exe'
    }
    Write-Host "正在啟動應用程式 ($targetExe)..." -ForegroundColor Yellow
    Start-Process $targetExe
}

