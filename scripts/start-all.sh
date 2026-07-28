#!/bin/bash

echo "========================================="
echo "  MGAgent 一键启动脚本"
echo "========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PIDS_DIR="$PROJECT_DIR/.pids"
mkdir -p "$PIDS_DIR"

# 使用正确的 Python 路径（安装了 uvicorn 的 anaconda3）
PYTHON="/opt/anaconda3/bin/python3"

echo "项目目录: $PROJECT_DIR"
echo "Python路径: $PYTHON"
echo ""

# 停止已运行的服务
echo "[0/4] 停止已运行的服务..."
"$SCRIPT_DIR/stop-all.sh" > /dev/null 2>&1
echo "完成"
echo ""

echo "[1/4] 启动 mgagent-backend (端口: 8000)"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-backend"
rm -f backend.log
# 使用进程组启动，便于停止时统一终止
nohup "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
sleep 3
# 获取实际监听端口的进程（可能是子进程）
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null)
if [ -n "$BACKEND_PIDS" ]; then
    # 记录第一个PID
    BACKEND_PID=$(echo "$BACKEND_PIDS" | head -1)
    echo "$BACKEND_PIDS" > "$PIDS_DIR/backend.pid"
    echo "后端服务已启动 (PIDs: $BACKEND_PIDS)"
else
    echo "后端服务启动失败，查看日志: backend.log"
    cat backend.log | tail -20
fi
echo "日志文件: $PROJECT_DIR/mgagent-backend/backend.log"
echo ""

echo "[2/4] 启动 mgagent-admin-backend (端口: 8001)"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-admin-backend"
rm -f admin-backend.log
nohup "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > admin-backend.log 2>&1 &
sleep 3
ADMIN_BACKEND_PIDS=$(lsof -ti:8001 2>/dev/null)
if [ -n "$ADMIN_BACKEND_PIDS" ]; then
    ADMIN_BACKEND_PID=$(echo "$ADMIN_BACKEND_PIDS" | head -1)
    echo "$ADMIN_BACKEND_PIDS" > "$PIDS_DIR/admin-backend.pid"
    echo "管理台后端服务已启动 (PIDs: $ADMIN_BACKEND_PIDS)"
else
    echo "管理台后端服务启动失败，查看日志: admin-backend.log"
    cat admin-backend.log | tail -20
fi
echo "日志文件: $PROJECT_DIR/mgagent-admin-backend/admin-backend.log"
echo ""

echo "[3/4] 启动 mgagent-frontend (端口: 5173)"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-frontend"
rm -f frontend.log
# 使用 npm run dev 启动，记录 PID
nohup npm run dev > frontend.log 2>&1 &
sleep 5
FRONTEND_PIDS=$(lsof -ti:5173 2>/dev/null)
if [ -n "$FRONTEND_PIDS" ]; then
    FRONTEND_PID=$(echo "$FRONTEND_PIDS" | head -1)
    echo "$FRONTEND_PIDS" > "$PIDS_DIR/frontend.pid"
    echo "前端服务已启动 (PIDs: $FRONTEND_PIDS)"
else
    echo "前端服务启动失败，查看日志: frontend.log"
    cat frontend.log | tail -20
fi
echo "日志文件: $PROJECT_DIR/mgagent-frontend/frontend.log"
echo ""

echo "[4/4] 启动 mgagent-admin-frontend (端口: 5174)"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-admin-frontend"
rm -f admin-frontend.log
nohup npm run dev -- --port 5174 > admin-frontend.log 2>&1 &
sleep 5
ADMIN_FRONTEND_PIDS=$(lsof -ti:5174 2>/dev/null)
if [ -n "$ADMIN_FRONTEND_PIDS" ]; then
    ADMIN_FRONTEND_PID=$(echo "$ADMIN_FRONTEND_PIDS" | head -1)
    echo "$ADMIN_FRONTEND_PIDS" > "$PIDS_DIR/admin-frontend.pid"
    echo "管理台前端服务已启动 (PIDs: $ADMIN_FRONTEND_PIDS)"
else
    echo "管理台前端服务启动失败，查看日志: admin-frontend.log"
    cat admin-frontend.log | tail -20
fi
echo "日志文件: $PROJECT_DIR/mgagent-admin-frontend/admin-frontend.log"
echo ""

echo "========================================="
echo "  所有服务启动完成!"
echo "========================================="
echo ""
echo "服务地址:"
echo "  - 核心前端: http://localhost:5173"
echo "  - 核心后端: http://localhost:8000"
echo "  - 管理台前端: http://localhost:5174"
echo "  - 管理台后端: http://localhost:8001"
echo ""
echo "停止服务请运行: ./scripts/stop-all.sh"
echo "检查服务状态: ./scripts/status.sh"
echo ""