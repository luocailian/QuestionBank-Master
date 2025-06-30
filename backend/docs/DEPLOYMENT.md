# QuestionBank Master 部署指南

## 概述

本文档详细介绍了如何在不同环境中部署 QuestionBank Master 系统。

## 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Docker

### 推荐配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **操作系统**: Ubuntu 22.04 LTS

### 软件依赖
- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Redis 7+
- Nginx 1.18+

## 开发环境部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd questionbank-master
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接

# 初始化数据库
flask init-db
flask create-admin
flask seed-data

# 启动后端服务
flask run
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 一键启动脚本

```bash
chmod +x start-dev.sh
./start-dev.sh
```

## 生产环境部署

### 方式一：Docker Compose（推荐）

#### 1. 准备配置文件

```bash
# 复制环境变量文件
cp backend/.env.example backend/.env

# 编辑环境变量
vim backend/.env
```

**环境变量配置示例**:
```bash
# Flask配置
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# 数据库配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=questionbank
MYSQL_PASSWORD=your-secure-password
MYSQL_DATABASE=questionbank_master

# Redis配置
REDIS_URL=redis://redis:6379/0

# 邮件配置（可选）
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

#### 2. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 初始化数据库（首次部署）
docker-compose exec backend flask init-db
docker-compose exec backend flask create-admin
```

#### 3. 配置反向代理

创建 `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端API
    location /api/ {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 文件上传大小限制
        client_max_body_size 50M;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 方式二：手动部署

#### 1. 安装系统依赖

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm mysql-server redis-server nginx
```

**CentOS/RHEL**:
```bash
sudo yum update
sudo yum install -y python3 python3-pip nodejs npm mysql-server redis nginx
```

#### 2. 配置数据库

```bash
# 启动MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation

# 创建数据库和用户
mysql -u root -p
```

```sql
CREATE DATABASE questionbank_master CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'questionbank'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON questionbank_master.* TO 'questionbank'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. 配置Redis

```bash
sudo systemctl start redis
sudo systemctl enable redis

# 配置Redis（可选）
sudo vim /etc/redis/redis.conf
```

#### 4. 部署后端

```bash
# 创建应用目录
sudo mkdir -p /opt/questionbank-master
sudo chown $USER:$USER /opt/questionbank-master
cd /opt/questionbank-master

# 克隆代码
git clone <repository-url> .

# 设置后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env

# 初始化数据库
flask init-db
flask create-admin

# 创建systemd服务
sudo vim /etc/systemd/system/questionbank-backend.service
```

**systemd服务配置**:
```ini
[Unit]
Description=QuestionBank Master Backend
After=network.target mysql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/questionbank-master/backend
Environment=PATH=/opt/questionbank-master/backend/venv/bin
ExecStart=/opt/questionbank-master/backend/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动后端服务
sudo systemctl daemon-reload
sudo systemctl start questionbank-backend
sudo systemctl enable questionbank-backend
```

#### 5. 部署前端

```bash
cd /opt/questionbank-master/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 配置Nginx
sudo vim /etc/nginx/sites-available/questionbank-master
```

**Nginx配置**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /opt/questionbank-master/frontend/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/questionbank-master /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL证书配置

### 使用Let's Encrypt

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 监控和日志

### 1. 日志配置

```bash
# 创建日志目录
sudo mkdir -p /var/log/questionbank-master
sudo chown www-data:www-data /var/log/questionbank-master

# 配置日志轮转
sudo vim /etc/logrotate.d/questionbank-master
```

```
/var/log/questionbank-master/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload questionbank-backend
    endscript
}
```

### 2. 系统监控

```bash
# 安装监控工具
sudo apt install htop iotop nethogs

# 查看系统状态
sudo systemctl status questionbank-backend
sudo systemctl status nginx
sudo systemctl status mysql
sudo systemctl status redis
```

## 备份策略

### 1. 数据库备份

```bash
# 创建备份脚本
sudo vim /opt/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="questionbank_master"
DB_USER="questionbank"
DB_PASS="your-password"

mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/db_backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
```

```bash
# 设置定时备份
sudo chmod +x /opt/backup-db.sh
sudo crontab -e
# 添加: 0 2 * * * /opt/backup-db.sh
```

### 2. 文件备份

```bash
# 备份上传的文件
sudo rsync -av /opt/questionbank-master/backend/uploads/ /opt/backups/uploads/
```

## 性能优化

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX idx_questions_bank_type ON questions(bank_id, type);
CREATE INDEX idx_user_answers_user_question ON user_answers(user_id, question_id);
```

### 2. Redis缓存配置

```bash
# 编辑Redis配置
sudo vim /etc/redis/redis.conf

# 设置内存限制
maxmemory 1gb
maxmemory-policy allkeys-lru

# 启用持久化
save 900 1
save 300 10
save 60 10000
```

### 3. Nginx优化

```nginx
# 在http块中添加
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

# 连接池优化
upstream backend {
    server 127.0.0.1:5000;
    keepalive 32;
}
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查MySQL状态
   sudo systemctl status mysql
   
   # 检查连接
   mysql -u questionbank -p questionbank_master
   ```

2. **Redis连接失败**
   ```bash
   # 检查Redis状态
   sudo systemctl status redis
   
   # 测试连接
   redis-cli ping
   ```

3. **文件上传失败**
   ```bash
   # 检查目录权限
   ls -la /opt/questionbank-master/backend/uploads/
   
   # 修复权限
   sudo chown -R www-data:www-data /opt/questionbank-master/backend/uploads/
   ```

4. **前端页面空白**
   ```bash
   # 检查构建文件
   ls -la /opt/questionbank-master/frontend/dist/
   
   # 重新构建
   cd /opt/questionbank-master/frontend
   npm run build
   ```

### 日志查看

```bash
# 后端日志
sudo journalctl -u questionbank-backend -f

# Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# MySQL日志
sudo tail -f /var/log/mysql/error.log
```

## 安全建议

1. **防火墙配置**
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   ```

2. **定期更新**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

3. **监控异常访问**
   ```bash
   # 安装fail2ban
   sudo apt install fail2ban
   ```

4. **数据库安全**
   - 使用强密码
   - 限制数据库用户权限
   - 定期备份数据

5. **应用安全**
   - 定期更新依赖包
   - 使用HTTPS
   - 配置安全头
