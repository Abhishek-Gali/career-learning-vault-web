# scripts\setup.ps1 — Windows Setup Script (Strictly self-contained in project root)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "Setting up CLF-C02 Researcher in: $ProjectRoot" -ForegroundColor Cyan

# Set local pip and playwright cache paths
$env:PIP_CACHE_DIR = Join-Path $ProjectRoot ".pip-cache"
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $ProjectRoot ".playwright"

# 1. Create local virtual environment
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating Python virtual environment in $VenvPath..." -ForegroundColor Yellow
    python -m venv $VenvPath
} else {
    Write-Host "Virtual environment already exists in $VenvPath." -ForegroundColor Green
}

# 2. Activate virtual environment
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip = Join-Path $VenvPath "Scripts\pip.exe"

# 3. Upgrade pip and install package
Write-Host "Installing dependencies into local virtual environment..." -ForegroundColor Yellow
& $VenvPip install --cache-dir $env:PIP_CACHE_DIR --upgrade pip
& $VenvPip install --cache-dir $env:PIP_CACHE_DIR -e "$ProjectRoot[dev]"

# 4. Download HTMX locally for offline use
$VendorDir = Join-Path $ProjectRoot "app\web\static\vendor"
if (-not (Test-Path $VendorDir)) {
    New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null
}
$HtmxFile = Join-Path $VendorDir "htmx.min.js"
if (-not (Test-Path $HtmxFile)) {
    Write-Host "Downloading HTMX to $HtmxFile..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "https://unpkg.com/htmx.org@2.0.11/dist/htmx.min.js" -OutFile $HtmxFile -TimeoutSec 15
        Write-Host "HTMX downloaded successfully." -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not download HTMX (offline). A minimal fallback will be generated." -ForegroundColor DarkYellow
    }
}

# 5. Ensure all data directories exist
$DataDirs = @(
    "data\db",
    "data\cache\pages",
    "data\cache\curriculum",
    "data\exports",
    "data\logs"
)
foreach ($d in $DataDirs) {
    $fullPath = Join-Path $ProjectRoot $d
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Force -Path $fullPath | Out-Null
    }
}

Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "To activate environment run: .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "To check system health run: clf doctor" -ForegroundColor Cyan
