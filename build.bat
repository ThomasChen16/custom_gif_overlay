@echo off
echo ============================================
echo   GIF Overlay - Build EXE
echo ============================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Make sure Python is installed and added to PATH.
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install pillow pyinstaller --quiet

:: Find pyinstaller using Python itself (works regardless of PATH)
echo [2/3] Building gif_overlay.exe (this takes ~30 seconds)...
python -m PyInstaller --onefile --windowed --name gif_overlay gif_overlay.py

:: Check success
if exist "dist\gif_overlay.exe" (
    echo.
    echo [3/3] SUCCESS!
    echo.
    echo Your exe is ready at:
    echo   %cd%\dist\gif_overlay.exe
    echo.
    echo You can move gif_overlay.exe anywhere and double-click to run it.
    echo No terminal, no Python needed.
) else (
    echo.
    echo BUILD FAILED. Check the output above for errors.
)

echo.
pause