@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Mentoring Report Generator
echo ========================================
echo.

:: Check for UV Package Manager
echo [1/4] Checking UV...
where uv >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] UV not found
    echo Please install UV first: https://docs.astral.sh/uv/
    pause
    exit /b 1
)
echo [OK] UV found
echo.

:: Check for FFmpeg (optional - just warn if missing)
echo [2/4] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [WARNING] FFmpeg not found - video transcription will be skipped
    echo To install: winget install Gyan.FFmpeg
) else (
    echo [OK] FFmpeg found
)
echo.

:: Check for Claude Code CLI
echo [3/4] Checking Claude Code...
where claude >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Claude Code not found
    echo Install: powershell -ExecutionPolicy ByPass -c "irm https://claude.ai/install.ps1 | iex"
    pause
    exit /b 1
)
echo [OK] Claude Code found
echo.

:: Check for .env file
echo [4/4] Checking configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from template...
        copy ".env.example" ".env" >nul
        echo [OK] Created .env
        echo.
        echo [IMPORTANT] Edit .env with your SharePoint credentials
        echo.
        notepad .env
        pause
    ) else (
        echo [ERROR] .env.example not found
        pause
        exit /b 1
    )
) else (
    echo [OK] Configuration found
)
echo.

:: Install Python dependencies and package
echo ========================================
echo Installing dependencies and package...
echo ========================================
echo.

uv sync
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to sync dependencies
    pause
    exit /b 1
)

uv pip install -e .
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to install package
    pause
    exit /b 1
)

echo [OK] Installation complete
echo.

:: Launch application
echo ========================================
echo Launching mentoring report generator...
echo ========================================
echo.

uv run python -m src.generate_mentoring_report_auto

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [ERROR] Application failed. Check app.log for details.
    pause
    exit /b !ERRORLEVEL!
)

echo.
echo [OK] Complete! Check working_dir for output.
echo.
pause
