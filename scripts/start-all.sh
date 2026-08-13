#!/bin/bash

# ============================================
# MGAgent 一键启动脚本
# 仅支持 MySQL + Milvus (生产级)
#
# 用法:
#   ./scripts/start-all.sh [mysql|app]
#   ./scripts/start-all.sh mysql     # MySQL 模式 (需 Docker 基建)
#   ./scripts/start-all.sh app       # 仅重启前后端应用 (需基建已运行)
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ========== 参数解析 ==========
MODE="${1:-mysql}"  # 默认 mysql 模式

if [ "$MODE" != "mysql" ] && [ "$MODE" != "app" ]; then
    echo -e "${RED}错误: 无效的模式 '$MODE'${NC}"
    echo ""
    echo "用法: $0 [mysql|app]"
    echo ""
    echo "  mysql   - 使用 MySQL + Milvus (需要 Docker 基础设施)"
    echo "  app     - 仅重启前后端应用，不重启基建服务 (需基建已运行)"
    exit 1
fi

# ========== 路径配置 ==========
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PIDS_DIR="$PROJECT_DIR/.pids"
mkdir -p "$PIDS_DIR"

PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
    if [ -x "/opt/anaconda3/bin/python3" ]; then
        PYTHON="/opt/anaconda3/bin/python3"
    elif [ -x "/usr/local/bin/python3" ]; then
        PYTHON="/usr/local/bin/python3"
    else
        PYTHON="$(command -v python3 || echo python3)"
    fi
fi

if ! "$PYTHON" --version >/dev/null 2>&1; then
    echo -e "${RED}❌ 未找到可用的 Python: $PYTHON${NC}"
    echo "   请先安装 Python 3.10+ 或导出 PYTHON=/path/to/python3"
    exit 1
fi

# ========== 显示启动信息 ==========
echo "========================================="
echo -e "  ${CYAN}MGAgent 一键启动脚本 (MySQL + Milvus)${NC}"
echo "========================================="
echo ""

if [ "$MODE" = "app" ]; then
    echo -e "${GREEN}📦 启动模式: 仅前后端应用${NC}"
    echo -e "${YELLOW}    跳过基建服务重启，保持基础设施不变${NC}"
else
    echo -e "${GREEN}📦 启动模式: MySQL + Milvus (生产级)${NC}"
fi

echo "项目目录: $PROJECT_DIR"
echo "Python路径: $PYTHON"
echo ""

# ========== 步骤 0: 停止已运行的应用服务 ==========
echo -e "${YELLOW}[0/4] 停止已运行的应用服务...${NC}"
if [ "$MODE" = "app" ]; then
    "$SCRIPT_DIR/stop-all.sh" --app-only > /dev/null 2>&1
else
    "$SCRIPT_DIR/stop-all.sh" > /dev/null 2>&1
fi
echo "完成"
echo ""

# ========== 步骤 1: Docker 基础设施 ==========
if [ "$MODE" = "app" ]; then
    echo -e "${YELLOW}[1/4] 跳过 Docker 基础设施 (app 模式)${NC}"
    if ! lsof -i:3306 >/dev/null 2>&1; then
        echo -e "  ${RED}⚠️  MySQL (3306) 未运行! app 模式不会启动基建${NC}"
        echo -e "  ${YELLOW}    请先运行: ./scripts/start-all.sh mysql${NC}"
        exit 1
    fi
    if ! lsof -i:19530 >/dev/null 2>&1; then
        echo -e "  ${RED}⚠️  Milvus (19530) 未运行! app 模式不会启动基建${NC}"
        echo -e "  ${YELLOW}    请先运行: ./scripts/start-all.sh mysql${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✅ 基建服务已在运行 (MySQL + Milvus)${NC}"
else
    echo -e "${YELLOW}[1/4] 启动 Docker 基础设施服务 (MySQL + Milvus)...${NC}"
    echo "-----------------------------------------"
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
        echo "   macOS: 打开 Docker Desktop 应用"
        echo "   Linux: sudo systemctl start docker"
        exit 1
    fi
    
    "$SCRIPT_DIR/docker-services.sh" start
    
    echo -e "${GREEN}✅ 基础设施服务已启动${NC}"
fi
echo ""

# ========== 步骤 2: 配置环境变量 ==========
echo -e "${YELLOW}[2/4] 配置环境变量...${NC}"
echo "-----------------------------------------"

if [ "$MODE" != "app" ]; then
    BACKEND_ENV_FILE="$PROJECT_DIR/mgagent-backend/.env"
    BACKEND_ENV_TEMPLATE="$PROJECT_DIR/mgagent-backend/.env.mysql"

    if [ -f "$BACKEND_ENV_TEMPLATE" ]; then
        cp "$BACKEND_ENV_TEMPLATE" "$BACKEND_ENV_FILE"
        echo -e "  ✅ mgagent-backend/.env 已配置"
    else
        echo -e "  ⚠️  未找到 $BACKEND_ENV_TEMPLATE，使用现有 .env"
    fi

    ADMIN_BACKEND_ENV_FILE="$PROJECT_DIR/mgagent-admin-backend/.env"
    ADMIN_BACKEND_ENV_TEMPLATE="$PROJECT_DIR/mgagent-admin-backend/.env.mysql"

    if [ -f "$ADMIN_BACKEND_ENV_TEMPLATE" ]; then
        cp "$ADMIN_BACKEND_ENV_TEMPLATE" "$ADMIN_BACKEND_ENV_FILE"
        echo -e "  ✅ mgagent-admin-backend/.env 已配置"
    else
        echo -e "  ⚠️  未找到 $ADMIN_BACKEND_ENV_TEMPLATE，使用现有 .env"
    fi
