@echo off
REM RestaurantPOS FastAPI - Start Script
REM This script activates the virtual environment and starts the development server

echo.
echo =====================================================
echo   RestaurantPOS FastAPI - Development Server
echo =====================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\Activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\Activate.bat

REM Check if the activation was successful
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated!
echo.
echo Starting FastAPI server...
echo.
echo API will be available at:
echo   - Swagger UI: http://localhost:8000/docs
echo   - ReDoc:      http://localhost:8000/redoc
echo   - API Base:   http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
