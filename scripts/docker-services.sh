#!/bin/bash
# MGAgent Docker 服务管理脚本
# 用于启动/停止 MySQL 和 Milvus 服务，支持国内镜像源加速

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env.docker"
DAEMON_JSON="$HOME/.docker/daemon.json"

# 国内 Docker 镜像源列表
MIRROR_SOURCES=(
    "https://docker.1panel.live"
    "https://docker.1ms.run"
    "https://docker.m.daocloud.io"
    "https://hub-mirror.c.163.com"
    "https://docker.mirrors.ustc.edu.cn"
    "https://mirror.ccs.tencentyun.com"
)

# 需要预热的镜像列表（MySQL + Milvus 相关）
MYSQL_MILVUS_IMAGES=(
    "mysql:8.0"
    "milvusdb/milvus:v2.4.12"
    "docker.1ms.run/quay.io/coreos/etcd:v3.5.5"
    "minio/minio:RELEASE.2023-03-20T20-16-18Z"
    "zilliz/attu:v2.4"
)

# 应用构建所需的基础镜像
BUILD_IMAGES=(
    "python:3.10-slim"
    "node:18-alpine"
    "nginx:alpine"
)

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
    echo "  preload     预热所有镜像（使用国内镜像源）"
    echo "  setup-mirror 配置 Docker 国内镜像源"
    echo "  check-mirror 检查当前镜像源配置"
    echo "  help        显示帮助信息"
}

# 配置 Docker 国内镜像源
setup_mirror() {
    echo -e "${CYAN}📦 配置 Docker 国内镜像源...${NC}"
    
    if [ ! -d "$HOME/.docker" ]; then
        mkdir -p "$HOME/.docker"
    fi
    
    # 备份原配置
    if [ -f "$DAEMON_JSON" ] && [ ! -f "${DAEMON_JSON}.bak" ]; then
        cp "$DAEMON_JSON" "${DAEMON_JSON}.bak"
        echo -e "${YELLOW}已备份原配置到 ${DAEMON_JSON}.bak${NC}"
    fi
    
    # 读取现有配置或创建新配置
    local existing_config="{}"
    if [ -f "$DAEMON_JSON" ]; then
        existing_config=$(cat "$DAEMON_JSON" 2>/dev/null || echo "{}")
    fi
    
    # 使用 python3 合并配置（如果可用）
    if command -v python3 &>/dev/null; then
        python3 << PYEOF
import json
import sys

existing = json.loads('''${existing_config}''')

# 添加镜像源（去重）
existing_mirrors = existing.get("registry-mirrors", [])
new_mirrors = [
    "https://docker.1panel.live",
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io",
    "https://hub-mirror.c.163.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com"
]

for mirror in new_mirrors:
    if mirror not in existing_mirrors:
        existing_mirrors.append(mirror)

existing["registry-mirrors"] = existing_mirrors

# 确保其他默认配置存在
if "builder" not in existing:
    existing["builder"] = {
        "gc": {
            "defaultKeepStorage": "20GB",
            "enabled": True
        }
    }
if "experimental" not in existing:
    existing["experimental"] = False

with open("$DAEMON_JSON", "w") as f:
    json.dump(existing, f, indent=2)

print("✅ 镜像源配置已更新")
PYEOF
    else
        # 如果没有 python3，使用简单的 cat 方式（完全覆盖）
        cat > "$DAEMON_JSON" << 'EOF'
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io",
    "https://hub-mirror.c.163.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
        echo -e "${GREEN}✅ 镜像源配置已写入 ${DAEMON_JSON}${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}⚠️  重要：镜像源配置需要重启 Docker 才能生效${NC}"
    echo -e "${YELLOW}   macOS: Docker Desktop -> Settings -> 点击 'Restart'${NC}"
    echo -e "${YELLOW}   Linux: sudo systemctl restart docker${NC}"
    echo ""
    
    # 显示配置的镜像源
    echo -e "${CYAN}已配置的镜像源:${NC}"
    for mirror in "${MIRROR_SOURCES[@]}"; do
        echo -e "  ${GREEN}•${NC} $mirror"
    done
}

# 检查当前镜像源配置
check_mirror() {
    echo -e "${CYAN}🔍 检查 Docker 镜像源配置...${NC}"
    echo ""
    
    if [ -f "$DAEMON_JSON" ]; then
        echo -e "${BLUE}daemon.json 路径:${NC} $DAEMON_JSON"
        echo -e "${BLUE}配置内容:${NC}"
        cat "$DAEMON_JSON" | python3 -m json.tool 2>/dev/null || cat "$DAEMON_JSON"
    else
        echo -e "${RED}❌ 未找到 daemon.json 配置文件${NC}"
        echo -e "${YELLOW}请运行 '$0 setup-mirror' 配置镜像源${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${BLUE}当前 Docker 镜像源:${NC}"
    docker info 2>/dev/null | grep -A 10 "Registry Mirrors" || echo "  获取失败"
}