else
    echo -e "  ℹ️  app 模式: 保持现有 .env 配置不变"
fi
echo ""

# ========== 步骤 3: 启动后端服务 ==========
echo -e "${YELLOW}[3/4] 启动后端服务${NC}"
echo "-----------------------------------------"

echo -e "  ${CYAN}启动 mgagent-backend (端口: 8000)${NC}"
cd "$PROJECT_DIR/mgagent-backend"
rm -f backend.log

echo "  MySQL主机: $(grep MYSQL_HOST .env 2>/dev/null | cut -d= -f2 || echo 'localhost')"
echo "  MySQL端口: $(grep MYSQL_PORT .env 2>/dev/null | cut -d= -f2 || echo '3306')"

nohup "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
sleep 3

BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null)
if [ -n "$BACKEND_PIDS" ]; then
    echo "$BACKEND_PIDS" > "$PIDS_DIR/backend.pid"
    echo -e "  ${GREEN}✅ 后端服务已启动 (PIDs: $BACKEND_PIDS)${NC}"
else
    echo -e "  ${RED}❌ 后端服务启动失败${NC}"
    echo "  查看日志: $PROJECT_DIR/mgagent-backend/backend.log"
    tail -20 backend.log
    exit 1
fi
echo "  日志文件: $PROJECT_DIR/mgagent-backend/backend.log"
echo ""

echo -e "  ${CYAN}启动 mgagent-admin-backend (端口: 8001)${NC}"
cd "$PROJECT_DIR/mgagent-admin-backend"
rm -f admin-backend.log

nohup "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > admin-backend.log 2>&1 &
sleep 3

ADMIN_BACKEND_PIDS=$(lsof -ti:8001 2>/dev/null)
if [ -n "$ADMIN_BACKEND_PIDS" ]; then
    echo "$ADMIN_BACKEND_PIDS" > "$PIDS_DIR/admin-backend.pid"
    echo -e "  ${GREEN}✅ 管理台后端服务已启动 (PIDs: $ADMIN_BACKEND_PIDS)${NC}"
else
    echo -e "  ${RED}❌ 管理台后端服务启动失败${NC}"
    echo "  查看日志: $PROJECT_DIR/mgagent-admin-backend/admin-backend.log"
    tail -20 admin-backend.log
    exit 1
fi
echo "  日志文件: $PROJECT_DIR/mgagent-admin-backend/admin-backend.log"
echo ""

# ========== 步骤 4: 启动前端服务 ==========
echo -e "${YELLOW}[4/4] 启动前端服务${NC}"
echo "-----------------------------------------"

echo -e "  ${CYAN}启动 mgagent-frontend (端口: 5173)${NC}"
cd "$PROJECT_DIR/mgagent-frontend"
rm -f frontend.log
nohup npm run dev > frontend.log 2>&1 &
sleep 5

FRONTEND_PIDS=$(lsof -ti:5173 2>/dev/null)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "$FRONTEND_PIDS" > "$PIDS_DIR/frontend.pid"
    echo -e "  ${GREEN}✅ 前端服务已启动 (PIDs: $FRONTEND_PIDS)${NC}"
else
    echo -e "  ${YELLOW}⚠️  前端服务可能未完全启动，请查看日志${NC}"
    echo "  查看日志: $PROJECT_DIR/mgagent-frontend/frontend.log"
fi

echo -e "  ${CYAN}启动 mgagent-admin-frontend (端口: 5174)${NC}"
cd "$PROJECT_DIR/mgagent-admin-frontend"
rm -f admin-frontend.log
nohup npm run dev -- --port 5174 > admin-frontend.log 2>&1 &
sleep 5

ADMIN_FRONTEND_PIDS=$(lsof -ti:5174 2>/dev/null)
if [ -n "$ADMIN_FRONTEND_PIDS" ]; then
    echo "$ADMIN_FRONTEND_PIDS" > "$PIDS_DIR/admin-frontend.pid"
    echo -e "  ${GREEN}✅ 管理台前端服务已启动 (PIDs: $ADMIN_FRONTEND_PIDS)${NC}"
else
    echo -e "  ${YELLOW}⚠️  管理台前端服务可能未完全启动，请查看日志${NC}"
    echo "  查看日志: $PROJECT_DIR/mgagent-admin-frontend/admin-frontend.log"
fi
echo ""

# ========== 完成 ==========
echo "========================================="
echo -e "  ${GREEN}🎉 所有服务启动完成!${NC}"
echo "========================================="
echo ""
echo -e "${CYAN}启动模式:${NC} $MODE (MySQL + Milvus)"
echo ""
echo -e "${CYAN}服务地址:${NC}"
echo "  - 核心前端:     http://localhost:5173"
echo "  - 核心后端:     http://localhost:8000"
echo "  - 管理台前端:   http://localhost:5174"
echo "  - 管理台后端:   http://localhost:8001"
echo ""
echo -e "${CYAN}基础设施服务:${NC}"
echo "  - MySQL:        localhost:3306"
echo "  - Milvus:       localhost:19530"
echo "  - Attu UI:      http://localhost:8003"
echo ""
echo -e "${YELLOW}常用命令:${NC}"
echo "  停止服务:       ./scripts/stop-all.sh"
echo "  检查状态:       ./scripts/status.sh"
echo "  完整重启:       ./scripts/start-all.sh mysql"
echo "  仅重启前后端:   ./scripts/start-all.sh app"
echo "  管理基础设施:   ./scripts/docker-services.sh start|stop|status"
echo ""
