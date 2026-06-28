@echo off
cd "D:\Tools\Gaokao\result"

echo ========================================
echo   Gaokao Data Query Server
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel%==0 (
    python serve.py --port 8765
    pause
    exit
)

py --version >nul 2>&1
if %errorlevel%==0 (
    py serve.py --port 8765
    pause
    exit
)

if exist "python-embed\python.exe" (
    python-embed\python.exe serve.py --port 8765
    pause
    exit
)

echo Python not found.
echo Downloading portable Python...
powershell -Command "$u='https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip';$f=$env:TEMP+'\py.zip';(New-Object Net.WebClient).DownloadFile($u,$f)"
if exist "%TEMP%\py.zip" (
    if exist python-embed rmdir /s /q python-embed
    powershell -Command "Expand-Archive -Path ($env:TEMP+'\py.zip') -DestinationPath 'python-embed'"
    del "%TEMP%\py.zip"
    if exist python-embed\python.exe (
        python-embed\python.exe serve.py --port 8765
        pause
        exit
    )
)

echo Install Python manually: https://www.python.org/downloads/
pause
