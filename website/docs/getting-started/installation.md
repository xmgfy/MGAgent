---
title: 安装指南
description: MGAgent 系统环境要求、依赖安装与配置说明
slug: /getting-started/installation
---

# 安装指南

## 环境要求

### Docker 部署方式（推荐）

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Docker | 20.10 | 24.x |
| Docker Compose | 2.0 | 2.20+ |
| 操作系统 | macOS 11+ / Ubuntu 20.04+ / CentOS 7+ | 最新稳定版 |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 10 GB | 50 GB+ |

### 本地开发方式

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Python | 3.10 | 3.11+ |
| Node.js | 18 | 20 LTS |
| npm | 9 | 10+ |
| pip | 23+ | 最新版 |

## 安装 Docker

:::info macOS 用户
推荐使用 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 安装，支持 Apple Silicon 和 Intel 芯片。
:::

```bash
# 检查 Docker 是否已安装
docker --version
docker compose version
```

### Ubuntu / Debian

```bash
# 更新包索引
sudo apt-get update

# 安装 Docker
sudo apt-get install -y docker.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl enable docker
sudo systemctl start docker

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
newgrp docker
```

### CentOS / RHEL

```bash
# 安装 Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### 国内镜像源配置（可选）

```bash
# 创建 Docker 配置目录
mkdir -p ~/.docker

# 配置国内镜像源
cat > ~/.docker/daemon.json << 'EOF'
{
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

# 重启 Docker
sudo systemctl restart docker
```

:::warning 注意
镜像源配置需要重启 Docker 才能生效。macOS 用户可在 Docker Desktop → Settings → Docker Engine 中配置。
:::

## 安装项目

### 克隆代码

```bash
# 克隆项目
git clone https://github.com/xmgfy/MGAgent.git

# 进入项目目录
cd MGAgent
```

### 配置环境变量

```bash
# 生产环境：复制配置模板
cp .env.production.example .env.production

# 根据实际需求修改配置
vim .env.production
```

:::tip 本地开发
本地开发模式下，`start-all.sh` 脚本会自动加载对应模式（sqlite/mysql）的环境变量，无需手动配置。
:::

## 验证安装

### Docker 方式验证

```bash
# 查看 Docker 状态
docker info

# 查看 Docker Compose 版本
docker compose version
```

### 本地开发验证

```bash
# 检查 Python 版本
python3 --version

# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version
```

## 下一步

环境准备就绪后，继续阅读 [快速开始](/getting-started/quick-start) 章节，选择适合您的部署方式。