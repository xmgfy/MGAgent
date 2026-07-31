---
title: 常见问题
description: MGAgent 使用过程中常见问题解答，涵盖部署、配置、功能等方面
slug: /troubleshooting/faq
---

# 常见问题

## 部署相关

### Q: 启动脚本提示 Python 路径错误？

**问题：** `start-all.sh` 提示找不到 Python 或 uvicorn。

**解决：**

```bash
# 检查 Python 路径
which python3
python3 --version

# 修改 start-all.sh 中的 PYTHON 变量
# 默认设置为 /opt/anaconda3/bin/python3
PYTHON="/usr/bin/python3"  # 修改为实际路径
```

### Q: Docker Compose 命令找不到？

**问题：** 执行 `docker compose` 或 `docker-compose` 提示命令不存在。

**解决：**

```bash
# Docker Desktop 用户
# Docker Compose 已内置，使用 docker compose（无横线）

# 独立安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证
docker compose version
```

### Q: 端口被占用怎么办？

**问题：** 启动服务时提示端口 8000/8001/5173/5174 已被占用。

**解决：**

```bash
# 查看端口占用
lsof -i :8000 :8001 :5173 :5174

# 使用一键脚本停止
./scripts/stop-all.sh

# 或手动终止占用进程
kill -9 $(lsof -t -i:8000)
```

### Q: Docker 镜像拉取速度慢？

**解决：**

```bash
# 配置国内镜像源
./scripts/docker-services.sh setup-mirror

# 预热所有必需镜像
./scripts/docker-services.sh preload
```

### Q: MySQL 容器启动失败？

**问题：** MySQL 容器不断重启或健康检查失败。

**解决：**

```bash
# 查看 MySQL 日志
docker logs mgagent-mysql --tail=100

# 常见原因：
# 1. 端口冲突 - 修改 MYSQL_PORT
# 2. 权限问题 - 检查数据卷权限
# 3. 内存不足 - 增加系统内存

# 清理并重建
docker compose -f docker-compose.infra.yml down -v
docker compose -f docker-compose.infra.yml up -d
```

## 配置相关

### Q: 如何切换技术栈方案？

**解决：**

通过切换 `.env` 文件来选择数据库方案：

```bash
# 切换到 MySQL 方案
cp .env.mysql .env

# 切换到 SQLite 方案
cp .env.sqlite .env

# 重启服务生效
```

### Q: 模型配置在哪里修改？

**问题：** 想修改 LLM 模型配置，但找不到配置文件。

**解决：**

MGAgent 使用 **数据库驱动** 的模型配置：

1. 启动系统
2. 登录 Admin 后台 (http://localhost:5174 或 http://localhost:3001)
3. 进入 **模型管理** 页面
4. 在此处增删改查模型配置

:::warning 注意
模型配置不再使用静态文件，统一在 Admin 后台管理。
:::

### Q: 如何配置多个 LLM 模型？

**解决：**

在 Admin 后台的 **模型管理** 页面：

1. 点击 **新增模型**
2. 填写模型信息（名称、API Key、API Base、模型名称）
3. 保存后点击 **测试连接** 验证
4. 点击 **启用** 设为当前活跃模型

系统支持多个模型配置，但同一时间只有一个活跃。

### Q: 修改模型配置后需要重启吗？

**不需要。** MGAgent 的 Agent 每次对话时都会从数据库读取当前活跃的模型配置，修改立即生效。

## 功能相关

### Q: 为什么对话时提示"未配置有效的模型"？

**问题：** Agent 抛出 `ValueError: 未配置有效的模型，请在admin管理端配置并启用模型`。

**解决：**

1. 确认已登录 Admin 后台
2. 进入 **模型管理** 页面
3. 创建至少一个模型配置
4. 点击 **测试连接** 确认可用
5. 点击 **启用** 激活模型

### Q: 知识库支持哪些文件格式？

**支持的格式：**

| 格式 | 扩展名 |
|------|--------|
| PDF | `.pdf` |
| 文本 | `.txt` |
| Word | `.docx` |
| Markdown | `.md` |

### Q: 知识库检索效果不好？

**优化建议：**

1. 确保文档内容质量
2. 拆分长文档为多个小文档
3. 使用更精确的检索查询
4. 调整向量检索参数（nprobe、k 值）

### Q: 如何使用数据库查询功能？

Agent 的数据库查询工具可以：

- 自动生成 SQL 查询
- 查看数据库表结构
- 检索业务数据

确保在 Admin 后台配置了有效的数据库连接。

### Q: 匿名用户的使用限制？

匿名用户默认可使用 **3 次** 对话。注册并经管理员审批后可获得完整使用权限。

### Q: 用户注册后多久可以使用？

新用户需要管理员审批：

1. 注册后状态为 `pending`
2. 管理员在 **用户管理** 页面审批
3. 审批通过后状态变为 `active`
4. 用户即可正常使用

## 前端相关

### Q: 前端页面空白？

**排查步骤：**

```bash
# 1. 检查前端是否运行
./scripts/status.sh

# 2. 检查浏览器控制台错误
# 打开 DevTools Console 查看

# 3. 检查 API 是否可达
curl http://localhost:8000/api/health
curl http://localhost:8001/admin/api/health

# 4. 检查 Nginx 代理配置
cat mgagent-frontend/nginx.conf
```

### Q: 前端 API 请求 404？

**解决：**

- 本地开发模式：前端通过 Vite 代理，请确认 `vite.config.ts` 中的代理配置
- Docker 模式：通过 Nginx 代理，请确认 `nginx.conf` 中的 `proxy_pass` 配置

### Q: 登录后跳转到首页？

这是正常行为。登录成功后，系统会跳转到首页并显示对话界面。

## 升级相关

### Q: 如何升级到最新版本？

```bash
# 1. 拉取最新代码
cd /path/to/MGAgent
git pull origin main

# 2. 停止当前服务
./scripts/deploy.sh stop

# 3. 重新部署
./scripts/deploy.sh sqlite   # 或 mysql

# 4. 检查状态
./scripts/deploy.sh status
```

### Q: 升级会丢失数据吗？

- **SQLite 方案**：数据存储在 `mgagent-backend/data/` 目录，升级不会删除
- **MySQL 方案**：数据存储在 Docker 数据卷，升级不会删除
- 建议升级前备份数据

### Q: 如何备份数据？

```bash
# SQLite 方案
cp -r mgagent-backend/data/ backup_$(date +%Y%m%d)

# MySQL 方案
docker exec mgagent-mysql mysqldump -u root -p mgagent > backup.sql
```

## 获取帮助

:::info 需要更多帮助
如果本文档未能解决您的问题，可以：

1. 查看 [故障排查](/troubleshooting/common-issues) 获取更详细的技术排查
2. 查看 [脚本使用指南](/development/scripts) 了解运维脚本
3. 查看 [API 参考](/development/api-reference) 了解接口细节
4. 提交 Issue 到 GitHub 仓库
:::