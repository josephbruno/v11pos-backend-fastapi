# Restaurant POS - Docker Setup Guide

## Quick Start

Run the automated setup script:
```bash
./docker-setup.sh
```

This script will:
- ✅ Verify Docker and MySQL are running
- ✅ Check database exists
- ✅ Build Docker image
- ✅ Start the application
- ✅ Test API connectivity

## Manual Commands

### Build and Start
```bash
sudo docker compose up --build -d
```

### View Logs
```bash
sudo docker compose logs -f
```

### Stop Application
```bash
sudo docker compose stop
```

### Start Application
```bash
sudo docker compose start
```

### Restart Application
```bash
sudo docker compose restart
```

### Stop and Remove Containers
```bash
sudo docker compose down
```

### View Container Status
```bash
sudo docker compose ps
```

## Access Points

- **API Server:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Database Configuration

The application connects to your **local MySQL server** (not a container):

- **Host (from host):** localhost
- **Host (from container):** host.docker.internal
- **Port:** 3306
- **Database:** restaurant_pos
- **Username:** root
- **Password:** root

## Admin Credentials

- **Email:** admin@restaurant.com
- **Password:** Admin123!

## Prerequisites

1. **Docker & Docker Compose** installed
2. **MySQL 8.0** running on localhost:3306
3. **Database** `restaurant_pos` must exist

### Setup MySQL Permissions

If you encounter access denied errors:
```bash
mysql -h localhost -u root -proot -e "GRANT ALL PRIVILEGES ON restaurant_pos.* TO 'root'@'%'; FLUSH PRIVILEGES;"
```

### Add User to Docker Group (Optional)

To run Docker without sudo:
```bash
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

## Troubleshooting

### Check Container Logs
```bash
sudo docker compose logs --tail=50
```

### Check Container is Running
```bash
sudo docker compose ps
```

### Restart Container
```bash
sudo docker compose restart
```

### Rebuild from Scratch
```bash
sudo docker compose down
sudo docker compose up --build -d
```

## Architecture

- **Application:** FastAPI (Python 3.10-slim)
- **Database:** MySQL 8.0 (local, not containerized)
- **Connection:** Docker container connects to host MySQL via `host.docker.internal`
- **Port:** 8000 (mapped to host)
- **Volumes:** 
  - `./app` → `/app/app` (live code reload)
  - `./uploads` → `/app/uploads` (file storage)

## Response Format

All API endpoints return standardized responses:
```json
{
  "status": "success",
  "message": "Operation description",
  "data": { }
}
```

## Features

- ✅ 133 API endpoints
- ✅ JWT Authentication (24-hour expiration)
- ✅ Product catalog management
- ✅ Customer & loyalty system
- ✅ QR code ordering
- ✅ Order management
- ✅ Analytics & dashboard
- ✅ File upload support
- ✅ Tax settings
