#!/bin/bash

# QuestionBank Master 零停机部署脚本
# 使用蓝绿部署策略确保服务不中断

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${PROJECT_DIR}/logs/deploy.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# 检查必要文件
check_prerequisites() {
    log "检查部署前置条件..."
    
    if [ ! -f "$ENV_FILE" ]; then
        error "环境配置文件 .env.prod 不存在，请先创建配置文件"
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker Compose 配置文件不存在"
    fi
    
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装"
    fi
    
    success "前置条件检查通过"
}

# 创建备份
create_backup() {
    log "创建数据备份..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # 备份数据库
    docker exec questionbank_mysql mysqldump \
        -u root -p"${MYSQL_ROOT_PASSWORD}" \
        --single-transaction \
        --routines \
        --triggers \
        questionbank_master > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        success "数据库备份完成: $BACKUP_FILE"
    else
        error "数据库备份失败"
    fi
    
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    success "备份文件已压缩"
}

# 构建新镜像
build_images() {
    local version=$1
    log "构建版本 $version 的镜像..."
    
    # 构建后端镜像
    log "构建后端镜像..."
    docker build -f backend/Dockerfile.prod -t "questionbank/backend:$version" backend/
    
    # 构建前端镜像
    log "构建前端镜像..."
    docker build -f frontend/Dockerfile.prod \
        --build-arg VITE_API_BASE_URL="$VITE_API_BASE_URL" \
        -t "questionbank/frontend:$version" frontend/
    
    success "镜像构建完成"
}

# 健康检查
health_check() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    log "等待 $service 服务健康检查..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" | grep -q "healthy"; then
            success "$service 服务健康检查通过"
            return 0
        fi
        
        log "健康检查尝试 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    error "$service 服务健康检查失败"
}

# 蓝绿部署
blue_green_deploy() {
    local version=$1
    log "开始蓝绿部署，版本: $version"
    
    # 设置环境变量
    export VERSION="$version"
    
    # 启动新版本服务（绿色环境）
    log "启动绿色环境..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps backend frontend
    
    # 等待服务健康
    health_check "backend"
    health_check "frontend"
    
    # 更新负载均衡器配置，切换流量
    log "切换流量到新版本..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart nginx-lb
    
    # 等待一段时间确保服务稳定
    log "等待服务稳定..."
    sleep 30
    
    # 验证新版本
    if verify_deployment; then
        success "新版本部署成功，开始清理旧版本"
        cleanup_old_images "$version"
    else
        error "新版本验证失败，开始回滚"
        rollback
    fi
}

# 验证部署
verify_deployment() {
    log "验证部署状态..."
    
    # 检查API健康状态
    local api_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/health)
    if [ "$api_health" != "200" ]; then
        error "API健康检查失败，状态码: $api_health"
        return 1
    fi
    
    # 检查前端页面
    local frontend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)
    if [ "$frontend_health" != "200" ]; then
        error "前端健康检查失败，状态码: $frontend_health"
        return 1
    fi
    
    success "部署验证通过"
    return 0
}

# 回滚
rollback() {
    log "开始回滚到上一个版本..."
    
    # 获取上一个版本的镜像
    local last_version=$(docker images questionbank/backend --format "table {{.Tag}}" | grep -v TAG | grep -v latest | head -2 | tail -1)
    
    if [ -z "$last_version" ]; then
        error "找不到可回滚的版本"
    fi
    
    log "回滚到版本: $last_version"
    export VERSION="$last_version"
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps backend frontend
    
    health_check "backend"
    health_check "frontend"
    
    success "回滚完成"
}

# 清理旧镜像
cleanup_old_images() {
    local current_version=$1
    log "清理旧版本镜像..."
    
    # 保留最近3个版本
    docker images questionbank/backend --format "table {{.Tag}}" | grep -v TAG | grep -v latest | grep -v "$current_version" | tail -n +4 | xargs -r docker rmi questionbank/backend: 2>/dev/null || true
    docker images questionbank/frontend --format "table {{.Tag}}" | grep -v TAG | grep -v latest | grep -v "$current_version" | tail -n +4 | xargs -r docker rmi questionbank/frontend: 2>/dev/null || true
    
    success "旧镜像清理完成"
}

# 主函数
main() {
    local version=${1:-$(date +%Y%m%d_%H%M%S)}
    
    log "开始部署 QuestionBank Master 版本: $version"
    
    # 加载环境变量
    source "$ENV_FILE"
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 执行部署步骤
    check_prerequisites
    create_backup
    build_images "$version"
    blue_green_deploy "$version"
    
    success "部署完成！版本: $version"
    log "访问地址: http://localhost"
    log "管理后台: http://localhost/admin"
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
