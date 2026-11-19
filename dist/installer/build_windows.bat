@echo off
REM RADXOID Installer - Build for Windows
REM This script creates a standalone executable for Windows

setlocal

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install PyInstaller --user
)

REM Create output directory
if not exist "build" mkdir build
if not exist "build\windows" mkdir build\windows

REM Build the installer
echo Building RADXOID Installer for Windows...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name RADXOID-Installer ^
    --icon=radxoid.ico ^
    --add-data "../README.md;." ^
    --add-data "../LICENSE;." ^
    --distpath build\windows ^
    --workpath build\windows\temp ^
    radxoid_installer.py

if errorlevel 1 (
    echo Error: Build failed
    pause
    exit /b 1
)

echo.
echo ✅ Build successful!
echo The installer is at: build\windows\RADXOID-Installer.exe

REM Copy additional files
copy radxoid_installer.py build\windows\ >nul
copy ../README.md build\windows\ >nul
copy ../LICENSE build\windows\ >nul

echo.
echo To create the distribution package:
echo 1. Run: split_volumes.py /path/to/artifacts dist/volumes
echo 2. Copy all files to: build\windows\volumes
echo 3. Zip the build\windows directory

pause
