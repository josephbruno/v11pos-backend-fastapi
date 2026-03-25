# FastAPI POS System - Docker Setup and Run Script for Windows
# This script sets up the environment and runs the Docker container

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FastAPI POS System - Docker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "Success: Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Success: .env file created" -ForegroundColor Green
        Write-Host "Warning: Please update .env with your database credentials if needed" -ForegroundColor Yellow
    } else {
        Write-Host "Creating default .env file..." -ForegroundColor Yellow
        $envContent = @"
# Application Environment
APP_ENV=development

# Database Configuration (MySQL on host)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fastapi_pos
DB_USER=root
DB_PASSWORD=root

# JWT Configuration
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "Success: Default .env file created" -ForegroundColor Green
    }
} else {
    Write-Host "Success: .env file already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building Docker Image" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Build the Docker image
Write-Host "Building FastAPI image..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host "Success: Docker image built successfully" -ForegroundColor Green
} else {
    Write-Host "Error: Failed to build Docker image" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Docker Container" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the container
Write-Host "Starting FastAPI container..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "Success: Container started successfully" -ForegroundColor Green
} else {
    Write-Host "Error: Failed to start container" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Waiting for application to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Container Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "API Base URL: http://localhost:8000/api/v1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:        docker-compose logs -f" -ForegroundColor White
Write-Host "  Stop container:   docker-compose down" -ForegroundColor White
Write-Host "  Restart:          docker-compose restart" -ForegroundColor White
Write-Host "  Shell access:     docker-compose exec fastapi bash" -ForegroundColor White
Write-Host ""
Write-Host "To view live logs, run:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f fastapi" -ForegroundColor White
Write-Host ""
