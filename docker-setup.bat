@echo off
echo ========================================
echo FastAPI POS System - Docker Setup
echo ========================================
echo.

REM Check if Docker is running
echo Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    echo.
    pause
    exit /b 1
)
echo SUCCESS: Docker is running
echo.

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo SUCCESS: .env file created from .env.example
        echo WARNING: Please update .env with your database credentials!
    ) else (
        echo Creating default .env file...
        (
            echo # Application Environment
            echo APP_ENV=development
            echo.
            echo # Database Configuration ^(MySQL on host^)
            echo DB_HOST=localhost
            echo DB_PORT=3306
            echo DB_NAME=fastapi_pos
            echo DB_USER=root
            echo DB_PASSWORD=root
            echo.
            echo # JWT Configuration
            echo JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
            echo JWT_ALGORITHM=HS256
            echo ACCESS_TOKEN_EXPIRE_MINUTES=30
            echo REFRESH_TOKEN_EXPIRE_DAYS=7
        ) > .env
        echo SUCCESS: Default .env file created
    )
    echo.
) else (
    echo SUCCESS: .env file already exists
    echo.
)

echo ========================================
echo Building Docker Image
echo ========================================
echo.
docker-compose build
if errorlevel 1 (
    echo ERROR: Failed to build Docker image
    pause
    exit /b 1
)
echo SUCCESS: Docker image built
echo.

echo ========================================
echo Starting Docker Container
echo ========================================
echo.
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start container
    pause
    exit /b 1
)
echo SUCCESS: Container started
echo.

echo Waiting for application to start...
timeout /t 5 /nobreak >nul
echo.

echo ========================================
echo Container Status
echo ========================================
docker-compose ps
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo API Documentation: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo API Base URL: http://localhost:8000/api/v1
echo.
echo Useful Commands:
echo   View logs:        docker-compose logs -f
echo   Stop container:   docker-compose down
echo   Restart:          docker-compose restart
echo.
echo To view live logs, run:
echo   docker-compose logs -f fastapi
echo.
pause
