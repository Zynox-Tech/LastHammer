# Last Hammer — Desktop Shortcut Creator
# Run from PowerShell inside the LastHammer folder:
#   powershell -ExecutionPolicy Bypass -File make_shortcut.ps1

$AppDir     = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonW    = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)?.Source
if (-not $PythonW) {
    # fallback: find pythonw next to python
    $Python  = (Get-Command python.exe -ErrorAction SilentlyContinue)?.Source
    if ($Python) {
        $PythonW = Join-Path (Split-Path $Python) "pythonw.exe"
    }
}
if (-not $PythonW -or -not (Test-Path $PythonW)) {
    Write-Host ""
    Write-Host "  [!!] Could not find pythonw.exe." -ForegroundColor Red
    Write-Host "       Make sure Python is installed and on your PATH." -ForegroundColor Red
    Write-Host ""
    pause
    exit
}

$MainScript = Join-Path $AppDir "main.py"
$IconPath   = Join-Path $AppDir "assets\logo.ico"
$Desktop    = [Environment]::GetFolderPath("Desktop")
$Shortcut   = Join-Path $Desktop "Last Hammer.lnk"

$WShell = New-Object -ComObject WScript.Shell
$Link   = $WShell.CreateShortcut($Shortcut)
$Link.TargetPath       = $PythonW
$Link.Arguments        = "`"$MainScript`""
$Link.WorkingDirectory = $AppDir
$Link.Description      = "Last Hammer Expenditure Management System"
if (Test-Path $IconPath) {
    $Link.IconLocation = $IconPath
}
$Link.Save()

Write-Host ""
if (Test-Path $Shortcut) {
    Write-Host "  [OK]  Desktop shortcut created!" -ForegroundColor Green
    Write-Host "        Double-click 'Last Hammer' on your Desktop to launch." -ForegroundColor Green
} else {
    Write-Host "  [!!]  Could not create shortcut." -ForegroundColor Red
}
Write-Host ""
Read-Host "Press Enter to close"