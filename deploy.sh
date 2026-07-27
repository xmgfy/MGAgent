#!/bin/bash

# MGAgent Docker 部署脚本
# 用于一键启动 MGAgent 项目所有服务

set -e

echo "=========================================="
echo "  MGAgent Docker 部署脚本"
echo "=========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker Desktop"
    echo ""
    echo "在 macOS 上，可以通过以下方式启动："
    echo "  open -a Docker"
    exit 1
fi

echo "✅ Docker 正在运行"
echo ""

# 检查 docker compose 是否可用
if ! docker compose version > /dev/null 2>&1 && ! docker-compose --version > /dev/null 2>&1; then
    echo "❌ Docker Compose 不可用"
    exit 1
fi

# 确定使用的命令
if docker compose version > /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "✅ Docker Compose 可用: $($COMPOSE_CMD version)"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 解析参数
ACTION=${1:-"up"}

case "$ACTION" in
    up|start)
        echo "🚀 正在启动 MGAgent 服务..."
        echo ""
        $COMPOSE_CMD up -d --build
        echo ""
        echo "✅ MGAgent 服务已启动！"
        echo ""
        echo "服务访问地址："
        echo "  - 智能客服助手前端: http://localhost:${FRONTEND_PORT:-3000}"
        echo "  - 管理台前端: http://localhost:${ADMIN_FRONTEND_PORT:-3001}"
        echo "  - 智能客服助手后端 API: http://localhost:${BACKEND_PORT:-8000}"
        echo "  - 管理台后端 API: http://localhost:${ADMIN_BACKEND_PORT:-8001}"
        echo "  - MySQL: localhost:${MYSQL_PORT:-3306}"
        echo "  - Milvus 向量数据库: localhost:${MILVUS_PORT:-19530}"
        echo "  - Attu (Milvus 管理界面): http://localhost:8003"
        echo ""
        echo "默认管理员账号: admin / admin123"
        echo ""
        echo "查看服务状态: $0 status"
        echo "查看日志: $0 logs"
        echo "停止服务: $0 stop"
        ;;
        
    down|stop)
        echo "🛑 正在停止 MGAgent 服务..."
        $COMPOSE_CMD down
        echo "✅ MGAgent 服务已停止"
        ;;
        
    restart)
        echo "🔄 正在重启 MGAgent 服务..."
        $COMPOSE_CMD down
        $COMPOSE_CMD up -d --build
        echo "✅ MGAgent 服务已重启"
        ;;
        
    status)
        echo "📊 服务状态："
        echo ""
        $COMPOSE_CMD ps
        ;;
        
    logs)
        echo "📋 服务日志："
        echo ""
        $COMPOSE_CMD logs --tail=100
        ;;
        
    rebuild)
        echo "🔨 正在重新构建并启动..."
        $COMPOSE_CMD build --no-cache
        $COMPOSE_CMD up -d
        echo "✅ 构建完成"
        ;;
        
    clean)
        echo "🧹 正在清理所有数据..."
        echo "⚠️  这将删除所有容器和数据卷！"
        read -p "确认继续吗？(y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            $COMPOSE_CMD down -v
            echo "✅ 清理完成"
        else
            echo "❌ 已取消"
        fi
        ;;
        
    *)
        echo "用法: $0 {up|down|restart|status|logs|rebuild|clean}"
        echo ""
        echo "  up       - 启动所有服务（默认）"
        echo "  down     - 停止所有服务"
        echo "  restart  - 重启所有服务"
        echo "  status   - 查看服务状态"
        echo "  logs     - 查看服务日志"
        echo "  rebuild  - 重新构建镜像"
        echo "  clean    - 清理所有数据"
        exit 1
        ;;
esac
