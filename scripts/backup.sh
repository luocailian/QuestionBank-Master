#!/bin/bash

# QuestionBank Master 自动备份脚本
# 支持本地备份和云存储备份

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${PROJECT_DIR}/logs/backup.log"

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

# 创建备份目录
create_backup_dirs() {
    mkdir -p "$BACKUP_DIR"/{database,uploads,logs}
    mkdir -p "$(dirname "$LOG_FILE")"
}

# 数据库备份
backup_database() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/database/db_backup_${timestamp}.sql"
    
    log "开始数据库备份..."
    
    # 检查MySQL容器是否运行
    if ! docker ps | grep -q questionbank_mysql; then
        error "MySQL容器未运行"
    fi
    
    # 执行备份
    docker exec questionbank_mysql mysqldump \
        -u root -p"${MYSQL_ROOT_PASSWORD}" \
        --single-transaction \
        --routines \
        --triggers \
        --add-drop-database \
        --databases questionbank_master > "$backup_file"
    
    if [ $? -eq 0 ]; then
        # 压缩备份文件
        gzip "$backup_file"
        success "数据库备份完成: ${backup_file}.gz"
        echo "${backup_file}.gz"
    else
        error "数据库备份失败"
    fi
}

# 文件备份
backup_uploads() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/uploads/uploads_backup_${timestamp}.tar.gz"
    
    log "开始文件备份..."
    
    if [ -d "${PROJECT_DIR}/uploads" ]; then
        tar -czf "$backup_file" -C "$PROJECT_DIR" uploads/
        success "文件备份完成: $backup_file"
        echo "$backup_file"
    else
        warning "uploads目录不存在，跳过文件备份"
    fi
}

# 日志备份
backup_logs() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/logs/logs_backup_${timestamp}.tar.gz"
    
    log "开始日志备份..."
    
    if [ -d "${PROJECT_DIR}/logs" ]; then
        tar -czf "$backup_file" -C "$PROJECT_DIR" logs/
        success "日志备份完成: $backup_file"
        echo "$backup_file"
    else
        warning "logs目录不存在，跳过日志备份"
    fi
}

# 上传到云存储（AWS S3）
upload_to_s3() {
    local file_path=$1
    local s3_path="s3://${BACKUP_S3_BUCKET}/questionbank-backups/$(basename "$file_path")"
    
    if [ -n "$BACKUP_S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
        log "上传备份到S3: $s3_path"
        
        if command -v aws &> /dev/null; then
            aws s3 cp "$file_path" "$s3_path"
            success "S3上传完成: $s3_path"
        else
            warning "AWS CLI未安装，跳过S3上传"
        fi
    fi
}

# 清理旧备份
cleanup_old_backups() {
    local retention_days=${BACKUP_RETENTION_DAYS:-30}
    
    log "清理${retention_days}天前的备份文件..."
    
    # 清理本地备份
    find "$BACKUP_DIR" -type f -name "*.gz" -mtime +$retention_days -delete
    find "$BACKUP_DIR" -type f -name "*.tar.gz" -mtime +$retention_days -delete
    
    # 清理S3备份（如果配置了）
    if [ -n "$BACKUP_S3_BUCKET" ] && command -v aws &> /dev/null; then
        local cutoff_date=$(date -d "${retention_days} days ago" +%Y-%m-%d)
        aws s3 ls "s3://${BACKUP_S3_BUCKET}/questionbank-backups/" | \
        awk '$1 < "'$cutoff_date'" {print $4}' | \
        xargs -I {} aws s3 rm "s3://${BACKUP_S3_BUCKET}/questionbank-backups/{}"
    fi
    
    success "旧备份清理完成"
}

# 验证备份完整性
verify_backup() {
    local backup_file=$1
    
    log "验证备份文件完整性: $(basename "$backup_file")"
    
    if [ "${backup_file##*.}" = "gz" ]; then
        if gzip -t "$backup_file"; then
            success "备份文件完整性验证通过"
            return 0
        else
            error "备份文件损坏: $backup_file"
            return 1
        fi
    fi
    
    return 0
}

# 发送通知
send_notification() {
    local status=$1
    local message=$2
    
    # 这里可以集成邮件、Slack、钉钉等通知方式
    log "备份状态: $status - $message"
    
    # 示例：发送邮件通知（需要配置邮件服务）
    # if command -v mail &> /dev/null; then
    #     echo "$message" | mail -s "QuestionBank Backup $status" admin@yourdomain.com
    # fi
}

# 主备份函数
main() {
    log "开始执行自动备份任务"
    
    # 加载环境变量
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    fi
    
    # 创建备份目录
    create_backup_dirs
    
    local backup_files=()
    local failed_backups=()
    
    # 执行各项备份
    if db_backup=$(backup_database); then
        backup_files+=("$db_backup")
        verify_backup "$db_backup" && upload_to_s3 "$db_backup"
    else
        failed_backups+=("database")
    fi
    
    if uploads_backup=$(backup_uploads); then
        backup_files+=("$uploads_backup")
        verify_backup "$uploads_backup" && upload_to_s3 "$uploads_backup"
    fi
    
    if logs_backup=$(backup_logs); then
        backup_files+=("$logs_backup")
        verify_backup "$logs_backup" && upload_to_s3 "$logs_backup"
    fi
    
    # 清理旧备份
    cleanup_old_backups
    
    # 生成备份报告
    local total_backups=${#backup_files[@]}
    local failed_count=${#failed_backups[@]}
    
    if [ $failed_count -eq 0 ]; then
        success "备份任务完成，共创建 $total_backups 个备份文件"
        send_notification "SUCCESS" "备份任务成功完成，共创建 $total_backups 个备份文件"
    else
        error "备份任务部分失败，失败项目: ${failed_backups[*]}"
        send_notification "FAILED" "备份任务部分失败，失败项目: ${failed_backups[*]}"
    fi
    
    log "备份任务结束"
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
