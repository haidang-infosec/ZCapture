# =====================================================================
# ZCapture - Automated Build Script (PowerShell)
# Tự động dọn dẹp, kiểm tra cú pháp & đóng gói ra file ZCapture.exe Portable
# =====================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "                ZCAPTURE AUTOMATED BUILD SYSTEM                      " -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Don dep tien trinh cu, cache va cac thu muc build cu
Write-Host "[1/4] Dung tien trinh cu va don dep cache/build..." -ForegroundColor Green
Stop-Process -Name ZCapture -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

$dirsToClean = @("build", "dist")
foreach ($dir in $dirsToClean) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
        Write-Host "      - Da xoa thu muc: $dir" -ForegroundColor Gray
    }
}

Get-ChildItem -Path . -Recurse -Filter "__pycache__" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Recurse -Force $_.FullName -ErrorAction SilentlyContinue
}
Write-Host "      - Da don dep sach se tat ca __pycache__ folders." -ForegroundColor Gray
Write-Host ""

# Step 2: Kiem tra bien dich cu phap Python (Syntax Check)
Write-Host "[2/4] Kiem tra bien dich cu phap tat ca cac module Python..." -ForegroundColor Green
$pyFiles = @(
    "main.py",
    "core/config_store.py",
    "core/dpi_utils.py",
    "core/ocr_engine.py",
    "core/screen_grabber.py",
    "core/window_detector.py",
    "models/annotations.py",
    "models/watermark.py",
    "ui/about_dialog.py",
    "ui/ocr_dialog.py",
    "ui/overlay_canvas.py",
    "ui/pin_manager.py",
    "ui/pin_window.py",
    "ui/settings_window.py",
    "ui/toolbars.py",
    "ui/widgets.py",
    "ui/overlay/__init__.py",
    "ui/overlay/ocr_worker.py",
    "ui/overlay/sub_toolbars.py",
    "ui/overlay/rendering_helper.py",
    "ui/overlay/canvas_widget.py"
)

$pythonExe = "python"
$candidatePythons = @(
    "python",
    "py",
    "python3",
    "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
)
foreach ($cand in $candidatePythons) {
    if (Test-Path $cand) {
        $pythonExe = $cand
        break
    }
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd -and ($cmd.Source -notlike "*WindowsApps*")) {
        $pythonExe = $cand
        break
    }
}

$compileCmd = "$pythonExe -m py_compile " + ($pyFiles -join " ")
Invoke-Expression $compileCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "[LOI]: Kiem tra cu phap that bai! Vui long sua loi truoc khi build." -ForegroundColor Red
    exit 1
}
Write-Host "      - Tat ca $($pyFiles.Count) module Python hop le 100% (0 loi cu phap)." -ForegroundColor Gray
Write-Host ""

# Step 3: Thuc thi PyInstaller dong goi scripts/ZCapture.spec
Write-Host "[3/4] Tien hanh dong goi ung dung bang PyInstaller (scripts/ZCapture.spec)..." -ForegroundColor Green
$pyinstallerCmd = "& `"$pythonExe`" -m PyInstaller scripts/ZCapture.spec --noconfirm"
Invoke-Expression $pyinstallerCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "[LOI]: Tien trinh PyInstaller that bai!" -ForegroundColor Red
    exit 1
}

# Step 4: Kiem tra ket qua xuat file dist/ZCapture.exe
Write-Host ""
Write-Host "[4/4] Kiem tra san pham dau ra..." -ForegroundColor Green
$exePath = "dist/ZCapture.exe"

if (Test-Path $exePath) {
    $exeItem = Get-Item $exePath
    $sizeMB = [math]::Round($exeItem.Length / 1MB, 2)
    Write-Host ""
    Write-Host "=====================================================================" -ForegroundColor Green
    Write-Host "                DONG GOI HOAN TAT THANH CONG!                       " -ForegroundColor Yellow
    Write-Host "=====================================================================" -ForegroundColor Green
    Write-Host "  File dau ra : $($exeItem.FullName)" -ForegroundColor White
    Write-Host "  Dung luong  : $sizeMB MB" -ForegroundColor White
    Write-Host "  Loai file   : Portable Standalone Executable (Zero-Dependency)" -ForegroundColor White
    Write-Host "=====================================================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[LOI]: Khong tim thay file dist/ZCapture.exe sau khi dong goi!" -ForegroundColor Red
    exit 1
}
