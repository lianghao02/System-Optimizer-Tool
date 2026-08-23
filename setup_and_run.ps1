[CmdletBinding()]
param(
    [string]$TargetProject = '',
    [switch]$NoLaunch,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$projectDir = $PSScriptRoot
$projectName = Split-Path -Leaf $projectDir
$embedDir = Join-Path $projectDir 'python_embed'
$embedPython = Join-Path $embedDir 'python.exe'

# 判定進入點檔案
$entryPoint = 'main.py'
if (Test-Path -LiteralPath (Join-Path $projectDir 'main.py')) {
    $entryPoint = 'main.py'
} elseif (Test-Path -LiteralPath (Join-Path $projectDir 'ui.py')) {
    $entryPoint = 'ui.py'
} elseif (Test-Path -LiteralPath (Join-Path $projectDir 'app.py')) {
    $entryPoint = 'app.py'
}

# 判定需求檔
$reqFile = $null
if (Test-Path -LiteralPath (Join-Path $projectDir 'requirements.txt')) {
    $reqFile = Join-Path $projectDir 'requirements.txt'
} elseif (Test-Path -LiteralPath (Join-Path $projectDir 'requirements-release.txt')) {
    $reqFile = Join-Path $projectDir 'requirements-release.txt'
} elseif (Test-Path -LiteralPath (Join-Path $projectDir 'portable-requirements.txt')) {
    $reqFile = Join-Path $projectDir 'portable-requirements.txt'
}

Write-Host '=================================================================' -ForegroundColor Cyan
Write-Host "🚀 【智慧自癒啟動系統】專案：$projectName" -ForegroundColor Yellow
Write-Host '=================================================================' -ForegroundColor Cyan

# ----------------------------------------------------------------------
# 階段 ①：檢查是否已具備現成的 Python 可攜環境 (場景 1：隨身碟 / 已就緒)
# ----------------------------------------------------------------------
$isEnvironmentReady = $false

if ($Force -and (Test-Path -LiteralPath $embedDir)) {
    Write-Host "[強制重建] 偵測到 -Force 參數，正在重置環境..." -ForegroundColor Magenta
    Remove-Item -LiteralPath $embedDir -Recurse -Force
}
if (Test-Path -LiteralPath $embedPython) {
    # 測試執行並驗證 (包含 Tkinter 與 CustomTkinter 支援檢測)
    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $testRun = & $embedPython -c "import sys, tkinter, customtkinter; print('READY')" 2>$null
        if ($LASTEXITCODE -eq 0 -and $testRun -match 'READY') {
            $isEnvironmentReady = $true
        }
    } catch {
        $isEnvironmentReady = $false
    } finally {
        $ErrorActionPreference = $oldEap
    }
}

