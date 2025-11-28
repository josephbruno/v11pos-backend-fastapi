# Restaurant POS - FastAPI Backend

## 🌐 Production API
**Live API:** https://apipos.v11tech.com/
- **API Docs:** https://apipos.v11tech.com/docs
- **ReDoc:** https://apipos.v11tech.com/redoc

## 🚀 One Command Setup with Docker

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed ([Get Docker Compose](https://docs.docker.com/compose/install/))

### Start Everything

Run this single command:

```bash
./docker-setup.sh
```

Or manually:

```bash
docker-compose up --build -d
```

That's it! Everything will be set up automatically:
- ✅ MySQL Database
- ✅ FastAPI Application
- ✅ Database Tables
- ✅ Ready to use

---

## 📍 Access Points

- **API Server:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🔐 Default Credentials

### Admin User
- Email: `admin@restaurant.com`
- Password: `Admin123!`

### Database
- Host: `localhost`
- Port: `3306`
- Database: `restaurant_pos`
- Username: `root`
- Password: `root`

---

## 📋 Docker Commands

### Start
```bash
docker-compose up -d
```

### Stop
```bash
docker-compose down
```

### Restart
```bash
docker-compose restart
```

### View Logs
```bash
docker-compose logs -f
```

### View API Logs Only
```bash
docker-compose logs -f api
```

### View Database Logs Only
```bash
docker-compose logs -f mysql
```

### Rebuild
```bash
docker-compose up --build -d
```

### Stop and Remove Everything (including data)
```bash
docker-compose down -v
```

---

## 🧪 Test the API

### Quick Test
```bash
curl http://localhost:8000/health
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@restaurant.com","password":"Admin123!"}'
```

---

## 🛠️ Development

### Hot Reload
The application automatically reloads when you modify files in the `app/` directory.

### Access Database
```bash
docker exec -it restaurant_pos_db mysql -u root -proot restaurant_pos
```

### Access API Container
```bash
docker exec -it restaurant_pos_api bash
```

---

## 📦 What's Included

- **MySQL 8.0** - Database server
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **JWT Authentication** - Secure auth
- **Standard Response Format** - Consistent API responses

---

## 🔄 Update Application

1. Stop containers:
```bash
docker-compose down
```

2. Pull latest changes (if using git):
```bash
git pull
```

3. Rebuild and start:
```bash
docker-compose up --build -d
```

---

## 📊 Check Status

```bash
docker-compose ps
```

Expected output:
```
Name                    State    Ports
restaurant_pos_api      Up      0.0.0.0:8000->8000/tcp
restaurant_pos_db       Up      0.0.0.0:3306->3306/tcp
```

---

## 🐛 Troubleshooting

### Port Already in Use
If port 8000 or 3306 is already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Change to different port
```

### Database Connection Failed
Wait a few seconds for MySQL to initialize:
```bash
docker-compose logs mysql
```

### View All Logs
```bash
docker-compose logs
```

### Clean Start
```bash
docker-compose down -v
docker-compose up --build -d
```

---

## 🌐 Production Deployment

**Live Production Server:** https://apipos.v11tech.com/

### Quick Deploy to Server

```bash
# One-line deployment (on server as root)
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/josephbruno/v11pos-backend-fastapi/master/deploy.sh)"
```

### Manual Deployment

See comprehensive guides:
- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - Quick commands reference
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide

### Key Features in Production
- ✅ SSL/HTTPS with Let's Encrypt
- ✅ Nginx reverse proxy
- ✅ Multi-language support (en, es, fr, ar)
- ✅ Sample images included
- ✅ Database migrations automated
- ✅ Docker containerized
- ✅ API documentation available

### Production Scripts
- `deploy.sh` - Automated deployment
- `download_sample_images.sh` - Download sample images
- `test_production_api.sh` - Test all endpoints

---

## 📝 API Response Format

All endpoints return standardized responses:

```json
{
  "status": "success",
  "message": "Operation description",
  "data": {
    // Response data
  }
}
```

---

## 💾 Data Persistence

Database data is persisted in Docker volumes. To backup:

```bash
docker exec restaurant_pos_db mysqldump -u root -proot restaurant_pos > backup.sql
```

To restore:

```bash
docker exec -i restaurant_pos_db mysql -u root -proot restaurant_pos < backup.sql
```

---

## ✅ Success!

Your Restaurant POS system is now running!

Visit http://localhost:8000/docs to explore the API.
