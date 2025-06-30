#!/bin/bash

# QuestionBank Master 系统监控脚本
# 监控服务状态、资源使用、性能指标

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
LOG_FILE="${PROJECT_DIR}/logs/monitor.log"
ALERT_FILE="${PROJECT_DIR}/logs/alerts.log"

# 阈值配置
CPU_THRESHOLD=80
MEMORY_THRESHOLD=80
DISK_THRESHOLD=85
RESPONSE_TIME_THRESHOLD=5000  # 毫秒

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

alert() {
    echo -e "${RED}[ALERT]${NC} $1" | tee -a "$ALERT_FILE"
    log "ALERT: $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1" | tee -a "$LOG_FILE"
}

# 检查Docker容器状态
check_containers() {
    log "检查容器状态..."
    
    local containers=("questionbank_mysql" "questionbank_redis" "questionbank_backend" "questionbank_frontend")
    local failed_containers=()
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container.*Up"; then
            success "容器 $container 运行正常"
        else
            alert "容器 $container 未运行或状态异常"
            failed_containers+=("$container")
        fi
    done
    
    if [ ${#failed_containers[@]} -gt 0 ]; then
        return 1
    fi
    
    return 0
}

# 检查服务健康状态
check_health() {
    log "检查服务健康状态..."
    
    # 检查后端API
    local api_response=$(curl -s -w "%{http_code}:%{time_total}" http://localhost:5000/api/v1/health 2>/dev/null || echo "000:0")
    local api_code=$(echo "$api_response" | cut -d: -f1)
    local api_time=$(echo "$api_response" | cut -d: -f2)
    local api_time_ms=$(echo "$api_time * 1000" | bc -l | cut -d. -f1)
    
    if [ "$api_code" = "200" ]; then
        if [ "$api_time_ms" -lt "$RESPONSE_TIME_THRESHOLD" ]; then
            success "后端API健康 (响应时间: ${api_time_ms}ms)"
        else
            warning "后端API响应时间过长: ${api_time_ms}ms"
        fi
    else
        alert "后端API健康检查失败，状态码: $api_code"
        return 1
    fi
    
    # 检查前端
    local frontend_response=$(curl -s -w "%{http_code}" http://localhost/health 2>/dev/null || echo "000")
    if [ "$frontend_response" = "200" ]; then
        success "前端服务健康"
    else
        alert "前端服务健康检查失败，状态码: $frontend_response"
        return 1
    fi
    
    return 0
}

# 检查资源使用情况
check_resources() {
    log "检查系统资源使用情况..."
    
    # CPU使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    cpu_usage=${cpu_usage%.*}  # 去掉小数部分
    
    if [ "$cpu_usage" -gt "$CPU_THRESHOLD" ]; then
        alert "CPU使用率过高: ${cpu_usage}%"
    else
        success "CPU使用率正常: ${cpu_usage}%"
    fi
    
    # 内存使用率
    local memory_info=$(free | grep Mem)
    local total_mem=$(echo "$memory_info" | awk '{print $2}')
    local used_mem=$(echo "$memory_info" | awk '{print $3}')
    local memory_usage=$((used_mem * 100 / total_mem))
    
    if [ "$memory_usage" -gt "$MEMORY_THRESHOLD" ]; then
        alert "内存使用率过高: ${memory_usage}%"
    else
        success "内存使用率正常: ${memory_usage}%"
    fi
    
    # 磁盘使用率
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        alert "磁盘使用率过高: ${disk_usage}%"
    else
        success "磁盘使用率正常: ${disk_usage}%"
    fi
}

# 检查数据库连接
check_database() {
    log "检查数据库连接..."
    
    local db_check=$(docker exec questionbank_mysql mysql -u questionbank -p"${MYSQL_PASSWORD}" -e "SELECT 1" questionbank_master 2>/dev/null || echo "failed")
    
    if [ "$db_check" != "failed" ]; then
        success "数据库连接正常"
        
        # 检查数据库大小
        local db_size=$(docker exec questionbank_mysql mysql -u questionbank -p"${MYSQL_PASSWORD}" -e "
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB' 
            FROM information_schema.tables 
            WHERE table_schema='questionbank_master';" questionbank_master 2>/dev/null | tail -1)
        
        log "数据库大小: ${db_size}MB"
    else
        alert "数据库连接失败"
        return 1
    fi
    
    return 0
}

# 检查Redis连接
check_redis() {
    log "检查Redis连接..."
    
    local redis_check=$(docker exec questionbank_redis redis-cli ping 2>/dev/null || echo "failed")
    
    if [ "$redis_check" = "PONG" ]; then
        success "Redis连接正常"
        
        # 检查Redis内存使用
        local redis_memory=$(docker exec questionbank_redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        log "Redis内存使用: $redis_memory"
    else
        alert "Redis连接失败"
        return 1
    fi
    
    return 0
}

# 检查日志错误
check_logs() {
    log "检查应用日志错误..."
    
    local error_count=0
    
    # 检查后端错误日志
    if [ -f "${PROJECT_DIR}/logs/error.log" ]; then
        local recent_errors=$(tail -100 "${PROJECT_DIR}/logs/error.log" | grep -c "ERROR" || echo "0")
        if [ "$recent_errors" -gt 10 ]; then
            warning "后端错误日志中发现 $recent_errors 个错误"
            error_count=$((error_count + recent_errors))
        fi
    fi
    
    # 检查Nginx错误日志
    if [ -f "${PROJECT_DIR}/logs/nginx/error.log" ]; then
        local nginx_errors=$(tail -100 "${PROJECT_DIR}/logs/nginx/error.log" | grep -c "error" || echo "0")
        if [ "$nginx_errors" -gt 5 ]; then
            warning "Nginx错误日志中发现 $nginx_errors 个错误"
            error_count=$((error_count + nginx_errors))
        fi
    fi
    
    if [ "$error_count" -eq 0 ]; then
        success "日志检查正常"
    fi
    
    return 0
}

# 性能测试
performance_test() {
    log "执行性能测试..."
    
    # 测试API响应时间
    local endpoints=("/api/v1/health" "/api/v1/banks/public/statistics" "/api/v1/banks")
    
    for endpoint in "${endpoints[@]}"; do
        local response_time=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:5000$endpoint" 2>/dev/null || echo "0")
        local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
        
        if [ "$response_time_ms" -lt "$RESPONSE_TIME_THRESHOLD" ]; then
            success "API $endpoint 响应时间: ${response_time_ms}ms"
        else
            warning "API $endpoint 响应时间过长: ${response_time_ms}ms"
        fi
    done
}

# 生成监控报告
generate_report() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local report_file="${PROJECT_DIR}/logs/monitor_report_$(date +%Y%m%d).log"
    
    {
        echo "========================================="
        echo "QuestionBank Master 监控报告"
        echo "时间: $timestamp"
        echo "========================================="
        echo ""
        
        # 容器状态
        echo "容器状态:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep questionbank
        echo ""
        
        # 资源使用
        echo "资源使用:"
        echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
        echo "内存: $(free -h | grep Mem | awk '{print $3"/"$2}')"
        echo "磁盘: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
        echo ""
        
        # 网络连接
        echo "网络连接:"
        netstat -tuln | grep -E ":(80|443|3000|5000|3306|6379)"
        echo ""
        
    } >> "$report_file"
    
    log "监控报告已生成: $report_file"
}

# 发送告警
send_alert() {
    local message=$1
    
    # 这里可以集成各种告警方式
    log "发送告警: $message"
    
    # 示例：发送邮件告警
    # if command -v mail &> /dev/null; then
    #     echo "$message" | mail -s "QuestionBank Alert" admin@yourdomain.com
    # fi
    
    # 示例：发送Slack通知
    # if [ -n "$SLACK_WEBHOOK_URL" ]; then
    #     curl -X POST -H 'Content-type: application/json' \
    #         --data "{\"text\":\"$message\"}" \
    #         "$SLACK_WEBHOOK_URL"
    # fi
}

# 主监控函数
main() {
    log "开始系统监控检查"
    
    # 加载环境变量
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    fi
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$ALERT_FILE")"
    
    local check_results=()
    local failed_checks=()
    
    # 执行各项检查
    if check_containers; then
        check_results+=("containers:OK")
    else
        check_results+=("containers:FAILED")
        failed_checks+=("containers")
    fi
    
    if check_health; then
        check_results+=("health:OK")
    else
        check_results+=("health:FAILED")
        failed_checks+=("health")
    fi
    
    check_resources
    check_results+=("resources:OK")
    
    if check_database; then
        check_results+=("database:OK")
    else
        check_results+=("database:FAILED")
        failed_checks+=("database")
    fi
    
    if check_redis; then
        check_results+=("redis:OK")
    else
        check_results+=("redis:FAILED")
        failed_checks+=("redis")
    fi
    
    check_logs
    check_results+=("logs:OK")
    
    performance_test
    check_results+=("performance:OK")
    
    # 生成报告
    generate_report
    
    # 检查是否有失败项
    if [ ${#failed_checks[@]} -gt 0 ]; then
        local alert_message="QuestionBank Master 监控发现问题: ${failed_checks[*]}"
        alert "$alert_message"
        send_alert "$alert_message"
        exit 1
    else
        success "所有监控检查通过"
        exit 0
    fi
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
