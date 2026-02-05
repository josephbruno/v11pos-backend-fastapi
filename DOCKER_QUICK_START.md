# 🚀 Quick Start - Docker Setup

## ⚡ Fast Setup (3 Steps)

### 1️⃣ Start Docker Desktop
Make sure Docker Desktop is running (check system tray)

### 2️⃣ Run Setup Script
**Option A - Batch File (Easiest):**
```cmd
docker-setup.bat
```

**Option B - PowerShell:**
```powershell
.\docker-setup.ps1
```

**Option C - Manual:**
```powershell
# Create .env file
Copy-Item .env.example .env

# Build and start
docker-compose build
docker-compose up -d
```

### 3️⃣ Access the API
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 📋 Before You Start

### ✅ Requirements
- [x] Docker Desktop installed and running
- [x] MySQL running on localhost:3306 (or update `.env`)
- [x] Database created: `CREATE DATABASE fastapi_pos;`

### ⚙️ Configure Database
Edit `.env` file with your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fastapi_pos
DB_USER=root
DB_PASSWORD=your_password
```

---

## 🎯 Common Commands

| Action | Command |
|--------|---------|
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose down` |
| **Restart** | `docker-compose restart` |
| **View Logs** | `docker-compose logs -f fastapi` |
| **Shell Access** | `docker-compose exec fastapi bash` |
| **Rebuild** | `docker-compose build --no-cache` |

---

## 🔧 Run Migrations

After container is running:
```powershell
# Create migration
docker-compose exec fastapi alembic revision --autogenerate -m "Initial migration"

# Apply migration
docker-compose exec fastapi alembic upgrade head
```

---

## 🧪 Test the API

### Quick Health Check
```powershell
curl http://localhost:8000/health
```

### Test Login
```powershell
.\test_login_formats.ps1
```

---

## ❌ Troubleshooting

### Docker Not Running
```
Error: Cannot connect to Docker daemon
```
**Fix:** Start Docker Desktop

### Port Already in Use
```
Error: port is already allocated
```
**Fix:** Stop service on port 8000 or change port in docker-compose.yml

### Database Connection Failed
```
Error: Can't connect to MySQL server
```
**Fix:** 
1. Start MySQL
2. Check `.env` credentials
3. Use `host.docker.internal` instead of `localhost` on Windows

---

## 📚 Documentation

| File | Description |
|------|-------------|
| `DOCKER_SETUP_GUIDE.md` | Complete setup guide |
| `API_ENDPOINTS_REFERENCE.md` | All API endpoints |
| `LOGIN_FIX_SUMMARY.md` | Login endpoint details |
| `RESOLUTION_SUMMARY.md` | Complete overview |

---

## 🎉 Next Steps

1. ✅ Start Docker Desktop
2. ✅ Run `docker-setup.bat`
3. ✅ Open http://localhost:8000/docs
4. ✅ Test login with `.\test_login_formats.ps1`

**Need help?** Check `DOCKER_SETUP_GUIDE.md` for detailed instructions.
