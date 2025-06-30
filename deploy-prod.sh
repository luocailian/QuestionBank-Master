#!/bin/bash

# QuestionBank Master 一键生产部署脚本
# 自动化部署到生产环境

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 显示横幅
show_banner() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              QuestionBank Master 生产部署工具                ║
║                                                              ║
║              支持零停机部署、自动备份、版本管理                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo ""
}

# 检查系统要求
check_requirements() {
    log "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装，请先安装 Docker"
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装，请先安装 Docker Compose"
    fi
    
    # 检查系统资源
    local total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
    if [ "$total_mem" -lt 2 ]; then
        warning "系统内存少于2GB，可能影响性能"
    fi
    
    local disk_space=$(df / | awk 'NR==2{print $4}')
    if [ "$disk_space" -lt 10485760 ]; then  # 10GB in KB
        warning "磁盘可用空间少于10GB，可能影响运行"
    fi
    
    success "系统要求检查通过"
}

# 初始化环境
init_environment() {
    log "初始化部署环境..."
    
    # 创建必要目录
    mkdir -p logs backups uploads
    mkdir -p nginx/{conf.d,ssl} mysql/conf.d redis
    
    # 设置权限
    chmod +x scripts/*.sh
    
    # 复制环境配置文件
    if [ ! -f ".env.prod" ]; then
        if [ -f ".env.prod.example" ]; then
            cp .env.prod.example .env.prod
            warning "已创建 .env.prod 文件，请编辑其中的配置"
            echo "请编辑 .env.prod 文件中的配置，然后重新运行部署脚本"
            echo "主要需要配置的项目："
            echo "  - MYSQL_ROOT_PASSWORD: MySQL root密码"
            echo "  - MYSQL_PASSWORD: 应用数据库密码"
            echo "  - SECRET_KEY: 应用密钥"
            echo "  - JWT_SECRET_KEY: JWT密钥"
            echo "  - VITE_API_BASE_URL: API基础URL"
            exit 1
        else
            error "找不到环境配置模板文件"
        fi
    fi
    
    success "环境初始化完成"
}

# 配置SSL证书
setup_ssl() {
    log "配置SSL证书..."
    
    local domain=${DOMAIN:-localhost}
    local ssl_dir="nginx/ssl"
    
    if [ ! -f "$ssl_dir/cert.pem" ] || [ ! -f "$ssl_dir/key.pem" ]; then
        log "生成自签名SSL证书..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$ssl_dir/key.pem" \
            -out "$ssl_dir/cert.pem" \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=$domain" \
            2>/dev/null
        
        warning "已生成自签名SSL证书，生产环境建议使用正式证书"
    fi
    
    success "SSL证书配置完成"
}

# 配置数据库
setup_database() {
    log "配置数据库..."
    
    # 创建MySQL配置文件
    cat > mysql/conf.d/my.cnf << 'EOF'
[mysqld]
# 性能优化
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# 连接数
max_connections = 200
max_connect_errors = 10000

# 查询缓存
query_cache_type = 1
query_cache_size = 32M

# 慢查询日志
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# 二进制日志
log-bin = mysql-bin
binlog_format = ROW
expire_logs_days = 7
EOF
    
    success "数据库配置完成"
}

# 配置Redis
setup_redis() {
    log "配置Redis..."
    
    # 创建Redis配置文件
    cat > redis/redis.conf << 'EOF'
# 内存配置
maxmemory 256mb
maxmemory-policy allkeys-lru

# 持久化
save 900 1
save 300 10
save 60 10000

# 安全
protected-mode yes
port 6379

# 日志
loglevel notice
logfile /var/log/redis/redis.log

# 网络
tcp-keepalive 300
timeout 0
EOF
    
    success "Redis配置完成"
}

# 部署应用
deploy_application() {
    local version=${1:-$(date +%Y%m%d_%H%M%S)}
    
    log "部署应用版本: $version"
    
    # 加载环境变量
    source .env.prod
    export VERSION="$version"
    
    # 构建镜像
    log "构建Docker镜像..."
    docker-compose -f docker-compose.prod.yml build
    
    # 启动服务
    log "启动服务..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 60
    
    # 健康检查
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:5000/api/v1/health >/dev/null 2>&1; then
            success "应用部署成功"
            return 0
        fi
        
        log "健康检查尝试 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    error "应用部署失败，请检查日志"
}

# 设置定时任务
setup_cron() {
    log "设置定时任务..."
    
    # 创建cron任务文件
    cat > /tmp/questionbank_cron << EOF
# QuestionBank Master 定时任务

# 每天凌晨2点执行数据备份
0 2 * * * $PROJECT_DIR/scripts/backup.sh >> $PROJECT_DIR/logs/backup.log 2>&1

# 每5分钟执行系统监控
*/5 * * * * $PROJECT_DIR/scripts/monitor.sh >> $PROJECT_DIR/logs/monitor.log 2>&1

# 每周日凌晨3点清理旧日志
0 3 * * 0 find $PROJECT_DIR/logs -name "*.log" -mtime +30 -delete

# 每月1号凌晨4点清理旧备份
0 4 1 * * find $PROJECT_DIR/backups -name "*.gz" -mtime +90 -delete
EOF
    
    # 安装cron任务
    crontab /tmp/questionbank_cron
    rm /tmp/questionbank_cron
    
    success "定时任务设置完成"
}

# 显示部署信息
show_deployment_info() {
    local domain=${DOMAIN:-localhost}
    
    success "QuestionBank Master 部署完成！"
    echo ""
    echo "访问信息："
    echo "  前台地址: http://$domain"
    echo "  管理后台: http://$domain/admin"
    echo "  API文档: http://$domain:5000/api/v1/"
    echo ""
    echo "管理命令："
    echo "  查看状态: ./scripts/version-manager.sh status"
    echo "  查看日志: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  执行备份: ./scripts/backup.sh"
    echo "  系统监控: ./scripts/monitor.sh"
    echo ""
    echo "重要文件："
    echo "  环境配置: .env.prod"
    echo "  部署配置: docker-compose.prod.yml"
    echo "  日志目录: logs/"
    echo "  备份目录: backups/"
    echo ""
}

# 主函数
main() {
    local version=${1:-$(date +%Y%m%d_%H%M%S)}
    
    show_banner
    
    log "开始 QuestionBank Master 生产环境部署"
    log "部署版本: $version"
    echo ""
    
    # 确认部署
    echo -n "确认开始部署? (y/N): "
    read -r confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log "部署已取消"
        exit 0
    fi
    
    # 执行部署步骤
    check_requirements
    init_environment
    setup_ssl
    setup_database
    setup_redis
    deploy_application "$version"
    setup_cron
    
    echo ""
    show_deployment_info
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
