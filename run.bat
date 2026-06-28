@echo off
REM One command on Windows: venv + deps + start. Mirror of run.sh (#20).
setlocal
cd /d "%~dp0"

if "%PORT%"=="" set PORT=8000
if "%HOST%"=="" set HOST=127.0.0.1

where python >nul 2>&1 || (echo [X] Python not found. Install Python 3.10+ from python.org & exit /b 1)

if not exist .venv (
  echo [*] Creating .venv
  python -m venv .venv || (echo [X] venv creation failed & exit /b 1)
)
call .venv\Scripts\activate.bat

echo [*] Installing dependencies
pip install -q -r requirements.txt || (echo [X] pip install failed & exit /b 1)

REM Frontend build (#44) — falls back to legacy web/ if Node missing or build fails
where npm >nul 2>&1 && if exist frontend (
  if not exist web-dist (
    echo [*] Building frontend (React)
    if not exist frontend\node_modules ( pushd frontend & npm install & popd )
    pushd frontend & npm run build & popd
  )
)

if not exist .env (
  echo [!] .env missing - copying .env.example. Edit it to add a key/model.
  copy /y .env.example .env >nul
)

echo [*] Starting Emotionist.ai - http://%HOST%:%PORT%
uvicorn server:app --host %HOST% --port %PORT%
endlocal
