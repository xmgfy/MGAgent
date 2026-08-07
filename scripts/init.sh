#!/bin/bash
set -e

echo "========================================="
echo "  MGAgent 初始化脚本"
echo "========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
echo "项目目录: $PROJECT_DIR"
echo ""

# ========== 前置检查 ==========
check_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "❌ 未找到命令: $1"
        echo "   请先安装后再运行此脚本"
        exit 1
    fi
}

echo "检查运行环境..."
check_cmd python3
check_cmd pip3
check_cmd node
check_cmd npm
echo "✅ 环境依赖满足 (python3 / pip3 / node / npm)"
echo ""

# ========== 安装后端依赖 ==========
echo "[1/6] 安装 mgagent-backend 依赖"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-backend"
pip3 install -r requirements.txt -q
echo "✅ mgagent-backend 依赖安装完成"
echo ""

echo "[2/6] 安装 mgagent-admin-backend 依赖"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-admin-backend"
pip3 install -r requirements.txt -q
echo "✅ mgagent-admin-backend 依赖安装完成"
echo ""

# ========== 安装前端依赖 ==========
echo "[3/6] 安装 mgagent-frontend 依赖"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-frontend"
npm install -q
echo "✅ mgagent-frontend 依赖安装完成"
echo ""

echo "[4/6] 安装 mgagent-admin-frontend 依赖"
echo "-----------------------------------------"
cd "$PROJECT_DIR/mgagent-admin-frontend"
npm install -q
echo "✅ mgagent-admin-frontend 依赖安装完成"
echo ""

# ========== 创建必要目录 ==========
echo "[5/6] 创建必要目录"
echo "-----------------------------------------"
mkdir -p "$PROJECT_DIR/.pids"
mkdir -p "$PROJECT_DIR/mgagent-backend/data/chroma"
mkdir -p "$PROJECT_DIR/mgagent-backend/data/documents"
mkdir -p "$PROJECT_DIR/mgagent-backend/instance"
mkdir -p "$PROJECT_DIR/mgagent-admin-backend/instance"
mkdir -p "$PROJECT_DIR/mgagent-admin-backend/data/models"
mkdir -p "$PROJECT_DIR/logs"
echo "✅ 目录创建完成"
echo ""

# ========== 设置脚本执行权限 ==========
echo "[6/6] 设置脚本执行权限"
echo "-----------------------------------------"
chmod +x "$SCRIPT_DIR/init.sh"
chmod +x "$SCRIPT_DIR/start-all.sh"
chmod +x "$SCRIPT_DIR/stop-all.sh"
chmod +x "$SCRIPT_DIR/status.sh"
chmod +x "$SCRIPT_DIR/docker-services.sh"
chmod +x "$SCRIPT_DIR/deploy.sh"
# 如有则赋予
[ -f "$SCRIPT_DIR/git-sync.sh" ] && chmod +x "$SCRIPT_DIR/git-sync.sh"
[ -f "$SCRIPT_DIR/deploy-docs.sh" ] && chmod +x "$SCRIPT_DIR/deploy-docs.sh"
echo "✅ 脚本权限设置完成"
echo ""

echo "========================================="
echo "  ✅ 初始化完成!"
echo "========================================="
echo ""
echo "使用说明:"
echo "  本地开发 (SQLite):  ./scripts/start-all.sh sqlite"
echo "  本地开发 (MySQL):   ./scripts/start-all.sh mysql   (需 Docker)"
echo "  仅重启前后端:       ./scripts/start-all.sh app"
echo "  生产部署:           cp .env.production.example .env.production"
echo "                      vim .env.production"
echo "                      ./scripts/deploy.sh up"
echo "  停止服务:           ./scripts/stop-all.sh"
echo "  状态检查:           ./scripts/status.sh"
echo ""
echo "本地开发端口:"
echo "  Chat 前端:      http://localhost:5173"
echo "  Chat 后端:      http://localhost:8000"
echo "  Admin 前端:     http://localhost:5174"
echo "  Admin 后端:     http://localhost:8001"
echo ""
echo "生产部署端口 (Nginx):"
echo "  Chat 前端:      http://localhost:3000"
echo "  Admin 前端:     http://localhost:3001"
echo ""