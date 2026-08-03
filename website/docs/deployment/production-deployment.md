---
title: 生产部署
description: MGAgent 生产环境部署指南，包括性能优化、安全配置和监控建议
slug: /deployment/production-deployment
---

# 生产部署

## 概述

本文档介绍如何将 MGAgent 部署到生产环境，确保系统的稳定性、安全性和可维护性。

## 生产环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| CPU | 4 核 | 8 核+ |
| 内存 | 8 GB | 16 GB+ |
| 磁盘 | 50 GB SSD | 200 GB+ SSD |
| Docker | 20.10+ | 24.x |
| 网络 | 稳定的互联网连接 | 100Mbps+ |

## 部署方案选择

### 推荐：MySQL + Milvus 方案

生产环境推荐使用 MySQL + Milvus 方案：

```bash
# 使用部署脚本（推荐）
cp .env.production.example .env.production  # 首次配置
./scripts/deploy.sh up

# 或手动分步部署
./scripts/docker-services.sh start          # 启动基础设施
docker compose -f docker-compose.prod.yml up -d --build  # 启动应用层
```

### 为什么选择 MySQL + Milvus

| 特性 | SQLite + ChromaDB | MySQL + Milvus |
|------|-------------------|----------------|
| 并发支持 | 单线程 | 高并发 |
| 数据量 | < 10万条 | 百万级 |
| 可靠性 | 无集群 | 主从/集群 |
| 备份恢复 | 手动文件复制 | 原生工具 |
| 监控能力 | 基础 | 完善 |

## 生产环境配置

### 1. 环境变量配置

```bash
# 创建生产环境配置
cat > .env.mysql << 'EOF'
# MySQL 配置
MYSQL_ROOT_PASSWORD=strong_root_password_2024
MYSQL_DATABASE=mgagent
MYSQL_USER=mgagent
MYSQL_PASSWORD=strong_password_2024
MYSQL_PORT=3306

# Milvus 配置
MILVUS_PORT=19530
MILVUS_GRPC_PORT=9091

# 服务端口
BACKEND_PORT=8000
ADMIN_BACKEND_PORT=8001
FRONTEND_PORT=3000
ADMIN_FRONTEND_PORT=3001
EOF
```

### 2. 修改默认密码

:::warning 安全警告
部署后 **立即** 修改默认密码！默认账号 `admin / admin123` 必须修改。
:::

通过 Admin 后台 → 系统管理 → 修改管理员密码。

### 3. 配置 HTTPS

使用 Nginx 或其他反向代理配置 HTTPS：

```nginx
# /etc/nginx/conf.d/mgagent.conf

upstream mgagent_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    # Chat 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
    }

    # Admin 前端
    location /admin/ {
        proxy_pass http://127.0.0.1:3001/;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }

    location /admin/api/ {
        proxy_pass http://127.0.0.1:8001;
    }
}
```

## 性能优化

### 数据库连接池

MySQL 连接池已在代码中优化：

```python
# app/db/database.py
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,      # 连接健康检查
    pool_recycle=3600,       # 连接回收时间
    pool_size=10,            # 连接池大小
    max_overflow=20,        # 最大溢出连接数
    echo=settings.DEBUG
)
```

### Milvus 索引优化

```python
# IVF_FLAT 索引，nlist 可根据数据量调整
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}

# 搜索时调整 nprobe 平衡精度和速度
search_params = {"metric_type": "L2", "params": {"nprobe": 16}}
```

### Docker 资源限制

在 Docker Compose 中设置资源限制：

```yaml
services:
  mgagent-backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 1G
          cpus: '1'
```

### Nginx 缓存配置

```nginx
# 启用 gzip 压缩
gzip on;
gzip_types application/json text/plain text/css application/javascript;
gzip_min_length 1024;

# 静态资源缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## 数据备份

### MySQL 定期备份

```bash
# 创建备份脚本
cat > /opt/backup-mysql.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

mysqldump -u root -p${MYSQL_ROOT_PASSWORD} mgagent | gzip > $BACKUP_DIR/mgagent_$DATE.sql.gz

# 保留最近 30 天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "备份完成: mgagent_$DATE.sql.gz"
EOF

# 添加到 crontab（每天凌晨 3 点备份）
crontab -e
0 3 * * * /opt/backup-mysql.sh
```

### 向量数据备份

Milvus 数据通过 Docker 卷持久化：

```bash
# 备份 MinIO 数据
docker run --rm -v minio_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/minio-backup.tar.gz /data

# 备份 Milvus 元数据
docker run --rm -v etcd_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/etcd-backup.tar.gz /data
```

## 监控与日志

### 健康检查

所有服务内置健康检查端点：

```bash
# Chat 后端
curl http://localhost:8000/api/health

# Admin 后端
curl http://localhost:8001/admin/api/health

# Milvus
curl http://localhost:19530/healthz

# MySQL
docker exec mgagent-mysql mysqladmin ping -h localhost
```

### 日志管理

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs --tail=100

# 基础设施日志
docker compose -f docker-compose.infra.yml logs --tail=100

# 实时监控
docker compose -f docker-compose.prod.yml logs -f
```

:::tip 日志轮转
建议配置 Docker 日志轮转，防止日志文件占用过多磁盘空间：

```yaml
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```
:::

## 更新与维护

### 版本更新流程

```bash
# 1. 拉取最新代码
cd /opt/MGAgent
git pull origin main

# 2. 备份数据
./scripts/deploy.sh down

# 3. 重新构建并启动
./scripts/deploy.sh up

# 4. 验证服务
./scripts/deploy.sh status
```

### 滚动更新

```bash
# 应用层可以独立更新，不影响基础设施
docker compose -f docker-compose.prod.yml up -d --build

# 基础设施更新需要停机
docker compose -f docker-compose.infra.yml down
docker compose -f docker-compose.infra.yml up -d
```

## 安全清单

- [ ] 修改默认管理员密码
- [ ] 配置 HTTPS / SSL 证书
- [ ] 设置强密码（MySQL、MinIO 等）
- [ ] 配置防火墙规则
- [ ] 禁用不必要的端口
- [ ] 定期更新系统和 Docker 镜像
- [ ] 配置数据备份策略
- [ ] 设置日志轮转
- [ ] 配置监控告警

## 相关文档

- [环境变量配置](/configuration/environment-variables)
- [Nginx 配置](/configuration/nginx)
- [Docker 配置](/configuration/docker)
- [故障排查](/troubleshooting/common-issues)