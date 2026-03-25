# Docker Setup Guide - FastAPI POS Backend

## Prerequisites

1. **Docker Desktop** must be installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Make sure Docker Desktop is running (check system tray)

2. **MySQL Database** must be running on your host machine
   - The application will connect to MySQL on `localhost:3306`
   - Or update `.env` file with your MySQL connection details

## Quick Setup Steps

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your Windows machine.

### Step 2: Create Environment File
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

Or create `.env` manually with this content:
```env
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
```

**Important:** Update the database credentials to match your MySQL setup!

### Step 3: Build Docker Image
```powershell
docker-compose build
```

### Step 4: Start the Container
```powershell
docker-compose up -d
```

### Step 5: Check Container Status
```powershell
docker-compose ps
```

### Step 6: View Logs
```powershell
docker-compose logs -f fastapi
```

## Access the Application

Once running, you can access:

- **API Documentation (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **API Base URL:** http://localhost:8000/api/v1

## Database Setup

### Option 1: Use Existing MySQL on Host

The docker-compose.yml uses `network_mode: host`, so the container can access services on your host machine.

1. Make sure MySQL is running on your host
2. Create the database:
   ```sql
   CREATE DATABASE fastapi_pos;
   ```
3. Update `.env` with your MySQL credentials

### Option 2: Run Migrations

After the container is running, run database migrations:

```powershell
# Create initial migration
docker-compose exec fastapi alembic revision --autogenerate -m "Initial migration"

# Apply migrations
docker-compose exec fastapi alembic upgrade head
```

## Useful Docker Commands

### View Container Logs
```powershell
docker-compose logs -f fastapi
```

### Stop Container
```powershell
docker-compose down
```

### Restart Container
```powershell
docker-compose restart
```

### Access Container Shell
```powershell
docker-compose exec fastapi bash
```

### Rebuild and Restart
```powershell
docker-compose down
docker-compose build
docker-compose up -d
```

### View Container Status
```powershell
docker-compose ps
```

## Troubleshooting

### Docker Desktop Not Running
**Error:** "error during connect: This error may indicate that the docker daemon is not running"

**Solution:** Start Docker Desktop from the Start menu or system tray

### Port Already in Use
**Error:** "port is already allocated"

**Solution:** 
1. Stop any service using port 8000
2. Or change the port in docker-compose.yml

### Database Connection Failed
**Error:** "Can't connect to MySQL server"

**Solution:**
1. Make sure MySQL is running on your host
2. Verify credentials in `.env` file
3. Check if database exists: `CREATE DATABASE fastapi_pos;`
4. For Windows, use `host.docker.internal` instead of `localhost` in `.env`:
   ```env
   DB_HOST=host.docker.internal
   ```

### Container Exits Immediately
**Solution:**
1. Check logs: `docker-compose logs fastapi`
2. Verify `.env` file exists and has correct values
3. Make sure all dependencies are in requirements.txt

## Testing the API

### Test Health Endpoint
```powershell
curl http://localhost:8000/health
```

### Test Login Endpoint (JSON)
```powershell
$body = @{
    email = "superadmin@restaurant.com"
    password = "Super@123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method Post -ContentType "application/json" -Body $body
```

### Run Test Script
```powershell
.\test_login_formats.ps1
```

## Next Steps

1. **Start Docker Desktop**
2. **Create `.env` file** with your database credentials
3. **Run:** `docker-compose up -d`
4. **Check logs:** `docker-compose logs -f fastapi`
5. **Access API docs:** http://localhost:8000/docs

## Additional Resources

- **API Documentation:** See `API_ENDPOINTS_REFERENCE.md`
- **Login Fix:** See `LOGIN_FIX_SUMMARY.md`
- **Complete Guide:** See `RESOLUTION_SUMMARY.md`
