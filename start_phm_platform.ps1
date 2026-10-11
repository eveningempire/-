param([switch]$CheckOnly, [switch]$NoBrowser, [int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location -LiteralPath $Root
$env:USE_SQLITE = 'true'
$env:DJANGO_DEBUG = 'True'
$env:PIP_NO_INDEX = '1'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$Py = Join-Path $Root '.venv\Scripts\python.exe'

try {
    Write-Host 'PHM - 重复使用运载器健康管理原型系统' -ForegroundColor Cyan
    if (-not (Test-Path -LiteralPath (Join-Path $Root 'manage.py'))) {
        throw '未找到 manage.py，请将补丁覆盖到原项目根目录。'
    }
    # Deployment consumes prebuilt assets and never runs npm.
    $dist = Join-Path $Root 'frontend\dist'
    $index = Join-Path $dist 'index.html'
    if (-not (Test-Path -LiteralPath $index -PathType Leaf)) {
        throw '缺少 frontend\dist\index.html，请覆盖前端成品补丁或完整解压离线包。'
    }
    $html = [IO.File]::ReadAllText($index, [Text.Encoding]::UTF8)
    $assets = [regex]::Matches($html, '(?:src|href)="/static/([^"?]+\.(?:js|css))')
    if ($assets.Count -lt 2) { throw '前端入口未引用完整的 JS/CSS 成品，请覆盖前端补丁。' }
    foreach ($asset in $assets) {
        $relative = $asset.Groups[1].Value.Replace('/', '\')
        if (-not (Test-Path -LiteralPath (Join-Path $dist $relative) -PathType Leaf)) {
            throw "缺少前端成品 $relative，请覆盖前端补丁；无需安装 Node.js 或 Vite。"
        }
    }
    $ready = $false
    if (Test-Path -LiteralPath $Py -PathType Leaf) {
        try {
            & $Py (Join-Path $Root 'verify_phm_runtime.py') *> $null
            $ready = ($LASTEXITCODE -eq 0)
        } catch { $ready = $false }
    }
    if (-not $ready) {
        Write-Host '正在从包内离线依赖初始化 Python 环境，首次运行请耐心等待。' -ForegroundColor Yellow
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'setup_migration.ps1') -SkipFrontend
        if ($LASTEXITCODE -ne 0) { throw '离线环境初始化失败，请查看上方错误。' }
        & $Py (Join-Path $Root 'verify_phm_runtime.py')
        if ($LASTEXITCODE -ne 0) { throw 'Python 运行环境检查未通过。' }
    }
    & $Py manage.py check
    if ($LASTEXITCODE -ne 0) { throw 'Django 系统检查失败。' }
    & $Py manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw '数据库迁移失败。' }
    & $Py (Join-Path $Root 'verify_phm_delivery.py')
    if ($LASTEXITCODE -ne 0) { throw '项目数据或算法模型不完整，请完整解压新版离线包。' }
    if ($CheckOnly) {
        Write-Host 'PHM 启动检查通过。' -ForegroundColor Green
        exit 0
    }
    $url = "http://127.0.0.1:$Port/"
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    foreach ($processId in ($listeners | Select-Object -ExpandProperty OwningProcess -Unique)) {
        $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
        throw "$Port 端口已被进程 $processId 占用，请先停止该服务，或使用 -Port 指定其他端口。"
    }
    $logs = Join-Path $Root 'logs'
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    $server = Start-Process -FilePath $Py -ArgumentList @('manage.py', 'runserver', "127.0.0.1:$Port", '--noreload') -WorkingDirectory $Root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'server.out.log') -RedirectStandardError (Join-Path $logs 'server.err.log')
    $connected = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        $server.Refresh()
        if ($server.HasExited) { break }
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $connected = $true; break }
        } catch { }
    }
    if (-not $connected) {
        if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
        Get-Content -LiteralPath (Join-Path $logs 'server.err.log') -Tail 20 -ErrorAction SilentlyContinue | Write-Host
        throw '服务未成功启动，请查看 logs\server.err.log。'
    }
    Write-Host "PHM 已启动：$url" -ForegroundColor Green
    @{ process_id = $server.Id; port = $Port; executable = $Py } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logs 'server-process.json') -Encoding UTF8
    if (-not $NoBrowser) {
        # Browser association failures must not turn a healthy service into a startup failure.
        try {
            Start-Process -FilePath $url -ErrorAction Stop
        } catch {
            Write-Host '无法自动打开浏览器，PHM 服务仍正常运行。' -ForegroundColor Yellow
            Write-Host "请在虚拟机内手动打开浏览器，访问 $url" -ForegroundColor Yellow
        }
    }
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
