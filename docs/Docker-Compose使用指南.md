# Docker Compose 使用指南

## 概述

QuestionBank Master 提供了完整的 Docker Compose 配置，支持开发环境和生产环境的容器化部署。

## 配置文件说明

### 开发环境配置
- **文件**: `docker-compose.dev.yml`
- **用途**: 本地开发和调试
- **特点**: 热重载、调试模式、开发工具

### 生产环境配置
- **文件**: `docker-compose.prod.yml`
- **用途**: 生产环境部署
- **特点**: 性能优化、安全加固、监控支持

## 开发环境使用

### 1. 启动开发环境

#### 完整启动
```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

#### 单独启动服务
```bash
# 只启动数据库和缓存
docker-compose -f docker-compose.dev.yml up -d mysql redis

# 启动后端服务
docker-compose -f docker-compose.dev.yml up -d backend

# 启动前端服务
docker-compose -f docker-compose.dev.yml up -d frontend
```

### 2. 开发环境配置

#### 服务端口
- **前端**: http://localhost:3000
- **后端**: http://localhost:5000
- **MySQL**: localhost:3306
- **Redis**: localhost:6379

#### 默认配置
```yaml
# MySQL配置
MYSQL_ROOT_PASSWORD: root123
MYSQL_DATABASE: questionbank_master
MYSQL_USER: questionbank
MYSQL_PASSWORD: questionbank123

# 应用配置
FLASK_ENV: development
FLASK_DEBUG: 1
VITE_API_BASE_URL: http://localhost:5000/api/v1
```

### 3. 开发调试

#### 查看日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
```

#### 进入容器调试
```bash
# 进入后端容器
docker-compose -f docker-compose.dev.yml exec backend bash

# 进入前端容器
docker-compose -f docker-compose.dev.yml exec frontend sh

# 进入数据库容器
docker-compose -f docker-compose.dev.yml exec mysql mysql -u questionbank -p
```

#### 重启服务
```bash
# 重启特定服务
docker-compose -f docker-compose.dev.yml restart backend

# 重新构建并启动
docker-compose -f docker-compose.dev.yml up -d --build backend
```

### 4. 停止开发环境
```bash
# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.dev.yml down -v

# 停止并删除镜像
docker-compose -f docker-compose.dev.yml down --rmi all
```

## 生产环境使用

### 1. 环境配置

#### 创建环境配置文件
```bash
# 复制配置模板
cp .env.prod.example .env.prod

# 编辑配置文件
vim .env.prod
```

#### 必须配置的变量
```bash
# 版本号
VERSION=v1.0.0

# 数据库配置（使用强密码）
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_db_password

# 应用密钥（32位以上随机字符串）
SECRET_KEY=your_very_secure_secret_key_32_chars_min
JWT_SECRET_KEY=your_very_secure_jwt_secret_key_32_chars_min

# API配置
VITE_API_BASE_URL=https://your-domain.com/api/v1

# 域名配置
DOMAIN=your-domain.com
```

### 2. 启动生产环境

#### 完整部署
```bash
# 构建并启动所有服务
docker-compose -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

#### 分步部署
```bash
# 1. 启动基础服务
docker-compose -f docker-compose.prod.yml up -d mysql redis

# 2. 等待数据库启动
sleep 30

# 3. 启动应用服务
docker-compose -f docker-compose.prod.yml up -d backend frontend

# 4. 启动负载均衡
docker-compose -f docker-compose.prod.yml up -d nginx-lb
```

### 3. 生产环境配置

#### 服务端口
- **前端**: http://localhost:80, https://localhost:443
- **后端**: http://localhost:5000
- **负载均衡**: http://localhost:8080, https://localhost:8443
- **MySQL**: localhost:3306 (内部访问)
- **Redis**: localhost:6379 (内部访问)

#### 健康检查
```bash
# 检查服务健康状态
curl http://localhost:5000/api/v1/health
curl http://localhost/health

# 检查统计API
curl http://localhost:5000/api/v1/banks/public/statistics
```

### 4. 生产环境维护

#### 更新服务
```bash
# 拉取最新镜像
docker-compose -f docker-compose.prod.yml pull

# 重新启动服务
docker-compose -f docker-compose.prod.yml up -d

# 清理旧镜像
docker image prune -f
```

#### 备份数据
```bash
# 备份数据库
docker-compose -f docker-compose.prod.yml exec mysql mysqldump \
  -u root -p"${MYSQL_ROOT_PASSWORD}" \
  --single-transaction questionbank_master > backup.sql

# 备份上传文件
tar -czf uploads_backup.tar.gz uploads/
```

#### 监控服务
```bash
# 查看资源使用
docker stats

# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看系统日志
docker-compose -f docker-compose.prod.yml logs --tail=100
```

## 常用命令

### 服务管理
```bash
# 启动服务
docker-compose -f <compose-file> up -d [service]

# 停止服务
docker-compose -f <compose-file> stop [service]

# 重启服务
docker-compose -f <compose-file> restart [service]

# 删除服务
docker-compose -f <compose-file> down [service]
```

### 日志管理
```bash
# 查看实时日志
docker-compose -f <compose-file> logs -f [service]

# 查看最近日志
docker-compose -f <compose-file> logs --tail=100 [service]

# 查看特定时间日志
docker-compose -f <compose-file> logs --since="2024-01-01" [service]
```

### 数据管理
```bash
# 查看数据卷
docker volume ls

# 备份数据卷
docker run --rm -v <volume>:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# 恢复数据卷
docker run --rm -v <volume>:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
```

## 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :3000
netstat -tulpn | grep :5000

# 修改端口配置
# 编辑 docker-compose.yml 中的 ports 配置
```

#### 2. 容器启动失败
```bash
# 查看容器日志
docker-compose logs <service>

# 检查容器状态
docker-compose ps

# 重新构建容器
docker-compose up -d --build <service>
```

#### 3. 数据库连接失败
```bash
# 检查数据库容器状态
docker-compose ps mysql

# 查看数据库日志
docker-compose logs mysql

# 测试数据库连接
docker-compose exec mysql mysql -u questionbank -p
```

#### 4. 网络问题
```bash
# 查看网络配置
docker network ls
docker network inspect <network_name>

# 重建网络
docker-compose down
docker-compose up -d
```

### 性能优化

#### 1. 资源限制
```yaml
# 在 docker-compose.yml 中添加资源限制
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

#### 2. 缓存优化
```bash
# 清理构建缓存
docker builder prune

# 清理镜像缓存
docker image prune -a

# 清理系统缓存
docker system prune -a
```

## 最佳实践

### 1. 开发环境
- 使用数据卷挂载源代码，支持热重载
- 启用调试模式，便于问题排查
- 使用开发专用的环境变量配置

### 2. 生产环境
- 使用环境变量文件管理配置
- 启用健康检查和重启策略
- 配置日志轮转和监控

### 3. 安全配置
- 使用强密码和随机密钥
- 限制容器权限和网络访问
- 定期更新镜像和依赖

### 4. 备份策略
- 定期备份数据库和文件
- 测试备份恢复流程
- 保留多个备份版本

## 总结

Docker Compose 提供了：
- ✅ **统一环境**: 开发和生产环境一致性
- ✅ **简化部署**: 一条命令启动所有服务
- ✅ **服务编排**: 自动处理服务依赖关系
- ✅ **扩展性**: 支持服务扩容和负载均衡
- ✅ **维护性**: 便于服务更新和故障排除

推荐在所有环境中使用 Docker Compose 进行部署和管理。
