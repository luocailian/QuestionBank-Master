#!/bin/bash

# QuestionBank Master 版本管理脚本
# 支持版本发布、回滚、查看历史等功能

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
VERSION_FILE="${PROJECT_DIR}/VERSION"
LOG_FILE="${PROJECT_DIR}/logs/version.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 显示帮助信息
show_help() {
    cat << EOF
QuestionBank Master 版本管理工具

用法: $0 <命令> [选项]

命令:
  list                    列出所有可用版本
  current                 显示当前版本
  deploy <version>        部署指定版本
  rollback [version]      回滚到指定版本（默认回滚到上一版本）
  tag <version> [message] 创建新版本标签
  history                 显示版本历史
  cleanup                 清理旧版本镜像
  status                  显示当前部署状态

选项:
  -h, --help             显示此帮助信息
  -v, --verbose          详细输出
  -f, --force            强制执行（跳过确认）

示例:
  $0 list                           # 列出所有版本
  $0 deploy v1.2.0                  # 部署v1.2.0版本
  $0 rollback                       # 回滚到上一版本
  $0 rollback v1.1.0                # 回滚到v1.1.0版本
  $0 tag v1.3.0 "新增用户管理功能"    # 创建新版本标签

EOF
}

# 获取当前版本
get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        echo "unknown"
    fi
}

# 设置当前版本
set_current_version() {
    local version=$1
    echo "$version" > "$VERSION_FILE"
    log "当前版本设置为: $version"
}

# 列出所有可用版本
list_versions() {
    log "可用的版本列表:"
    echo ""
    echo "Docker镜像版本:"
    echo "后端镜像:"
    docker images questionbank/backend --format "table {{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | head -10
    echo ""
    echo "前端镜像:"
    docker images questionbank/frontend --format "table {{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | head -10
    echo ""
    
    # 显示Git标签（如果是Git仓库）
    if [ -d "${PROJECT_DIR}/.git" ]; then
        echo "Git标签:"
        git tag -l --sort=-version:refname | head -10
        echo ""
    fi
}

# 显示当前版本信息
show_current() {
    local current_version=$(get_current_version)
    log "当前版本: $current_version"
    
    # 显示容器状态
    echo ""
    echo "容器状态:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep questionbank
    echo ""
    
    # 显示镜像信息
    echo "镜像信息:"
    docker images | grep questionbank | head -5
}

# 验证版本是否存在
validate_version() {
    local version=$1
    
    # 检查后端镜像是否存在
    if ! docker images questionbank/backend:$version --format "{{.Tag}}" | grep -q "^$version$"; then
        error "后端镜像版本 $version 不存在"
    fi
    
    # 检查前端镜像是否存在
    if ! docker images questionbank/frontend:$version --format "{{.Tag}}" | grep -q "^$version$"; then
        error "前端镜像版本 $version 不存在"
    fi
    
    success "版本 $version 验证通过"
}

# 部署指定版本
deploy_version() {
    local version=$1
    local force=${2:-false}
    
    if [ -z "$version" ]; then
        error "请指定要部署的版本"
    fi
    
    log "准备部署版本: $version"
    
    # 验证版本
    validate_version "$version"
    
    # 确认部署
    if [ "$force" != "true" ]; then
        echo -n "确认部署版本 $version? (y/N): "
        read -r confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            log "部署已取消"
            exit 0
        fi
    fi
    
    # 记录当前版本（用于回滚）
    local current_version=$(get_current_version)
    if [ "$current_version" != "unknown" ]; then
        echo "$current_version" > "${PROJECT_DIR}/.last_version"
    fi
    
    # 执行部署
    log "开始部署版本 $version..."
    
    # 设置环境变量
    export VERSION="$version"
    
    # 加载环境配置
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    fi
    
    # 停止当前服务
    log "停止当前服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    # 启动新版本
    log "启动新版本服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 30
    
    # 健康检查
    if health_check; then
        set_current_version "$version"
        success "版本 $version 部署成功"
        
        # 记录部署历史
        echo "$(date +'%Y-%m-%d %H:%M:%S') DEPLOY $version" >> "${PROJECT_DIR}/logs/deploy_history.log"
    else
        error "版本 $version 部署失败，请检查日志"
    fi
}

# 回滚到指定版本
rollback_version() {
    local target_version=$1
    
    # 如果没有指定版本，使用上一个版本
    if [ -z "$target_version" ]; then
        if [ -f "${PROJECT_DIR}/.last_version" ]; then
            target_version=$(cat "${PROJECT_DIR}/.last_version")
        else
            error "没有找到可回滚的版本"
        fi
    fi
    
    log "准备回滚到版本: $target_version"
    
    # 验证版本
    validate_version "$target_version"
    
    # 确认回滚
    echo -n "确认回滚到版本 $target_version? (y/N): "
    read -r confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log "回滚已取消"
        exit 0
    fi
    
    # 执行回滚
    log "开始回滚到版本 $target_version..."
    
    # 记录当前版本
    local current_version=$(get_current_version)
    
    # 部署目标版本
    deploy_version "$target_version" true
    
    # 记录回滚历史
    echo "$(date +'%Y-%m-%d %H:%M:%S') ROLLBACK from $current_version to $target_version" >> "${PROJECT_DIR}/logs/deploy_history.log"
    
    success "回滚到版本 $target_version 完成"
}

