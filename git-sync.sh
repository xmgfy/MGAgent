#!/bin/bash

# MGAgent Git 同步脚本
# 支持同时同步到 GitHub 和 Gitee

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${BLUE}MGAgent Git 同步脚本${NC}"
    echo "用法: $0 <命令>"
    echo ""
    echo "命令列表:"
    echo "  pull          从远程拉取最新代码"
    echo "  push          推送本地代码到所有远程仓库"
    echo "  commit <msg>  提交代码并推送 (示例: $0 commit \"fix: 修复bug\")"
    echo "  status        查看当前状态"
    echo "  sync          拉取、提交、推送一站式操作"
    echo "  help          显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 commit \"feat: 添加新功能\""
    echo "  $0 sync"
}

# 检查是否在 Git 仓库中
check_git_repo() {
    if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        echo -e "${RED}错误: 当前目录不是 Git 仓库${NC}"
        exit 1
    fi
}

# 拉取代码
git_pull() {
    echo -e "${BLUE}正在从远程拉取代码...${NC}"
    
    echo -e "${YELLOW}拉取 GitHub...${NC}"
    git pull origin main
    
    echo -e "${YELLOW}拉取 Gitee...${NC}"
    git pull gitee main
    
    echo -e "${GREEN}✓ 拉取完成${NC}"
}

# 推送代码
git_push() {
    echo -e "${BLUE}正在推送到远程仓库...${NC}"
    
    echo -e "${YELLOW}推送到 GitHub...${NC}"
    git push origin main
    
    echo -e "${YELLOW}推送到 Gitee...${NC}"
    git push gitee main
    
    echo -e "${GREEN}✓ 推送完成${NC}"
}

# 提交代码
git_commit() {
    if [ -z "$1" ]; then
        echo -e "${RED}错误: 提交信息不能为空${NC}"
        echo "用法: $0 commit \"提交信息\""
        exit 1
    fi
    
    echo -e "${BLUE}正在提交代码...${NC}"
    
    # 添加所有文件
    git add .
    
    # 显示变更
    echo -e "${YELLOW}变更详情:${NC}"
    git status --short
    
    # 提交
    git commit -m "$1"
    
    echo -e "${GREEN}✓ 提交完成${NC}"
}

# 查看状态
git_status() {
    echo -e "${BLUE}当前 Git 状态:${NC}"
    git status
    echo ""
    echo -e "${BLUE}远程仓库:${NC}"
    git remote -v
}

# 同步操作 (拉取 -> 提交 -> 推送)
git_sync() {
    check_git_repo
    
    echo -e "${BLUE}========== 开始同步 ==========${NC}"
    
    # 拉取代码
    git_pull
    
    # 检查是否有未提交的更改
    if git diff --cached --exit-code > /dev/null 2>&1 && git diff --exit-code > /dev/null 2>&1; then
        echo -e "${YELLOW}提示: 没有未提交的更改${NC}"
        echo -e "${BLUE}========== 同步结束 ==========${NC}"
        exit 0
    fi
    
    # 自动生成提交信息
    local commit_msg="chore: 同步更新"
    
    # 添加并提交
    git add .
    git commit -m "$commit_msg"
    
    # 推送
    git_push
    
    echo -e "${BLUE}========== 同步完成 ==========${NC}"
}

# 主逻辑
check_git_repo

case "$1" in
    pull)
        git_pull
        ;;
    push)
        git_push
        ;;
    commit)
        shift
        git_commit "$*"
        ;;
    status)
        git_status
        ;;
    sync)
        git_sync
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac