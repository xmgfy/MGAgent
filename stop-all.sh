#!/bin/bash

echo "========================================="
echo "  MGAgent 一键停止脚本"
echo "========================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_DIR="$PROJECT_DIR/.pids"

# 停止单个服务
stop_service() {
    local name=$1
    local port=$2
    local pid_file="$PIDS_DIR/$3.pid"
    
    echo "停止 $name (端口: $port)"
    
    # 收集所有需要终止的进程
    local target_pids=""
    
    # 1. 从PID文件读取（可能包含多个PID，换行或空格分隔）
    if [ -f "$pid_file" ]; then
        local saved_pids=$(cat "$pid_file" | tr '\n' ' ')
        for saved_pid in $saved_pids; do
            if [ -n "$saved_pid" ] && kill -0 "$saved_pid" 2>/dev/null; then
                target_pids="$target_pids $saved_pid"
                echo "  从PID文件找到进程: $saved_pid"
            elif [ -n "$saved_pid" ]; then
                echo "  PID文件中的进程已不存在: $saved_pid"
            fi
        done
    fi
    
    # 2. 通过端口查找进程
    local port_pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$port_pids" ]; then
        target_pids="$target_pids $port_pids"
        echo "  通过端口找到进程: $port_pids"
    fi
    
    # 3. 如果没有找到进程，尝试通过命令名查找（适用于前端服务）
    if [ -z "$target_pids" ]; then
        if [ "$3" = "frontend" ] || [ "$3" = "admin-frontend" ]; then
            local cmd_pids=$(pgrep -f "vite" 2>/dev/null)
            if [ -n "$cmd_pids" ]; then
                target_pids="$target_pids $cmd_pids"
                echo "  通过命令名找到进程: $cmd_pids"
            fi
        elif [ "$3" = "backend" ] || [ "$3" = "admin-backend" ]; then
            local cmd_pids=$(pgrep -f "uvicorn" 2>/dev/null)
            if [ -n "$cmd_pids" ]; then
                target_pids="$target_pids $cmd_pids"
                echo "  通过命令名找到进程: $cmd_pids"
            fi
        fi
    fi
    
    # 去重
    target_pids=$(echo "$target_pids" | tr ' ' '\n' | sort -u | tr '\n' ' ')
    
    if [ -z "$target_pids" ]; then
        echo "  ? $name 未在运行"
    else
        echo "  准备终止进程: $target_pids"
        
        # 获取所有进程组ID
        local pgids=""
        for pid in $target_pids; do
            local pgid=$(ps -o pgid= "$pid" | grep -o '[0-9]*')
            if [ -n "$pgid" ]; then
                pgids="$pgids $pgid"
            fi
        done
        pgids=$(echo "$pgids" | tr ' ' '\n' | sort -u | tr '\n' ' ')
        
        # 步骤1: 发送 SIGTERM 优雅停止进程组
        if [ -n "$pgids" ]; then
            echo "  [步骤1] 优雅停止进程组: $pgids"
            for pgid in $pgids; do
                kill -TERM -"$pgid" 2>/dev/null
            done
        else
            echo "  [步骤1] 优雅停止进程: $target_pids"
            kill -TERM $target_pids 2>/dev/null
        fi
        
        # 等待3秒
        sleep 3
        
        # 步骤2: 检查是否还有残留进程
        local remaining=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$remaining" ]; then
            echo "  [步骤2] 仍有残留进程: $remaining"
            
            # 获取残留进程的进程组
            local remaining_pgids=""
            for pid in $remaining; do
                local pgid=$(ps -o pgid= "$pid" | grep -o '[0-9]*')
                if [ -n "$pgid" ]; then
                    remaining_pgids="$remaining_pgids $pgid"
                fi
            done
            remaining_pgids=$(echo "$remaining_pgids" | tr ' ' '\n' | sort -u | tr '\n' ' ')
            
            # 发送 SIGKILL 强制终止
            if [ -n "$remaining_pgids" ]; then
                echo "  [步骤2] 强制终止进程组: $remaining_pgids"
                kill -9 -$remaining_pgids 2>/dev/null
            else
                echo "  [步骤2] 强制终止进程: $remaining"
                kill -9 $remaining 2>/dev/null
            fi
            
            sleep 1
        fi
        
        # 步骤3: 最后检查并清理
        local final_check=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$final_check" ]; then
            echo "  [步骤3] 清理顽固进程: $final_check"
            kill -9 $final_check 2>/dev/null
            sleep 1
        fi
        
        echo "  ✓ $name 已停止"
    fi
    
    # 清理PID文件
    if [ -f "$pid_file" ]; then
        rm -f "$pid_file"
        echo "  清理PID文件"
    fi
}

echo "[1/4] 停止 mgagent-backend"
echo "-----------------------------------------"
stop_service "mgagent-backend" "8000" "backend"
echo ""

echo "[2/4] 停止 mgagent-admin-backend"
echo "-----------------------------------------"
stop_service "mgagent-admin-backend" "8001" "admin-backend"
echo ""

echo "[3/4] 停止 mgagent-frontend"
echo "-----------------------------------------"
stop_service "mgagent-frontend" "5173" "frontend"
echo ""

echo "[4/4] 停止 mgagent-admin-frontend"
echo "-----------------------------------------"
stop_service "mgagent-admin-frontend" "5174" "admin-frontend"
echo ""

echo "========================================="
echo "  所有服务已停止!"
echo "========================================="
echo ""

# 验证所有服务是否已停止
echo "验证服务状态:"
echo ""

check_port() {
    if lsof -Pi ":$1" -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✗ 端口 $1 仍在监听"
        return 1
    else
        echo "✓ 端口 $1 已释放"
        return 0
    fi
}

all_clean=true
check_port 8000 || all_clean=false
check_port 8001 || all_clean=false
check_port 5173 || all_clean=false
check_port 5174 || all_clean=false

echo ""
if [ "$all_clean" = true ]; then
    echo "所有端口已成功释放!"
else
    echo "警告: 部分端口仍在占用，请手动检查!"
    echo "可使用命令: lsof -i :8000 :8001 :5173 :5174"
fi
echo ""
echo "启动服务请运行: ./start-all.sh"
echo ""