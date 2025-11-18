@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Mentoring Report Generator
echo ========================================
echo.

:: Check for UV Package Manager
echo [1/4] Checking UV...
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo UV not found. Installing...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install UV
        echo Please install manually: https://docs.astral.sh/uv/
        pause
        exit /b 1
    )
    echo UV installed successfully
    echo Please restart this script
    pause
    exit /b 0
)
echo [OK] UV found
echo.

:: Check for FFmpeg
echo [2/5] Checking FFmpeg for video processing...
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo FFmpeg not found. Attempting automatic installation...

    REM Try winget first (built into Windows 10/11)
    echo Trying Windows Package Manager (winget)...
    winget install --id=Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] FFmpeg installed via winget
        goto ffmpeg_success
    )

    REM Try chocolatey
    echo winget failed. Trying Chocolatey...
    choco install ffmpeg -y >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] FFmpeg installed via Chocolatey
        goto ffmpeg_success
    )

    REM Try scoop
    echo Chocolatey failed. Trying Scoop...
    scoop install ffmpeg >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] FFmpeg installed via Scoop
        goto ffmpeg_success
    )

    REM All automatic methods failed
    echo.
    echo [WARNING] Could not automatically install FFmpeg
    echo FFmpeg is required for video transcription support
    echo.
    echo To install FFmpeg manually:
    echo   1. Download from: https://ffmpeg.org/download.html
    echo   2. Install via winget: winget install Gyan.FFmpeg
    echo   3. Install via Chocolatey: choco install ffmpeg
    echo   4. Install via Scoop: scoop install ffmpeg
    echo.
    echo You can continue without FFmpeg, but video files will be skipped.
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i "!CONTINUE!" NEQ "y" (
        echo Installation cancelled
        pause
        exit /b 1
    )
    goto ffmpeg_done

    :ffmpeg_success
    echo FFmpeg installed! PATH will be refreshed automatically...

    :ffmpeg_done
) else (
    echo [OK] FFmpeg found
)
echo.

:: Check for Claude Code CLI
echo [3/5] Checking Claude Code...
where claude >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Claude Code not found
    echo.
    echo Install Claude Code:
    echo   powershell -ExecutionPolicy ByPass -c "irm https://claude.ai/install.ps1 | iex"
    echo.
    echo After installation, restart terminal and run this script again
    pause
    exit /b 1
)
echo [OK] Claude Code found
echo.

:: Check for document-skills plugin
echo [4/5] Checking document-skills plugin...
claude skill list 2>nul | findstr /C:"document-skills" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Document-skills plugin not found
    echo.
    echo In Claude Code, run these commands:
    echo   /plugin marketplace add anthropics/skills
    echo   /plugin install document-skills@anthropic-agent-skills
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i "!CONTINUE!" NEQ "y" (
        exit /b 1
    )
) else (
    echo [OK] Document-skills found
)
echo.

:: Check for .env file
echo [5/5] Checking configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from template...
        copy ".env.example" ".env" >nul
        echo [OK] Created .env
        echo.
        echo [IMPORTANT] Edit .env with your SharePoint credentials
        echo See README_AFM.md for details
        echo.
        notepad .env
        echo.
        set /p CONTINUE="Press Enter when ready..."
    ) else (
        echo [ERROR] .env.example not found
        pause
        exit /b 1
    )
) else (
    findstr /C:"your-tenant-id-here" ".env" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [WARNING] .env has placeholder values
        echo Edit with real credentials before using AFM mode
        echo.
    ) else (
        echo [OK] Configuration found
    )
)
echo.

:: Install Python dependencies
echo Installing dependencies...
uv sync
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

:: Launch application
echo ========================================
echo Launching application...
echo ========================================
echo.

uv run src/generate_mentoring_report_auto.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application failed. Check app.log for details.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] Complete! Check working_dir for output.
echo.
pause
