#!/bin/bash

# MGAgent 一键部署脚本
# 支持两套技术栈方案：
#   方案1: SQLite + ChromaDB (docker-compose.local.yml)
#   方案2: MySQL + Milvus (docker-compose.infra.yml + docker-compose.mysql-app.yml)

set -e

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    MGAgent 一键部署脚本                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_info "Docker 环境检查通过"
}

# 获取 docker compose 命令
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# 显示使用说明
show_usage() {
    echo "使用方法:"
    echo "  ./scripts/deploy.sh [选项]"
    echo ""
    echo "选项:"
    echo "  sqlite      启动 SQLite + ChromaDB 方案（轻量级，无需外部数据库）"
    echo "  mysql       启动 MySQL + Milvus 方案（先启动基础设施，再启动应用）"
    echo "  stop        停止所有服务"
    echo "  restart     重启所有服务"
    echo "  logs        查看服务日志"
    echo "  status      查看服务状态"
    echo "  cleanup     清理所有容器和数据卷"
    echo "  help        显示帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/deploy.sh sqlite      # 启动 SQLite + ChromaDB 方案"
    echo "  ./scripts/deploy.sh mysql       # 启动 MySQL + Milvus 方案"
    echo "  ./scripts/deploy.sh stop        # 停止所有服务"
}

# 交互式选择方案
select_scheme() {
    echo ""
    echo "请选择部署方案:"
    echo ""
    echo "  ${GREEN}1)${NC} SQLite + ChromaDB"
    echo "     - 轻量级单机部署"
    echo "     - 适合开发调试"
    echo "     - 无需外部数据库服务"
    echo ""
    echo "  ${GREEN}2)${NC} MySQL + Milvus"
    echo "     - 高性能生产级部署"
    echo "     - 适合大规模数据"
    echo "     - 包含完整的数据库服务"
    echo ""
    
    read -p "请输入选项 [1/2] (默认: 1): " choice
    
    case $choice in
        2)
            echo "mysql"
            ;;
        *)
            echo "sqlite"
            ;;
    esac
}

# 启动 SQLite + ChromaDB 方案
start_sqlite() {
    print_info "正在启动 SQLite + ChromaDB 方案..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.local.yml" down 2>/dev/null || true
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.local.yml" build --no-cache
    
    print_info "镜像构建完成，正在启动服务..."
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.local.yml" up -d
    
    print_success_message "SQLite + ChromaDB"
}

# 启动 MySQL + Milvus 方案
start_mysql() {
    print_info "正在启动 MySQL + Milvus 方案..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    # 检查环境变量文件
    if [ ! -f "$PROJECT_ROOT/.env.prod" ]; then
        print_warning "未找到 .env.prod 文件，使用默认配置"
        create_default_env_prod
    fi
    
    # 第一步：启动基础设施服务
    print_info "第一步：启动 MySQL + Milvus 基础设施..."
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.infra.yml" down 2>/dev/null || true
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.infra.yml" up -d
    
    print_info "等待基础设施就绪 (约 20 秒)..."
    sleep 20
    
    # 检查基础设施状态
    if ! $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.infra.yml" ps | grep -q "healthy"; then
        print_warning "部分基础设施可能尚未完全就绪，继续部署应用..."
    fi
    
    # 第二步：启动应用层服务
    print_info "第二步：构建并启动应用层服务..."
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.mysql-app.yml" down 2>/dev/null || true
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.mysql-app.yml" build --no-cache
    
    print_info "镜像构建完成，正在启动应用服务..."
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.mysql-app.yml" up -d
    
    print_success_message "MySQL + Milvus"
}

# 创建默认的生产环境配置
create_default_env_prod() {
    cat > "$PROJECT_ROOT/.env.prod" << 'EOF'
# MySQL 配置
MYSQL_ROOT_PASSWORD=mgagent_root_2024
MYSQL_DATABASE=mgagent
MYSQL_USER=mgagent
MYSQL_PASSWORD=mgagent_password_2024
MYSQL_PORT=3306

# Milvus 配置
MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_GRPC_PORT=9091

# 服务端口配置
BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001
EOF
    
    print_info "已创建默认配置文件 .env.prod"
}