if (-not $isEnvironmentReady) {
    Write-Host '🔍 偵測到本機尚未就緒 Python 可攜環境或 Tkinter 核心，正在啟動自動自癒佈置...' -ForegroundColor Yellow
    Write-Host ''

    # 搜尋本機候選 ZIP (優先級：專案根目錄 -> 00_home\downloads -> D:\Caches -> 使用者 Downloads)
    $searchPaths = @(
        $projectDir,
        (Join-Path (Split-Path -Parent $projectDir) '00_home\downloads'),
        'D:\Caches',
        (Join-Path $env:USERPROFILE 'Downloads')
    )

    $zipPath = $null
    foreach ($sp in $searchPaths) {
        if ($sp -and (Test-Path -LiteralPath $sp)) {
            $found = Get-ChildItem -LiteralPath $sp -Filter '*embed*amd64*.zip' -File -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending | Select-Object -First 1
            if ($found) {
                $zipPath = $found.FullName
                break
            }
        }
    }

    if (-not $zipPath) {
        $zipPath = Join-Path $projectDir 'python-3.13.5-embed-amd64.zip'
    }

    # ------------------------------------------------------------------
    # 階段 ②：取得 ZIP 壓縮包 (場景 3: 本機優先 / 場景 2: 線上下載)
    # ------------------------------------------------------------------
    if (-not (Test-Path -LiteralPath $zipPath)) {
        $downloadUrl = 'https://www.python.org/ftp/python/3.13.5/python-3.13.5-embed-amd64.zip'
        Write-Host '🌐 [1/4] 本機未發現 ZIP，正在從 Python 官方下載可攜核心 (11.9 MB)...' -ForegroundColor Green
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
        Write-Host "   ✅ 下載完成：$zipPath" -ForegroundColor Gray
    } else {
        Write-Host "⚡ [1/4] 發現本機 Python ZIP 母檔：$zipPath（略過下載）" -ForegroundColor Green
    }

    # ------------------------------------------------------------------
    # 階段 ③：解壓縮至 python_embed
    # ------------------------------------------------------------------
    Write-Host '📦 [2/4] 正在解壓縮可攜核心至 python_embed/ 資料夾...' -ForegroundColor Green
    if (Test-Path -LiteralPath $embedDir) {
        Remove-Item -LiteralPath $embedDir -Recurse -Force
    }
    Expand-Archive -LiteralPath $zipPath -DestinationPath $embedDir -Force

    # ------------------------------------------------------------------
    # 階段 ④：解除 ._pth 限制 (嚴格使用純 ASCII 無 BOM 寫入，防 encodings 模組載入崩潰)
    # ------------------------------------------------------------------
    Write-Host '⚙️  [3/4] 正在解除環境隔離限制並配置 pip 套件管理器...' -ForegroundColor Green
    $pthFile = Get-ChildItem -LiteralPath $embedDir -Filter '*._pth' -File | Select-Object -First 1
    if ($pthFile) {
        $zipName = [IO.Path]::GetFileNameWithoutExtension($pthFile.Name) + '.zip'
        $pthLines = @(
            $zipName,
            '.',
            '..',
            'DLLs',
            'Lib',
            'Lib\site-packages',
            'import site'
        )
        $asciiBytes = [System.Text.Encoding]::ASCII.GetBytes(($pthLines -join [Environment]::NewLine) + [Environment]::NewLine)
        [System.IO.File]::WriteAllBytes($pthFile.FullName, $asciiBytes)
    }

    # 針對 Tkinter / CustomTkinter 依賴補齊 Tcl/Tk 與 _tkinter 核心
    $candidatePyHomes = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313'),
        'C:\Python313',
        'D:\Python313'
    )
    $sysPy = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($sysPy -and $sysPy.Source) {
        $candidatePyHomes += (Split-Path -Parent $sysPy.Source)
    }

    foreach ($pyHome in $candidatePyHomes) {
        if ($pyHome -and (Test-Path -LiteralPath (Join-Path $pyHome 'DLLs\_tkinter.pyd'))) {
            Write-Host "🎨 正在自本機環境 ($pyHome) 自動補齊 Tkinter / GUI 渲染模組..." -ForegroundColor Green
            $dstDlls = Join-Path $embedDir 'DLLs'
            New-Item -ItemType Directory -Force -Path $dstDlls | Out-Null
            foreach ($dllName in @('_tkinter.pyd', 'tcl86t.dll', 'tk86t.dll', 'zlib1.dll')) {
                $src = Join-Path $pyHome "DLLs\$dllName"
                if (Test-Path -LiteralPath $src) {
                    Copy-Item -LiteralPath $src -Destination $dstDlls -Force
                    Copy-Item -LiteralPath $src -Destination $embedDir -Force
                }
            }

            $srcTcl = Join-Path $pyHome 'tcl'
            $dstTcl = Join-Path $embedDir 'tcl'
            if (Test-Path -LiteralPath $srcTcl) {
                if (Test-Path -LiteralPath $dstTcl) { Remove-Item -LiteralPath $dstTcl -Recurse -Force }
                Copy-Item -LiteralPath $srcTcl -Destination $dstTcl -Recurse -Force
            }

            $srcLibTk = Join-Path $pyHome 'Lib\tkinter'
            $dstLibTk = Join-Path $embedDir 'Lib\tkinter'
            if (Test-Path -LiteralPath $srcLibTk) {
                $dstLib = Join-Path $embedDir 'Lib'
                New-Item -ItemType Directory -Force -Path $dstLib | Out-Null
                if (Test-Path -LiteralPath $dstLibTk) { Remove-Item -LiteralPath $dstLibTk -Recurse -Force }
                Copy-Item -LiteralPath $srcLibTk -Destination $dstLibTk -Recurse -Force
            }
            break
        }
    }

    # 配置 get-pip.py
    $getPipPath = Join-Path $embedDir 'get-pip.py'
    $cachedGetPip = Join-Path (Split-Path -Parent $projectDir) '00_home\downloads\get-pip.py'
    if (Test-Path -LiteralPath $cachedGetPip) {
        Copy-Item -LiteralPath $cachedGetPip -Destination $getPipPath -Force
    } else {
        $getPipUrl = 'https://bootstrap.pypa.io/get-pip.py'
        try {
            Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath -UseBasicParsing
        } catch {
            Write-Host '   ⚠️  無法從網路下載 get-pip.py，將嘗試使用已內建套件機制' -ForegroundColor Yellow
        }
    }

    if (Test-Path -LiteralPath $getPipPath) {
        $oldEap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $null = & $embedPython $getPipPath --no-warn-script-location 2>$null
        } finally {
            $ErrorActionPreference = $oldEap
        }
    }

    # ------------------------------------------------------------------
    # 階段 ⑤：安裝相依套件 (requirements.txt)
    # ------------------------------------------------------------------
    if ($reqFile -and (Test-Path -LiteralPath $reqFile)) {
        Write-Host "📚 [4/4] 正在自動安裝專案相依套件 ($([IO.Path]::GetFileName($reqFile)))..." -ForegroundColor Green
        $oldEap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $embedPython -m pip install --no-warn-script-location -r $reqFile
        } finally {
            $ErrorActionPreference = $oldEap
        }
    } elseif ($projectName -eq '06_System-Optimizer-Tool') {
        Write-Host '📚 [4/4] 正在為系統優化工具安裝必要套件 (customtkinter)...' -ForegroundColor Green
        $oldEap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $embedPython -m pip install --no-warn-script-location customtkinter
        } finally {
            $ErrorActionPreference = $oldEap
        }
    }

    Write-Host ''
    Write-Host '🎉 【自癒成功】專案環境已 100% 佈置完成！' -ForegroundColor Cyan
    Write-Host '=================================================================' -ForegroundColor Cyan
}

if ($NoLaunch) {
    Write-Host '✨ 模式為僅建置環境，已順利完成。' -ForegroundColor Green
    return
}

# ----------------------------------------------------------------------
# 階段 ⑥：啟動主程式
# ----------------------------------------------------------------------
$mainFile = Join-Path $projectDir $entryPoint
if (-not (Test-Path -LiteralPath $mainFile)) {
    throw "找不到專案啟動進入點：$mainFile"
}

Write-Host "🚀 正在啟動 $projectName ($entryPoint)..." -ForegroundColor Green
Write-Host ''

# 依專案類型選擇視窗啟動或終端啟動
$pythonwExe = Join-Path $embedDir 'pythonw.exe'
if ($projectName -in @('07_auto-learning-bot', '10_Smart-Photo-Organizer') -and (Test-Path -LiteralPath $pythonwExe)) {
    Start-Process -FilePath $pythonwExe -ArgumentList $mainFile -WorkingDirectory $projectDir
} else {
    & $embedPython $mainFile
}
