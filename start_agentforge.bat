@echo off
echo ================================================
echo  AgentForge - Autonomous Multi-Agent Platform
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r agentforge_requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:: Copy .env if not exists
if not exist "agentforge\.env" (
    echo [2/3] Setting up environment file...
    copy "agentforge\.env.example" "agentforge\.env"
    echo.
    echo  IMPORTANT: Edit agentforge\.env and add your LLM_API_KEY
    echo  Press any key after setting your API key...
    pause
) else (
    echo [2/3] Environment file found.
)

:: Start API server in background
echo [3/3] Starting AgentForge API server...
start "AgentForge API" cmd /k "python -m uvicorn agentforge.api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for API to start
echo Waiting for API server to start...
timeout /t 5 /nobreak >nul

:: Start Streamlit dashboard
echo Starting AgentForge Dashboard...
echo.
echo  Dashboard: http://localhost:8501
echo  API Docs:  http://localhost:8000/docs
echo  API:       http://localhost:8000
echo.
streamlit run agentforge/frontend/app.py --server.port 8501 --server.address localhost

pause
