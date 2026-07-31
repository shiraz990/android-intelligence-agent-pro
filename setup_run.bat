@echo off
setlocal enabledelayedexpansion
color 0A

echo ============================================================
echo   🤖 CodePulse AI - Setup & Run Script
echo ============================================================
echo.

:: ============ STEP 1: FIND PYTHON ============
echo [1/6] Locating Python...
set PYTHON_FOUND=0

:: Try common locations
if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_PATH=C:\Program Files\Python311\python.exe
    set PYTHON_DIR=C:\Program Files\Python311\
    set PYTHON_FOUND=1
)
if exist "C:\Program Files\Python312\python.exe" (
    set PYTHON_PATH=C:\Program Files\Python312\python.exe
    set PYTHON_DIR=C:\Program Files\Python312\
    set PYTHON_FOUND=1
)
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe
    set PYTHON_DIR=%USERPROFILE%\AppData\Local\Programs\Python\Python311\
    set PYTHON_FOUND=1
)
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe" (
    set PYTHON_PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe
    set PYTHON_DIR=%USERPROFILE%\AppData\Local\Programs\Python\Python312\
    set PYTHON_FOUND=1
)

:: Try using 'where' command
if %PYTHON_FOUND%==0 (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        set PYTHON_PATH=%%i
        set PYTHON_DIR=%%~dpi
        set PYTHON_FOUND=1
    )
)

if %PYTHON_FOUND%==0 (
    echo ❌ Python not found!
    echo.
    echo Please install Python 3.11+ from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found: %PYTHON_PATH%
echo.

:: ============ STEP 2: SETUP SCRIPTS PATH ============
set SCRIPTS_DIR=%PYTHON_DIR%Scripts\
echo [2/6] Adding Python Scripts to PATH...
set PATH=%PATH%;%SCRIPTS_DIR%

:: ============ STEP 3: INSTALL DEPENDENCIES ============
echo [3/6] Installing Python packages...
echo This may take 1-2 minutes...

%PYTHON_PATH% -m pip install --upgrade pip >nul 2>&1
%PYTHON_PATH% -m pip install streamlit plotly pandas requests

if %errorlevel% neq 0 (
    echo ❌ Failed to install packages!
    echo.
    echo Try manually:
    echo %PYTHON_PATH% -m pip install streamlit plotly pandas requests
    pause
    exit /b 1
)

echo ✅ Packages installed!
echo.

:: ============ STEP 4: CHECK OLLAMA ============
echo [4/6] Checking Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Ollama not found!
    echo.
    echo Download and install from:
    echo https://ollama.com/download/windows
    echo.
    echo After installing, press any key to continue...
    pause >nul
)

:: ============ STEP 5: PULL AI MODELS (First Time Only) ============
echo [5/6] Checking AI models...
ollama list | findstr llama3.2 >nul
if %errorlevel% neq 0 (
    echo Downloading AI models (first time setup)...
    echo This will take 5-10 minutes...
    echo.
    ollama pull llama3.2:3b
    ollama pull qwen2.5-coder:1.5b
    ollama pull gemma2:2b
) else (
    echo ✅ AI models already downloaded!
)
echo.

:: ============ STEP 6: START OLLAMA ============
echo [6/6] Starting Ollama...
start /B ollama serve
timeout /t 3 /nobreak >nul

:: ============ LAUNCH APP ============
echo.
echo ============================================================
echo   ✅ Setup Complete! Launching CodePulse AI...
echo ============================================================
echo.
echo 📱 Access the app at: http://localhost:8501
echo 🔄 Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

%PYTHON_PATH% -m streamlit run app_with_custom_logo.py --server.port=8501

pause