# 超时执行命令（兼容 macOS，原生 timeout 不可用时使用 perl）
timeout_cmd() {
    local seconds=$1
    shift
    if command -v timeout &>/dev/null; then
        timeout "$seconds" "$@"
    elif command -v gtimeout &>/dev/null; then
        gtimeout "$seconds" "$@"
    else
        # macOS 自带 perl，使用 perl 实现超时
        perl -e '
            my $timeout = shift;
            my $pid = fork();
            if (!defined $pid) { die "fork failed\n"; }
            if ($pid == 0) {
                exec @ARGV;
                exit 1;
            }
            my $alarm = $SIG{ALRM};
            $SIG{ALRM} = sub { kill 9, $pid; exit 1; };
            alarm $timeout;
            waitpid($pid, 0);
            alarm 0;
            $SIG{ALRM} = $alarm;
            exit $?;
        ' "$seconds" "$@" 2>/dev/null
    fi
}

# 预热单个镜像
preload_image() {
    local image=$1
    
    echo -ne "  拉取 ${CYAN}$image${NC} ... "
    
    # 尝试直接拉取（使用 Docker 配置的镜像源）
    if timeout_cmd 300 docker pull "$image" 2>/dev/null; then
        echo -e "${GREEN}✅ 成功${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}⏱️  超时或失败${NC}"
    echo -ne "    尝试通过国内镜像源拉取... "
    
    # 对于 Docker Hub 的镜像，尝试通过国内镜像源代理拉取
    if [[ ! "$image" == *"/"* ]] || [[ "$image" == docker.io/* ]] || [[ ! "$image" == *"."*"/"* ]]; then
        # 这是 Docker Hub 的镜像，尝试通过镜像源代理拉取
        local proxy_success=false
        for mirror in "${MIRROR_SOURCES[@]}"; do
            local mirror_image="${mirror#https://}/${image}"
            echo -ne "\n      尝试 ${mirror} ... "
            if timeout_cmd 120 docker pull "$mirror_image" 2>/dev/null; then
                # 重新标记为原始名称
                docker tag "$mirror_image" "$image" 2>/dev/null
                docker rmi "$mirror_image" 2>/dev/null
                echo -ne "${GREEN}✅ 成功${NC}"
                proxy_success=true
                break
            fi
        done
        if [ "$proxy_success" = true ]; then
            echo ""
            return 0
        fi
    fi
    
    # 尝试直接拉取 Docker Hub（不使用 timeout，可能较慢）
    echo -ne "\n      直接从 Docker Hub 拉取... "
    if docker pull "$image" 2>/dev/null; then
        echo -ne "${GREEN}✅ 成功${NC}"
        echo ""
        return 0
    fi
    
    echo -e "${RED}❌ 拉取失败，请手动拉取或检查网络${NC}"
    return 1
}

# 预热所有镜像
preload_images() {
    echo -e "${CYAN}🚀 预热 MGAgent 所需的 Docker 镜像...${NC}"
    echo ""
    
    # 检查 Docker 是否运行
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📦 预热 MySQL + Milvus 相关镜像:${NC}"
    for image in "${MYSQL_MILVUS_IMAGES[@]}"; do
        preload_image "$image"
    done
    
    echo ""
    echo -e "${BLUE}📦 预热应用构建镜像:${NC}"
    for image in "${BUILD_IMAGES[@]}"; do
        preload_image "$image"
    done
    
    echo ""
    echo -e "${GREEN}✅ 镜像预热完成！${NC}"
    echo -e "${YELLOW}💡 提示：如果某些镜像拉取失败，可以稍后重试或手动拉取${NC}"
}

start_services() {
    echo -e "${BLUE}🚀 启动 MGAgent 基础设施服务...${NC}"
    
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    fi
    
    # 检查 Docker 镜像源配置
    if [ -f "$DAEMON_JSON" ]; then
        local mirror_count=$(grep -c "registry-mirrors" "$DAEMON_JSON" 2>/dev/null || echo "0")
        if [ "$mirror_count" -gt 0 ]; then
            echo -e "${GREEN}✓ Docker 镜像源已配置${NC}"
        else
            echo -e "${YELLOW}⚠️  未配置 Docker 镜像源，拉取速度可能较慢${NC}"
            echo -e "${YELLOW}   运行 '$0 setup-mirror' 配置国内镜像源${NC}"
        fi
    fi
    
    # 检查是否需要预热镜像
    local need_preload=false
    for image in "${MYSQL_MILVUS_IMAGES[@]}"; do
        if ! docker image inspect "$image" >/dev/null 2>&1; then
            need_preload=true
            break
        fi
    done
    
    if [ "$need_preload" = true ]; then
        echo ""
        echo -e "${YELLOW}📥 检测到部分镜像不存在，开始拉取...${NC}"
        preload_images
        echo ""
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
    echo -e "   Attu UI:    http://localhost:8003"
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
    preload)
        preload_images
        ;;
    setup-mirror)
        setup_mirror
        ;;
    check-mirror)
        check_mirror
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