# 创建版本标签
create_tag() {
    local version=$1
    local message=$2
    
    if [ -z "$version" ]; then
        error "请指定版本号"
    fi
    
    # 验证版本号格式
    if [[ ! $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        error "版本号格式错误，应为 vX.Y.Z 格式"
    fi
    
    log "创建版本标签: $version"
    
    # 如果是Git仓库，创建Git标签
    if [ -d "${PROJECT_DIR}/.git" ]; then
        if [ -n "$message" ]; then
            git tag -a "$version" -m "$message"
        else
            git tag "$version"
        fi
        success "Git标签 $version 创建成功"
    fi
    
    # 构建并标记Docker镜像
    log "构建Docker镜像..."
    
    # 构建后端镜像
    docker build -f backend/Dockerfile.prod -t "questionbank/backend:$version" backend/
    docker tag "questionbank/backend:$version" "questionbank/backend:latest"
    
    # 构建前端镜像
    docker build -f frontend/Dockerfile.prod -t "questionbank/frontend:$version" frontend/
    docker tag "questionbank/frontend:$version" "questionbank/frontend:latest"
    
    success "Docker镜像标签 $version 创建成功"
    
    # 记录标签历史
    echo "$(date +'%Y-%m-%d %H:%M:%S') TAG $version $message" >> "${PROJECT_DIR}/logs/deploy_history.log"
}

# 显示版本历史
show_history() {
    log "版本部署历史:"
    echo ""
    
    if [ -f "${PROJECT_DIR}/logs/deploy_history.log" ]; then
        tail -20 "${PROJECT_DIR}/logs/deploy_history.log"
    else
        warning "没有找到部署历史记录"
    fi
    
    echo ""
    
    # 显示Git提交历史（如果是Git仓库）
    if [ -d "${PROJECT_DIR}/.git" ]; then
        echo "最近的Git提交:"
        git log --oneline -10
    fi
}

# 清理旧版本
cleanup_versions() {
    log "清理旧版本镜像..."
    
    # 保留最近5个版本
    local keep_count=5
    
    # 清理后端镜像
    local backend_images=$(docker images questionbank/backend --format "{{.Tag}}" | grep -v latest | tail -n +$((keep_count + 1)))
    if [ -n "$backend_images" ]; then
        echo "$backend_images" | xargs -I {} docker rmi questionbank/backend:{} 2>/dev/null || true
    fi
    
    # 清理前端镜像
    local frontend_images=$(docker images questionbank/frontend --format "{{.Tag}}" | grep -v latest | tail -n +$((keep_count + 1)))
    if [ -n "$frontend_images" ]; then
        echo "$frontend_images" | xargs -I {} docker rmi questionbank/frontend:{} 2>/dev/null || true
    fi
    
    # 清理悬空镜像
    docker image prune -f
    
    success "旧版本清理完成"
}

# 健康检查
health_check() {
    local max_attempts=30
    local attempt=1
    
    log "执行健康检查..."
    
    while [ $attempt -le $max_attempts ]; do
        # 检查后端API
        if curl -s -f http://localhost:5000/api/v1/health >/dev/null 2>&1; then
            # 检查前端
            if curl -s -f http://localhost/health >/dev/null 2>&1; then
                success "健康检查通过"
                return 0
            fi
        fi
        
        log "健康检查尝试 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    error "健康检查失败"
    return 1
}

# 显示部署状态
show_status() {
    log "当前部署状态:"
    echo ""
    
    # 显示当前版本
    show_current
    
    # 显示服务状态
    echo ""
    echo "服务健康状态:"
    
    # 检查各个服务
    local services=("http://localhost:5000/api/v1/health" "http://localhost/health")
    for service in "${services[@]}"; do
        if curl -s -f "$service" >/dev/null 2>&1; then
            echo "✓ $service - 健康"
        else
            echo "✗ $service - 异常"
        fi
    done
    
    echo ""
    
    # 显示资源使用
    echo "资源使用情况:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep questionbank
}

# 主函数
main() {
    local command=$1
    shift
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    case $command in
        list)
            list_versions
            ;;
        current)
            show_current
            ;;
        deploy)
            deploy_version "$@"
            ;;
        rollback)
            rollback_version "$@"
            ;;
        tag)
            create_tag "$@"
            ;;
        history)
            show_history
            ;;
        cleanup)
            cleanup_versions
            ;;
        status)
            show_status
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            echo "未知命令: $command"
            echo "使用 '$0 --help' 查看帮助信息"
            exit 1
            ;;
    esac
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
