[CmdletBinding()]
param(
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
Write-Host "【SystemOptimizer.App】C# .NET 8 原生單檔編譯與發布系統" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

$appCsproj = Join-Path $projectDir 'src\SystemOptimizer.App\SystemOptimizer.App.csproj'
$outputDir = Join-Path $projectDir 'publish'

Write-Host "[1/2] 正在編譯發布單一獨立 Exe (Release x64)..." -ForegroundColor Green
& $dotnet publish $appCsproj -c Release -r win-x64 --self-contained false -o $outputDir -p:PublishSingleFile=true

$exePath = Join-Path $outputDir 'SystemOptimizer.App.exe'
if (Test-Path $exePath) {
    $fileSizeMb = (Get-Item $exePath).Length / 1MB
    Write-Host "[2/2] 發布成功！" -ForegroundColor Cyan
    Write-Host "      產出檔案：$exePath" -ForegroundColor Gray
    Write-Host "      檔案體積：$([math]::Round($fileSizeMb, 2)) MB (極致輕量)" -ForegroundColor Green
    
    if ($RunAfterBuild) {
        Write-Host "正在啟動應用程式..." -ForegroundColor Yellow
        Start-Process $exePath
    }
} else {
    throw "發布後未發現預期之 Exe 檔案"
}
