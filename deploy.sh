#!/bin/bash

# 🚀 Quick Deployment Script for apipos.v11tech.com
# Run this script on your server after cloning the repository

set -e  # Exit on any error

echo "🚀 Starting deployment for apipos.v11tech.com..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/var/www/v11pos-backend-fastapi"
DOMAIN="apipos.v11tech.com"

# Check if running as sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: Update system
echo -e "${GREEN}[1/12] Updating system...${NC}"
apt update && apt upgrade -y

# Step 2: Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}[2/12] Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${YELLOW}[2/12] Docker already installed${NC}"
fi

# Step 3: Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}[3/12] Installing Docker Compose...${NC}"
    apt install docker-compose -y
else
    echo -e "${YELLOW}[3/12] Docker Compose already installed${NC}"
fi

# Step 4: Install MySQL
if ! command -v mysql &> /dev/null; then
    echo -e "${GREEN}[4/12] Installing MySQL...${NC}"
    apt install mysql-server -y
else
    echo -e "${YELLOW}[4/12] MySQL already installed${NC}"
fi

# Step 5: Install Nginx
if ! command -v nginx &> /dev/null; then
    echo -e "${GREEN}[5/12] Installing Nginx...${NC}"
    apt install nginx -y
else
    echo -e "${YELLOW}[5/12] Nginx already installed${NC}"
fi

# Step 6: Clone repository
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${GREEN}[6/12] Cloning repository...${NC}"
    echo -e "${YELLOW}Enter your GitHub token or username:password${NC}"
    read -sp "GitHub Token: " GITHUB_TOKEN
    echo ""
    mkdir -p /var/www
    cd /var/www
    git clone https://${GITHUB_TOKEN}@github.com/josephbruno/v11pos-backend-fastapi.git
    cd v11pos-backend-fastapi
else
    echo -e "${YELLOW}[6/12] Repository already exists, pulling latest changes...${NC}"
    cd $PROJECT_DIR
    git pull origin master
fi

# Step 7: Create uploads directories
echo -e "${GREEN}[7/12] Creating upload directories...${NC}"
mkdir -p uploads/products uploads/categories
chmod -R 755 uploads

# Step 8: Create .env file if not exists
if [ ! -f ".env" ]; then
    echo -e "${GREEN}[8/12] Creating .env file...${NC}"
    cat > .env << EOF
# Database Configuration
DB_HOST=host.docker.internal
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=restaurant_pos

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
BASE_URL=https://${DOMAIN}

# Security
SECRET_KEY=$(openssl rand -base64 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@v11tech.com
EOF
    echo -e "${YELLOW}⚠️  Please update .env file with your actual credentials${NC}"
else
    echo -e "${YELLOW}[8/12] .env file already exists${NC}"
fi

# Step 9: Setup database
echo -e "${GREEN}[9/12] Setting up database...${NC}"
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS restaurant_pos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EOF

# Run migration
if [ -f "migrations/add_translations_table.sql" ]; then
    echo -e "${GREEN}Running database migration...${NC}"
    mysql -u root -p restaurant_pos < migrations/add_translations_table.sql
fi

# Step 10: Build and start Docker containers
echo -e "${GREEN}[10/12] Building and starting Docker containers...${NC}"
docker-compose down 2>/dev/null || true
docker-compose build
docker-compose up -d

# Wait for container to start
echo -e "${YELLOW}Waiting for API to start...${NC}"
sleep 10

# Check if container is running
if docker ps | grep -q restaurant_pos_api; then
    echo -e "${GREEN}✓ API container is running${NC}"
else
    echo -e "${RED}✗ API container failed to start${NC}"
    docker logs restaurant_pos_api
    exit 1
fi

# Step 11: Configure Nginx
echo -e "${GREEN}[11/12] Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/apipos << 'EOF'
server {
    listen 80;
    server_name apipos.v11tech.com;
    
    # For Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
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
    
    # Static files
    location /uploads/ {
        alias /var/www/v11pos-backend-fastapi/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    client_max_body_size 50M;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/apipos /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t && systemctl reload nginx

# Step 12: Setup SSL with Let's Encrypt
echo -e "${GREEN}[12/12] Setting up SSL certificate...${NC}"
if ! command -v certbot &> /dev/null; then
    apt install certbot python3-certbot-nginx -y
fi

echo -e "${YELLOW}To complete SSL setup, run:${NC}"
echo -e "${GREEN}sudo certbot --nginx -d ${DOMAIN}${NC}"

# Setup firewall
echo -e "${GREEN}Configuring firewall...${NC}"
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow from 127.0.0.1 to any port 3306

# Final status check
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "API URL: ${GREEN}http://${DOMAIN}${NC}"
echo -e "API Docs: ${GREEN}http://${DOMAIN}/docs${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update .env file with your credentials"
echo -e "2. Run: ${GREEN}sudo certbot --nginx -d ${DOMAIN}${NC}"
echo -e "3. Test API: ${GREEN}curl http://${DOMAIN}/api/v1/products/${NC}"
echo -e "4. Upload sample images"
echo -e "5. Run seed data: ${GREEN}python3 seed_data.py${NC}"
echo ""
echo -e "${YELLOW}Check logs:${NC}"
echo -e "- API: ${GREEN}docker logs -f restaurant_pos_api${NC}"
echo -e "- Nginx: ${GREEN}tail -f /var/log/nginx/error.log${NC}"
echo ""
