#!/bin/bash
# MGAgent Docker 服务管理脚本
# 用于启动/停止 MySQL 和 Milvus 服务

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env.docker"

show_help() {
    echo -e "${BLUE}MGAgent Docker 服务管理${NC}"
    echo "用法: $0 <命令>"
    echo ""
    echo "命令列表:"
    echo "  start       启动 MySQL 和 Milvus 服务"
    echo "  stop        停止所有服务"
    echo "  restart     重启所有服务"
    echo "  status      查看服务状态"
    echo "  logs        查看服务日志"
    echo "  migrate     执行数据迁移"
    echo "  help        显示帮助信息"
}

start_services() {
    echo -e "${BLUE}🚀 启动 MGAgent 基础设施服务...${NC}"
    
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    fi
    
    docker compose -f "$COMPOSE_FILE" up -d
    
    echo -e "${YELLOW}等待服务就绪...${NC}"
    sleep 10
    
    docker compose -f "$COMPOSE_FILE" ps
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
    echo ""
    echo -e "📊 访问地址:"
    echo -e "   MySQL:      mysql -h localhost -P 3306 -u mgagent -p"
    echo -e "   Milvus:     localhost:19530"
    echo -e "   Attu UI:    http://localhost:8000"
}

stop_services() {
    echo -e "${BLUE}🛑 停止 MGAgent 基础设施服务...${NC}"
    
    docker compose -f "$COMPOSE_FILE" down
    
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

restart_services() {
    echo -e "${BLUE}🔄 重启 MGAgent 基础设施服务...${NC}"
    stop_services
    sleep 5
    start_services
}

show_status() {
    echo -e "${BLUE}📊 MGAgent 服务状态${NC}"
    docker compose -f "$COMPOSE_FILE" ps
}

show_logs() {
    echo -e "${BLUE}📝 MGAgent 服务日志${NC}"
    docker compose -f "$COMPOSE_FILE" logs -f --tail=100
}

do_migrate() {
    echo -e "${BLUE}🚀 执行数据迁移...${NC}"
    
    # 检查 Python 依赖
    pip install pymysql pymilvus langchain-chroma chromadb -q 2>/dev/null || true
    
    python "$PROJECT_ROOT/scripts/migrate_data.py"
}

case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    migrate)
        do_migrate
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
