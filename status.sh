#!/bin/bash

echo "========================================="
echo "  MGAgent 服务状态检查"
echo "========================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_DIR="$PROJECT_DIR/.pids"

services=(
    "mgagent-backend:8000:backend:http://localhost:8000/api/health"
    "mgagent-admin-backend:8001:admin-backend:http://localhost:8001/admin/api/health"
    "mgagent-frontend:5173:frontend:http://localhost:5173"
    "mgagent-admin-frontend:5174:admin-frontend:http://localhost:5174"
)

echo "--- 进程状态 ---"
echo ""

check_process() {
    local name=$1
    local port=$2
    local pid_name=$3
    
    echo "$name:"
    
    # 通过端口检查
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "  ✓ 端口 $port 正在监听"
        echo "  进程PID: $pids"
        
        # 显示进程详情
        for pid in $pids; do
            local cmd=$(ps -p $pid -o command= 2>/dev/null | head -1)
            if [ -n "$cmd" ]; then
                echo "    - PID $pid: $cmd"
            fi
        done
    else
        echo "  ✗ 端口 $port 未监听"
    fi
    
    # 检查PID文件
    local pid_file="$PIDS_DIR/$pid_name.pid"
    if [ -f "$pid_file" ]; then
        local saved_pid=$(cat "$pid_file")
        if kill -0 "$saved_pid" 2>/dev/null; then
            echo "  ✓ PID文件有效 (PID: $saved_pid)"
        else
            echo "  ✗ PID文件无效 (PID: $saved_pid, 需清理)"
        fi
    else
        echo "  ? 未记录PID文件"
    fi
    
    echo ""
}

check_http() {
    local name=$1
    local port=$2
    local url=$3
    
    echo "$name:"
    
    # 检查端口是否监听
    if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        # 测试HTTP访问
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$url" 2>/dev/null)
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "404" ]; then
            echo "  ✓ 可访问 (HTTP: $http_code)"
            echo "  URL: $url"
        else
            echo "  ✗ 访问异常 (HTTP: $http_code)"
            echo "  URL: $url"
        fi
    else
        echo "  ✗ 服务未运行"
    fi
    
    echo ""
}

for service in "${services[@]}"; do
    IFS=':' read -r name port pid_name url <<< "$service"
    check_process "$name" "$port" "$pid_name"
done

echo "--- 服务访问测试 ---"
echo ""

for service in "${services[@]}"; do
    IFS=':' read -r name port pid_name url <<< "$service"
    check_http "$name" "$port" "$url"
done

echo "--- 磁盘使用情况 ---"
echo ""
df -h "$PROJECT_DIR" | tail -1

echo ""
echo "========================================="
echo "  检查完成"
echo "========================================="
echo ""
echo "启动服务: ./start-all.sh"
echo "停止服务: ./stop-all.sh"
echo ""