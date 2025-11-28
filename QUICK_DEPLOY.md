# 🚀 Quick Deployment Commands

## Production Server: https://apipos.v11tech.com/

---

## 🔧 One-Line Deployment (On Server)

```bash
# As root or with sudo
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/josephbruno/v11pos-backend-fastapi/master/deploy.sh)"
```

---

## 📦 Manual Deployment Steps

### 1. SSH into Server
```bash
ssh username@your-server-ip
```

### 2. Clone Repository
```bash
cd /var/www
sudo git clone https://YOUR_TOKEN@github.com/josephbruno/v11pos-backend-fastapi.git
cd v11pos-backend-fastapi
```

### 3. Run Deployment Script
```bash
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

### 4. Download Sample Images
```bash
chmod +x download_sample_images.sh
./download_sample_images.sh
```

### 5. Setup SSL Certificate
```bash
sudo certbot --nginx -d apipos.v11tech.com
```

### 6. Test API
```bash
chmod +x test_production_api.sh
./test_production_api.sh
```

---

## 🧪 Quick Tests

### Test Root Endpoint
```bash
curl https://apipos.v11tech.com/
```

### Test Products API (English)
```bash
curl https://apipos.v11tech.com/api/v1/products/
```

### Test Products API (Spanish)
```bash
curl -H "Accept-Language: es" https://apipos.v11tech.com/api/v1/products/
```

### Test Categories API
```bash
curl https://apipos.v11tech.com/api/v1/categories/
```

### Test Image Access
```bash
curl -I https://apipos.v11tech.com/uploads/products/coca-cola.jpg
```

---

## 📚 API Documentation

- **Swagger UI:** https://apipos.v11tech.com/docs
- **ReDoc:** https://apipos.v11tech.com/redoc

---

## 🔄 Update Deployment

```bash
cd /var/www/v11pos-backend-fastapi
git pull origin master
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d
```

---

## 📊 Monitoring Commands

### View API Logs
```bash
sudo docker logs -f restaurant_pos_api
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Container Status
```bash
sudo docker ps
sudo docker stats restaurant_pos_api
```

### Check Disk Space
```bash
df -h
```

---

## 🔒 Security Checklist

- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] Strong database passwords set
- [ ] .env file with secure SECRET_KEY
- [ ] Regular backups configured
- [ ] Fail2ban installed (optional)

---

## 💾 Backup Database

```bash
# Manual backup
mysqldump -u root -p restaurant_pos > backup_$(date +%Y%m%d).sql

# Automated backup (add to crontab)
sudo crontab -e
# Add: 0 2 * * * mysqldump -u root -p'password' restaurant_pos > /var/backups/db_$(date +\%Y\%m\%d).sql
```

---

## 🆘 Troubleshooting

### API Not Starting
```bash
sudo docker logs restaurant_pos_api
sudo docker restart restaurant_pos_api
```

### Database Connection Issues
```bash
sudo systemctl status mysql
mysql -u root -p
```

### Nginx Issues
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate Issues
```bash
sudo certbot renew
sudo certbot certificates
```

---

## 📞 Support

For detailed documentation, see:
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `README.md` - Project documentation
- `TRANSLATION_API_INTEGRATION_COMPLETE.md` - Translation system docs

---

**Base URL:** https://apipos.v11tech.com/
**Repository:** https://github.com/josephbruno/v11pos-backend-fastapi
**Last Updated:** November 28, 2025
