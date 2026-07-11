@echo off
:: ============================================================
::  Last Hammer EMS — Desktop Shortcut Creator
::  Run this once to create a desktop icon
:: ============================================================

echo.
echo  Creating Last Hammer desktop shortcut...
echo.

:: Get the directory where this script lives
set "APP_DIR=%~dp0"
:: Remove trailing backslash
if "%APP_DIR:~-1%"=="\" set "APP_DIR=%APP_DIR:~0,-1%"

:: Output shortcut path on Desktop
set "SHORTCUT=%USERPROFILE%\Desktop\Last Hammer.lnk"

:: Use PowerShell to create the shortcut
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%SHORTCUT%'); ^
   $s.TargetPath = 'pythonw.exe'; ^
   $s.Arguments = '\"%APP_DIR%\main.py\"'; ^
   $s.WorkingDirectory = '%APP_DIR%'; ^
   $s.IconLocation = '%APP_DIR%\assets\logo.ico'; ^
   $s.Description = 'Last Hammer Expenditure Management System'; ^
   $s.Save()"

if exist "%SHORTCUT%" (
    echo  [OK]  Shortcut created on Desktop: Last Hammer.lnk
) else (
    echo  [!!]  Could not create shortcut. Trying fallback...
    :: Fallback — create a simple .bat launcher on desktop instead
    set "LAUNCHER=%USERPROFILE%\Desktop\Last Hammer.bat"
    echo @echo off > "%LAUNCHER%"
    echo cd /d "%APP_DIR%" >> "%LAUNCHER%"
    echo start pythonw "%APP_DIR%\main.py" >> "%LAUNCHER%"
    echo  [OK]  Created launcher on Desktop: Last Hammer.bat
)

echo.
echo  Done! Look for "Last Hammer" on your Desktop.
echo.
pause