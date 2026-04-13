@echo off
echo === yt-dlp Chrome Extension Setup (Windows) ===
echo.

REM Check/install uv
echo [1/4] Checking uv...
where uv >nul 2>&1
if errorlevel 1 (
    echo        Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
) else (
    echo        uv already installed.
)

REM Install dependencies via uv
echo [2/4] Installing yt-dlp...
uv sync

REM Install ffmpeg
echo [3/4] Checking ffmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    where choco >nul 2>&1
    if errorlevel 1 (
        echo WARNING: ffmpeg not found and Chocolatey is not installed.
        echo Install ffmpeg manually from https://ffmpeg.org/download.html
        echo Or install Chocolatey from https://chocolatey.org and run: choco install ffmpeg
    ) else (
        echo Installing ffmpeg via Chocolatey...
        choco install ffmpeg -y
    )
) else (
    echo        ffmpeg already installed.
)

REM Create download directory
echo [4/4] Creating download directory...
if not exist "%USERPROFILE%\Downloads\yt-dlp-audio" mkdir "%USERPROFILE%\Downloads\yt-dlp-audio"

echo.
echo === Setup complete! ===
echo.
echo Next steps:
echo   1. Open chrome://extensions in Chrome
echo   2. Enable 'Developer mode' (toggle in top right)
echo   3. Click 'Load unpacked' and select the extension\ folder
echo   4. Start the server: uv run python server.py
echo   5. Go to any YouTube video and click the MP3 button!
echo.
echo Downloads will be saved to: %USERPROFILE%\Downloads\yt-dlp-audio\
