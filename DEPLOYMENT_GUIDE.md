# 🚀 Server Deployment Guide

## Base URL
**Production API:** `https://apipos.v11tech.com/`

---

## 📋 Prerequisites

- Ubuntu/Debian server with sudo access
- Domain pointed to server IP: `apipos.v11tech.com`
- Ports 80 and 443 open
- Docker and Docker Compose installed

---

## 🔧 Step-by-Step Deployment

### 1. Connect to Server

```bash
ssh username@your-server-ip
```

### 2. Install Docker (if not installed)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again for group changes to take effect
```

### 3. Clone Repository

```bash
# Navigate to deployment directory
cd /var/www/

# Clone the repository (replace YOUR_TOKEN with your GitHub token)
sudo git clone https://YOUR_GITHUB_TOKEN@github.com/josephbruno/v11pos-backend-fastapi.git

# Change ownership
sudo chown -R $USER:$USER v11pos-backend-fastapi

# Navigate to project
cd v11pos-backend-fastapi
```

### 4. Configure Environment

```bash
# Create .env file
nano .env
```

**Add the following:**
```env
# Database Configuration
DB_HOST=host.docker.internal
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=restaurant_pos

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
BASE_URL=https://apipos.v11tech.com

# Security
SECRET_KEY=your_very_secure_random_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (for password reset)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@v11tech.com
```

### 5. Setup MySQL Database

```bash
# Install MySQL if not installed
sudo apt install mysql-server -y

# Secure MySQL installation
sudo mysql_secure_installation

# Login to MySQL
sudo mysql -u root -p

# Create database and user
CREATE DATABASE restaurant_pos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'pos_user'@'%' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON restaurant_pos.* TO 'pos_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

### 6. Run Database Migration

```bash
# Run translation table migration
sudo mysql -u root -p restaurant_pos < migrations/add_translations_table.sql

# Initialize database with sample data
python3 init_db.py
```

### 7. Create Sample Images Directory

```bash
# Create uploads directory structure
mkdir -p uploads/products uploads/categories

# Set permissions
chmod -R 755 uploads
```

### 8. Build and Start Docker Containers

```bash
# Build the Docker image
sudo docker-compose build

# Start containers
sudo docker-compose up -d

# Check container status
sudo docker ps
```

### 9. Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/apipos
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name apipos.v11tech.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name apipos.v11tech.com;

    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/letsencrypt/live/apipos.v11tech.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/apipos.v11tech.com/privkey.pem;

    # Upload size limit
    client_max_body_size 50M;

    # API Proxy
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Static files (uploads)
    location /uploads/ {
        alias /var/www/v11pos-backend-fastapi/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/apipos /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 10. Setup SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d apipos.v11tech.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 11. Upload Sample Images

**Option 1: Using SCP from local machine**
```bash
# From your local machine
scp -r uploads/products/* username@server-ip:/var/www/v11pos-backend-fastapi/uploads/products/
scp -r uploads/categories/* username@server-ip:/var/www/v11pos-backend-fastapi/uploads/categories/
```

**Option 2: Download sample images on server**
```bash
# Create download script on server
cd /var/www/v11pos-backend-fastapi
./download_sample_images.sh
```

### 12. Verify Deployment

```bash
# Check API health
curl https://apipos.v11tech.com/

# Check products endpoint
curl https://apipos.v11tech.com/api/v1/products/

# Check categories endpoint
curl https://apipos.v11tech.com/api/v1/categories/

# Check translations endpoint
curl https://apipos.v11tech.com/api/v1/translations/languages
```

---

## 📦 Sample Data Setup

### Create Sample Products with Images

```bash
# From server, run seed script
cd /var/www/v11pos-backend-fastapi
python3 seed_data.py
```

### Test Translation System

```bash
# Test Spanish translations
curl -H "Accept-Language: es" https://apipos.v11tech.com/api/v1/products/

# Test French translations
curl -H "Accept-Language: fr" https://apipos.v11tech.com/api/v1/categories/

# Test Arabic translations
curl -H "Accept-Language: ar" https://apipos.v11tech.com/api/v1/modifiers/
```

---

## 🔄 Updating Deployment

```bash
# Navigate to project directory
cd /var/www/v11pos-backend-fastapi

# Pull latest changes
git pull origin master

# Rebuild and restart containers
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d

# Check logs
sudo docker logs -f restaurant_pos_api
```

---

## 📊 Monitoring

### View Logs
```bash
# API logs
sudo docker logs -f restaurant_pos_api

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Check Container Status
```bash
# List running containers
sudo docker ps

# Check container resource usage
sudo docker stats restaurant_pos_api
```

---

## 🔒 Security Checklist

- [ ] MySQL root password changed
- [ ] Database user created with limited privileges
- [ ] .env file with secure SECRET_KEY
- [ ] Firewall configured (UFW)
- [ ] SSL certificate installed and auto-renewal enabled
- [ ] Nginx security headers configured
- [ ] Docker containers running as non-root user
- [ ] Regular backups configured

---

## 🔥 Firewall Configuration

```bash
# Install UFW
sudo apt install ufw -y

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MySQL (only from localhost)
sudo ufw allow from 127.0.0.1 to any port 3306

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 💾 Backup Strategy

### Database Backup
```bash
# Create backup script
sudo nano /usr/local/bin/backup-pos-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/restaurant_pos"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u root -p'your_password' restaurant_pos > $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-pos-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-pos-db.sh
```

### Files Backup
```bash
# Backup uploads directory
tar -czf /var/backups/uploads_$(date +%Y%m%d).tar.gz /var/www/v11pos-backend-fastapi/uploads/
```

---

## 🧪 Testing Endpoints

### Test Products API
```bash
# List products
curl https://apipos.v11tech.com/api/v1/products/

# Get single product
curl https://apipos.v11tech.com/api/v1/products/{product_id}

# Create product with translation
curl -X POST https://apipos.v11tech.com/api/v1/products/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Test Product" \
  -d "description=Test Description" \
  -d "price=10.00" \
  -d "category_id=cat123" \
  -d "available=true" \
  -d 'translations_json={"es":{"name":"Producto de Prueba"}}'
```

### Test Categories API
```bash
# List categories
curl https://apipos.v11tech.com/api/v1/categories/

# Get with Spanish translation
curl -H "Accept-Language: es" https://apipos.v11tech.com/api/v1/categories/
```

### Test File Upload
```bash
# Upload category image
curl -X POST https://apipos.v11tech.com/api/v1/file-manager/upload \
  -F "file=@/path/to/image.jpg" \
  -F "entity_type=category" \
  -F "entity_id=cat123"
```

---

## 📝 API Documentation

Once deployed, access API documentation at:
- **Swagger UI:** https://apipos.v11tech.com/docs
- **ReDoc:** https://apipos.v11tech.com/redoc

---

## 🆘 Troubleshooting

### Container Not Starting
```bash
# Check logs
sudo docker logs restaurant_pos_api

# Restart container
sudo docker restart restaurant_pos_api
```

### Database Connection Error
```bash
# Check MySQL is running
sudo systemctl status mysql

# Test connection
mysql -u pos_user -p -h localhost restaurant_pos
```

### Nginx Not Working
```bash
# Test configuration
sudo nginx -t

# Check status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx
```

### SSL Certificate Issues
```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

---

## 📞 Support

For issues or questions:
- Check logs: `sudo docker logs -f restaurant_pos_api`
- Review documentation in repository
- Check Nginx logs: `/var/log/nginx/error.log`

---

**Deployment Status:** Ready for Production
**Base URL:** https://apipos.v11tech.com/
**Last Updated:** November 28, 2025
