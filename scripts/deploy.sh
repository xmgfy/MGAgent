#!/bin/bash

# ============================================
# MGAgent 生产环境部署脚本
# 适用于生产环境一键部署
#
# 用法:
#   ./scripts/deploy.sh up          启动所有服务
#   ./scripts/deploy.sh down        停止所有服务
#   ./scripts/deploy.sh restart     重启所有服务
#   ./scripts/deploy.sh status      查看服务状态
#   ./scripts/deploy.sh logs        查看日志
#   ./scripts/deploy.sh build       重新构建镜像
#   ./scripts/deploy.sh cleanup     清理所有容器和数据卷
#   ./scripts/deploy.sh help        显示帮助
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 路径配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"

# 显示帮助
show_help() {
    echo -e "${BLUE}MGAgent 生产环境部署脚本${NC}"
    echo ""
    echo "用法: $0 <命令>"
    echo ""
    echo "命令列表:"
    echo "  up        启动所有服务（首次会构建镜像）"
    echo "  down      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    查看服务运行状态"
    echo "  logs      查看服务日志"
    echo "  build     重新构建应用镜像"
    echo "  cleanup   清理所有容器和数据卷（不可恢复）"
    echo "  help      显示帮助信息"
    echo ""
    echo -e "${CYAN}前置条件:${NC}"
    echo "  1. 已安装 Docker 和 Docker Compose"
    echo "  2. 已配置 .env.production 环境变量文件"
    echo "  3. 端口未被占用（默认: 3000, 3001, 8000, 8001, 3306, 19530）"
    echo ""
    echo -e "${CYAN}快速开始:${NC}"
    echo "  # 1. 复制环境配置模板"
    echo "  cp .env.production.example .env.production"
    echo ""
    echo "  # 2. 修改生产环境配置（密码、域名等）"
    echo "  vim .env.production"
    echo ""
    echo "  # 3. 启动服务"
    echo "  ./scripts/deploy.sh up"
}

# 检查环境
check_env() {
    echo -e "${YELLOW}检查环境...${NC}"
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ 未找到 Docker${NC}"
        echo "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker 未运行${NC}"
        echo "请启动 Docker 服务"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}❌ 未找到 Docker Compose${NC}"
        echo "请安装 Docker Compose v2+"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker 环境正常${NC}"
    echo ""
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠  未找到 .env.production 文件${NC}"
        
        if [ -f "$PROJECT_DIR/.env.production.example" ]; then
            echo -e "${YELLOW}正在从模板创建...${NC}"
            cp "$PROJECT_DIR/.env.production.example" "$ENV_FILE"
            echo -e "${GREEN}✓ 已创建 .env.production${NC}"
            echo -e "${RED}请修改配置后重新运行: $0 up${NC}"
            echo ""
            cat "$ENV_FILE"
            exit 0
        else
            echo -e "${RED}❌ 未找到模板文件${NC}"
            exit 1
        fi
    fi
    
    # 检查必要的环境变量
    source "$ENV_FILE"
    
    MISSING=""
    [ -z "$MYSQL_ROOT_PASSWORD" ] && MISSING="$MISSING\n  - MYSQL_ROOT_PASSWORD"
    [ -z "$MYSQL_PASSWORD" ] && MISSING="$MISSING\n  - MYSQL_PASSWORD"
    
    if [ -n "$MISSING" ]; then
        echo -e "${RED}❌ 以下环境变量未设置:$MISSING${NC}"
        echo ""
        echo -e "${YELLOW}请编辑 $ENV_FILE 并设置缺失的变量${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 环境变量检查通过${NC}"
    echo ""
}

# 启动服务
start_services() {
    echo -e "${YELLOW}========== 启动所有服务 ==========${NC}"
    echo ""
    
    # 检查环境
    check_env
    check_env_file
    
    echo -e "${CYAN}启动 Docker Compose 服务...${NC}"
    echo ""
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    echo ""
    echo -e "${GREEN}✅ 所有服务已启动${NC}"
    echo ""
    
    show_access_info
    show_status
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}========== 停止所有服务 ==========${NC}"
    echo ""
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" down
    
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
}

# 重启服务
restart_services() {
    echo -e "${YELLOW}========== 重启所有服务 ==========${NC}"
    echo ""
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
    
    echo -e "${GREEN}✅ 所有服务已重启${NC}"
    show_status
}

# 查看状态
show_status() {
    echo -e "${YELLOW}========== 服务状态 ==========${NC}"
    echo ""
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    show_access_info
}

# 显示访问信息
show_access_info() {
    source "$ENV_FILE" 2>/dev/null || true
    
    CHAT_PORT="${CHAT_FRONTEND_PORT:-3000}"
    ADMIN_PORT="${ADMIN_FRONTEND_PORT:-3001}"
    ATTU_PORT="${ATTU_PORT:-8003}"
    
    SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
    
    echo -e "${CYAN}访问地址:${NC}"
    echo "  Chat 前端:   http://$SERVER_IP:$CHAT_PORT"
    echo "  Admin 前端:  http://$SERVER_IP:$ADMIN_PORT"
    echo "  Chat API:    http://$SERVER_IP:${CHAT_BACKEND_PORT:-8000}/docs"
    echo "  Admin API:   http://$SERVER_IP:${ADMIN_BACKEND_PORT:-8001}/docs"
    echo "  Attu UI:     http://$SERVER_IP:$ATTU_PORT"
    echo ""
}

# 查看日志
show_logs() {
    echo -e "${YELLOW}========== 服务日志 ==========${NC}"
    echo ""
    
    cd "$PROJECT_DIR"
    
    local SERVICE="${1:-all}"
    
    if [ "$SERVICE" = "all" ]; then
        docker compose -f "$COMPOSE_FILE" logs --tail=100 -f
    else
        docker compose -f "$COMPOSE_FILE" logs "$SERVICE" --tail=100 -f
    fi
}

# 构建镜像
build_images() {
    echo -e "${YELLOW}========== 重新构建镜像 ==========${NC}"
    echo ""
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# 清理
cleanup() {
    echo -e "${RED}⚠  警告: 此操作将删除所有容器和数据卷！${NC}"
    echo ""
    echo "这将删除:"
    echo "  - 所有 MGAgent 相关容器"
    echo "  - 所有数据卷（包括数据库、向量库数据）"
    echo ""
    echo -e "${RED}此操作不可恢复！${NC}"
    echo ""
    
    read -p "确认清理？输入 YES 继续: " CONFIRM
    
    if [ "$CONFIRM" != "YES" ]; then
        echo "已取消"
        exit 0
    fi
    
    cd "$PROJECT_DIR"
    
    echo -e "${YELLOW}正在停止并移除所有服务...${NC}"
    docker compose -f "$COMPOSE_FILE" down -v
    
    echo -e "${YELLOW}正在清理镜像...${NC}"
    docker compose -f "$COMPOSE_FILE" down --rmi all
    
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 主逻辑
case "${1:-help}" in
    up)
        start_services
        ;;
    down)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-all}"
        ;;
    build)
        build_images
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}错误: 未知命令 '$1'${NC}"
        echo ""
        show_help
        exit 1
esac