# 打印成功信息
print_success_message() {
    local env_type=$1
    
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 部署成功！                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BLUE}方案类型:${NC} $env_type"
    echo -e "  ${BLUE}MGAgent 前端:${NC}    http://localhost:3000"
    echo -e "  ${BLUE}管理台前端:${NC}      http://localhost:3001"
    echo -e "  ${BLUE}后端 API:${NC}        http://localhost:8000"
    echo -e "  ${BLUE}管理台 API:${NC}      http://localhost:8001"
    echo ""
    echo -e "${YELLOW}默认管理员账号:${NC}"
    echo -e "  用户名: admin"
    echo -e "  密码:   admin123"
    echo ""
    echo -e "${GREEN}查看服务状态:${NC} ./scripts/deploy.sh status"
    echo -e "${GREEN}查看服务日志:${NC} ./scripts/deploy.sh logs"
    echo -e "${GREEN}停止所有服务:${NC} ./scripts/deploy.sh stop"
    echo ""
}

# 停止服务
stop_services() {
    print_info "正在停止所有服务..."
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.local.yml" down 2>/dev/null || true
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.mysql-app.yml" down 2>/dev/null || true
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.infra.yml" down 2>/dev/null || true
    
    print_info "所有服务已停止"
}

# 重启服务
restart_services() {
    print_info "请选择要重启的方案..."
    
    scheme=$(select_scheme)
    
    stop_services
    
    if [ "$scheme" == "sqlite" ]; then
        start_sqlite
    else
        start_mysql
    fi
}

# 查看日志
show_logs() {
    print_info "请选择要查看日志的方案..."
    
    scheme=$(select_scheme)
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    if [ "$scheme" == "sqlite" ]; then
        $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.local.yml" logs -f --tail=100
    else
        print_info "基础设施日志:"
        $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.infra.yml" logs -f --tail=50 &
        local infra_pid=$!
        print_info "应用层日志:"
        $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.mysql-app.yml" logs -f --tail=50
        kill $infra_pid 2>/dev/null || true
    fi
}

# 查看状态
show_status() {
    echo ""
    echo -e "${BLUE}SQLite + ChromaDB 方案状态:${NC}"
    echo ""
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.local.yml" ps 2>/dev/null || echo "  未运行"
    
    echo ""
    echo -e "${BLUE}MySQL + Milvus 基础设施状态:${NC}"
    echo ""
    
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.infra.yml" ps 2>/dev/null || echo "  未运行"
    
    echo ""
    echo -e "${BLUE}MySQL + Milvus 应用层状态:${NC}"
    echo ""
    
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.mysql-app.yml" ps 2>/dev/null || echo "  未运行"
}

# 清理所有数据
cleanup_all() {
    echo ""
    print_warning "⚠️  此操作将删除所有容器和数据卷，不可恢复！"
    echo ""
    read -p "确认清理？(输入 yes 确认): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "已取消清理操作"
        exit 0
    fi
    
    COMPOSE_CMD=$(get_compose_cmd)
    
    print_info "正在清理 SQLite + ChromaDB 方案..."
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.local.yml" down -v 2>/dev/null || true
    
    print_info "正在清理 MySQL + Milvus 应用层..."
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.mysql-app.yml" down -v 2>/dev/null || true
    
    print_info "正在清理 MySQL + Milvus 基础设施..."
    $COMPOSE_CMD -f "$PROJECT_ROOT/docker-compose.infra.yml" down -v 2>/dev/null || true
    
    print_info "正在清理未使用的 Docker 资源..."
    docker system prune -f 2>/dev/null || true
    
    print_info "清理完成"
}

# 主函数
main() {
    print_banner
    
    # 检查 Docker 环境
    check_docker
    
    # 获取命令行参数
    action=${1:-""}
    
    case $action in
        sqlite)
            start_sqlite
            ;;
        mysql)
            start_mysql
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup_all
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            if [ -z "$action" ]; then
                # 交互式选择
                scheme=$(select_scheme)
                
                if [ "$scheme" == "sqlite" ]; then
                    start_sqlite
                else
                    start_mysql
                fi
            else
                print_error "未知选项: $action"
                show_usage
                exit 1
            fi
            ;;
    esac
}

# 执行主函数
main "$@"
