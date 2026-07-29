---
title: Nginx 配置
description: MGAgent Nginx 反向代理配置，包括前端部署、API 代理和 HTTPS 设置
slug: /configuration/nginx
---

# Nginx 配置

## 概述

MGAgent 前端（Chat 和 Admin）使用 Nginx 作为 Web 服务器，提供静态文件服务和 API 反向代理。

## 内置 Nginx 配置

每个前端项目都内置了 Nginx 配置文件：

- `mgagent-frontend/nginx.conf` - Chat 前端配置
- `mgagent-admin-frontend/nginx.conf` - Admin 前端配置

## Chat 前端 Nginx 配置

```nginx
server {
    listen 80;
    server_name localhost;

    # 静态文件根目录
    root /usr/share/nginx/html;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types application/json text/plain text/css application/javascript;
    gzip_min_length 1024;

    # API 代理到 Chat 后端
    location /api/ {
        proxy_pass http://mgagent-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式响应支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # Admin API 代理
    location /admin/api/ {
        proxy_pass http://mgagent-admin-backend:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA 路由回退
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Admin 前端 Nginx 配置

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # API 代理
    location /admin/api/ {
        proxy_pass http://mgagent-admin-backend:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://mgagent-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SPA 路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

## 生产环境配置

### HTTPS 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 前端静态文件
    root /var/www/mgagent;
    index index.html;

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    location /admin/api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # SPA 路由
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 多站点配置

```nginx
# /etc/nginx/conf.d/mgagent-chat.conf
server {
    listen 443 ssl;
    server_name chat.your-domain.com;
    # ... Chat 前端配置
}

# /etc/nginx/conf.d/mgagent-admin.conf
server {
    listen 443 ssl;
    server_name admin.your-domain.com;
    # ... Admin 前端配置
}
```

### 性能优化

```nginx
# Gzip 压缩优化
gzip on;
gzip_comp_level 6;
gzip_min_length 256;
gzip_buffers 16 8k;
gzip_http_version 1.1;
gzip_vary on;
gzip_proxied any;
gzip_types
    application/json
    application/javascript
    application/xml
    text/plain
    text/css
    text/javascript
    text/xml
    image/svg+xml;

# 客户端缓存
location ~* \.(js|css|woff2?)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Access-Control-Allow-Origin *;
}

# 图片缓存
location ~* \.(png|jpg|jpeg|gif|ico|svg)$ {
    expires 30d;
    add_header Cache-Control "public";
}

# WebSocket 支持（如需实时功能）
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Docker 中的 Nginx

### 前端 Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 创建缓存目录
RUN mkdir -p /var/cache/nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 健康检查

```nginx
# Nginx 健康检查端点
location = /health {
    access_log off;
    return 200 'OK';
    add_header Content-Type text/plain;
}
```

## 安全配置

### 基础安全头

```nginx
server {
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 隐藏 Nginx 版本
    server_tokens off;

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }
}
```

### 请求限制

```nginx
# 限制请求大小
client_max_body_size 50M;

# 限制请求频率
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}

location /api/auth/login {
    limit_req zone=login burst=3 nodelay;
    proxy_pass http://backend;
}
```

## 相关文档

- [生产部署](/deployment/production-deployment)
- [Docker 配置](/configuration/docker)
- [环境变量配置](/configuration/environment-variables)