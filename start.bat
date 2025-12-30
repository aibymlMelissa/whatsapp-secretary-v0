@echo off
REM WhatsApp Secretary - Windows Startup Script

setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    WhatsApp Secretary                        ║
echo ║                   Windows Startup Script                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not installed or not in PATH
    pause
    exit /b 1
)

echo [INFO] Prerequisites check passed

REM Check mode parameter
set MODE=%1
if "%MODE%"=="" set MODE=dev

if "%MODE%"=="docker" (
    echo [INFO] Starting in Docker mode...

    REM Check if Docker is installed
    docker --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker is not installed or not in PATH
        echo Please install Docker Desktop from https://docker.com
        pause
        exit /b 1
    )

    REM Check if docker-compose is installed
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] docker-compose is not installed or not in PATH
        pause
        exit /b 1
    )

    echo [INFO] Stopping existing containers...
    docker-compose down 2>nul

    echo [INFO] Building and starting Docker containers...
    docker-compose up --build -d

    echo [INFO] Waiting for services to be ready...
    timeout /t 10 /nobreak >nul

    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║                   🐳 DOCKER CONTAINERS READY              ║
    echo ║                                                            ║
    echo ║  🌐 Frontend:   http://localhost:3000                     ║
    echo ║  📡 Backend:    http://localhost:8001                     ║
    echo ║  📚 API Docs:   http://localhost:8001/docs                ║
    echo ║                                                            ║
    echo ║  💡 To connect WhatsApp:                                   ║
    echo ║     1. Open http://localhost:3000                         ║
    echo ║     2. Click 'Connect' in WhatsApp status panel           ║
    echo ║     3. Scan QR code with your WhatsApp app                ║
    echo ║                                                            ║
    echo ║  🛑 To stop: docker-compose down                          ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.

    echo [INFO] Press any key to stop containers and exit...
    pause >nul

    echo [INFO] Stopping containers...
    docker-compose down

) else if "%MODE%"=="dev" (
    echo [INFO] Starting in Development mode...

    REM Check if .env file exists
    if not exist ".env" (
        echo [WARNING] .env file not found
        if exist ".env.example" (
            echo [INFO] Creating .env from template...
            copy ".env.example" ".env" >nul
            echo [WARNING] Please edit .env file with your API keys
            echo Press any key to continue after editing .env...
            pause >nul
        ) else (
            echo [ERROR] .env file is required
            pause
            exit /b 1
        )
    )

    echo [INFO] Setting up backend...
    cd backend

    REM Create virtual environment if it doesn't exist
    if not exist "venv" (
        echo [INFO] Creating Python virtual environment...
        python -m venv venv
    )

    REM Activate virtual environment
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat

    REM Install dependencies
    echo [INFO] Installing backend dependencies...
    pip install -r requirements.txt >nul 2>&1

    REM Start backend
    echo [INFO] Starting backend server...
    start "WhatsApp Secretary Backend" cmd /k "venv\Scripts\activate.bat && python app.py"

    cd ..

    REM Wait for backend to start
    echo [INFO] Waiting for backend to start...
    timeout /t 5 /nobreak >nul

    echo [INFO] Setting up frontend...
    cd frontend

    REM Install dependencies if needed
    if not exist "node_modules" (
        echo [INFO] Installing frontend dependencies...
        npm install >nul 2>&1
    )

    REM Start frontend
    echo [INFO] Starting frontend development server...
    start "WhatsApp Secretary Frontend" cmd /k "npm run dev"

    cd ..

    REM Wait for frontend to start
    timeout /t 3 /nobreak >nul

    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║                   ✅ DEVELOPMENT SERVERS READY            ║
    echo ║                                                            ║
    echo ║  🌐 Frontend:   http://localhost:3000                     ║
    echo ║  📡 Backend:    http://localhost:8001                     ║
    echo ║  📚 API Docs:   http://localhost:8001/docs                ║
    echo ║                                                            ║
    echo ║  💡 To connect WhatsApp:                                   ║
    echo ║     1. Open http://localhost:3000                         ║
    echo ║     2. Click 'Connect' in WhatsApp status panel           ║
    echo ║     3. Scan QR code with your WhatsApp app                ║
    echo ║                                                            ║
    echo ║  🛑 Close terminal windows to stop services               ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.

    echo [INFO] Services are starting in separate windows
    echo [INFO] Press any key to exit this launcher...
    pause >nul

) else (
    echo [ERROR] Invalid mode: %MODE%
    echo Usage: start.bat [dev^|docker]
    echo   dev    - Start in development mode (default)
    echo   docker - Start using Docker containers
    pause
    exit /b 1
)

echo [INFO] Script completed
endlocal