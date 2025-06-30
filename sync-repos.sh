#!/bin/bash

# QuestionBank Master 双平台同步脚本
# 同时推送到GitHub和Gitee

set -e

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

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查Git状态
check_git_status() {
    log "检查Git状态..."
    
    if [ ! -d ".git" ]; then
        error "当前目录不是Git仓库"
    fi
    
    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        warning "检测到未提交的更改"
        echo "未提交的文件："
        git status --porcelain
        echo ""
        read -p "是否继续同步？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "同步已取消"
            exit 0
        fi
    fi
    
    success "Git状态检查通过"
}

# 检查远程仓库
check_remotes() {
    log "检查远程仓库配置..."
    
    if ! git remote | grep -q "origin"; then
        error "未找到origin远程仓库（GitHub）"
    fi
    
    if ! git remote | grep -q "gitee"; then
        warning "未找到gitee远程仓库，正在添加..."
        git remote add gitee https://gitee.com/luo-cailian/question-bank-master.git
        success "Gitee远程仓库已添加"
    fi
    
    echo "当前远程仓库："
    git remote -v
    echo ""
}

# 同步到GitHub
sync_to_github() {
    log "同步到GitHub..."
    
    if git push origin main; then
        success "GitHub同步成功"
    else
        error "GitHub同步失败"
    fi
}

# 同步到Gitee
sync_to_gitee() {
    log "同步到Gitee..."

    # 检查Gitee默认分支
    local gitee_default_branch=$(git ls-remote --symref gitee HEAD 2>/dev/null | grep "^ref:" | cut -d'/' -f3 || echo "master")

    if [ "$gitee_default_branch" = "master" ]; then
        log "Gitee默认分支为master，推送main到master分支"
        if git push gitee main:master; then
            success "Gitee同步成功 (main -> master)"
        else
            warning "Gitee同步失败，可能需要身份验证"
            echo ""
            echo "请手动执行以下命令完成Gitee同步："
            echo "git push gitee main:master  # 推送到master分支（Gitee默认）"
            echo "git push gitee main:main    # 推送到main分支（保持一致）"
            echo ""
            echo "或者使用Gitee网页导入功能："
            echo "https://gitee.com/luo-cailian/question-bank-master"
        fi
    else
        log "Gitee默认分支为main，直接推送"
        if git push gitee main; then
            success "Gitee同步成功 (main -> main)"
        else
            warning "Gitee同步失败，可能需要身份验证"
            echo ""
            echo "请手动执行以下命令完成Gitee同步："
            echo "git push gitee main"
            echo ""
            echo "或者使用Gitee网页导入功能："
            echo "https://gitee.com/luo-cailian/question-bank-master"
        fi
    fi
}

# 验证同步结果
verify_sync() {
    log "验证同步结果..."
    
    # 获取本地最新提交
    local_commit=$(git rev-parse HEAD)
    
    # 获取GitHub最新提交
    github_commit=$(git ls-remote origin main 2>/dev/null | cut -f1 || echo "unknown")
    
    # 获取Gitee最新提交（检查master和main分支）
    gitee_commit_master=$(git ls-remote gitee master 2>/dev/null | cut -f1 || echo "")
    gitee_commit_main=$(git ls-remote gitee main 2>/dev/null | cut -f1 || echo "")

    # 选择存在的分支
    if [ -n "$gitee_commit_main" ]; then
        gitee_commit="$gitee_commit_main"
        gitee_branch="main"
    elif [ -n "$gitee_commit_master" ]; then
        gitee_commit="$gitee_commit_master"
        gitee_branch="master"
    else
        gitee_commit="unknown"
        gitee_branch="none"
    fi
    
    echo "提交对比："
    echo "本地:   $local_commit"
    echo "GitHub: $github_commit (main)"
    echo "Gitee:  $gitee_commit ($gitee_branch)"
    echo ""
    
    if [ "$local_commit" = "$github_commit" ] && [ "$local_commit" = "$gitee_commit" ]; then
        success "所有仓库完全同步"
    elif [ "$local_commit" = "$github_commit" ]; then
        warning "GitHub同步正常，Gitee需要手动同步"
    elif [ "$local_commit" = "$gitee_commit" ]; then
        warning "Gitee同步正常，GitHub需要检查"
    else
        warning "存在同步差异，请检查"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
QuestionBank Master 双平台同步工具

用法: $0 [选项]

选项:
  -h, --help     显示此帮助信息
  -c, --check    仅检查同步状态，不执行同步
  -g, --github   仅同步到GitHub
  -e, --gitee    仅同步到Gitee

示例:
  $0              # 同步到所有平台
  $0 --check      # 检查同步状态
  $0 --github     # 仅同步到GitHub
  $0 --gitee      # 仅同步到Gitee

EOF
}

# 主函数
main() {
    local check_only=false
    local github_only=false
    local gitee_only=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            -g|--github)
                github_only=true
                shift
                ;;
            -e|--gitee)
                gitee_only=true
                shift
                ;;
            *)
                echo "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "🚀 QuestionBank Master 双平台同步工具"
    echo "================================================"
    echo ""
    
    # 执行检查
    check_git_status
    check_remotes
    
    if [ "$check_only" = true ]; then
        verify_sync
        exit 0
    fi
    
    # 执行同步
    if [ "$github_only" = true ]; then
        sync_to_github
    elif [ "$gitee_only" = true ]; then
        sync_to_gitee
    else
        sync_to_github
        sync_to_gitee
    fi
    
    echo ""
    verify_sync
    
    echo ""
    success "同步操作完成！"
    echo ""
    echo "访问地址："
    echo "GitHub: https://github.com/luocailian/QuestionBank-Master"
    echo "Gitee:  https://gitee.com/luo-cailian/question-bank-master"
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
