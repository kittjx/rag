# Redis Docker 配置指南

## 🔴 Redis 与 Docker

本项目支持使用 Docker 运行 Redis，这是推荐的方式，因为：
- ✅ 无需在本地安装 Redis
- ✅ 环境隔离，不影响系统
- ✅ 易于管理和重启
- ✅ 数据持久化

## 🚀 快速启动

### 方式 1: 使用 Make (推荐)

```bash
# 启动 Redis
make redis-start

# 查看日志
make redis-logs

# 停止 Redis
make redis-stop

# 连接 Redis CLI
make redis-cli
```

### 方式 2: 使用 docker-compose

```bash
# 启动
docker-compose up -d redis

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f redis

# 停止
docker-compose stop redis

# 删除容器（保留数据）
docker-compose down

# 删除容器和数据
docker-compose down -v
```

### 方式 3: 直接使用 Docker

```bash
# 启动 Redis
docker run -d \
  --name rag-redis \
  -p 6379:6379 \
  -v rag-redis-data:/data \
  redis:alpine \
  redis-server --appendonly yes

# 查看日志
docker logs -f rag-redis

# 停止
docker stop rag-redis

# 启动已存在的容器
docker start rag-redis

# 删除容器
docker rm rag-redis
```

## 🔧 配置说明

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine          # 使用轻量级 Alpine 版本
    container_name: rag-redis      # 容器名称
    ports:
      - "6379:6379"                # 端口映射
    volumes:
      - redis-data:/data           # 数据持久化
    command: redis-server --appendonly yes  # 启用 AOF 持久化
    restart: unless-stopped        # 自动重启
    healthcheck:                   # 健康检查
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

### 环境变量 (.env)

```env
# Redis 连接地址
REDIS_URL=redis://localhost:6379

# 如果 Redis 有密码
# REDIS_URL=redis://:password@localhost:6379

# 如果使用不同的端口
# REDIS_URL=redis://localhost:6380
```

## 🔍 验证 Redis 运行

### 方式 1: 使用项目检查脚本

```bash
python check_setup.py
```

应该看到：
```
🔴 检查Redis...
   ℹ️  连接地址: redis://localhost:6379
   ✅ Redis连接成功
   ℹ️  Redis版本: 8.4.0
```

### 方式 2: 使用 Docker 命令

```bash
# 检查容器状态
docker ps | grep redis

# 应该看到类似输出：
# CONTAINER ID   IMAGE          STATUS         PORTS                    NAMES
# abc123def456   redis:alpine   Up 5 minutes   0.0.0.0:6379->6379/tcp   rag-redis
```

### 方式 3: 使用 redis-cli

```bash
# 如果安装了 redis-cli
redis-cli ping
# 应该返回: PONG

# 或使用 Docker
docker exec rag-redis redis-cli ping
# 应该返回: PONG
```

### 方式 4: 使用 Python

```bash
python3 -c "
import redis
client = redis.Redis(host='localhost', port=6379)
print('Redis 版本:', client.info()['redis_version'])
print('连接成功!')
"
```

## 📊 Redis 管理

### 查看 Redis 信息

```bash
# 使用 Docker
docker exec rag-redis redis-cli INFO

# 查看内存使用
docker exec rag-redis redis-cli INFO memory

# 查看统计信息
docker exec rag-redis redis-cli INFO stats
```

### 清空缓存

```bash
# 清空所有数据
docker exec rag-redis redis-cli FLUSHALL

# 清空当前数据库
docker exec rag-redis redis-cli FLUSHDB
```

### 查看缓存键

```bash
# 查看所有键
docker exec rag-redis redis-cli KEYS '*'

# 查看特定前缀的键
docker exec rag-redis redis-cli KEYS 'chat:*'
```

## 🛠️ 故障排除

### 问题 1: 端口已被占用

```bash
# 检查端口占用
lsof -i :6379

# 停止占用端口的进程
kill -9 <PID>

# 或使用不同端口
docker run -d -p 6380:6379 --name rag-redis redis:alpine
# 然后修改 .env: REDIS_URL=redis://localhost:6380
```

### 问题 2: 容器无法启动

```bash
# 查看详细日志
docker logs rag-redis

# 删除并重新创建
docker rm -f rag-redis
make redis-start
```

### 问题 3: 数据丢失

```bash
# 检查数据卷
docker volume ls | grep redis

# 查看数据卷详情
docker volume inspect rag-redis-data

# 备份数据
docker run --rm -v rag-redis-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/redis-backup.tar.gz -C /data .

# 恢复数据
docker run --rm -v rag-redis-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/redis-backup.tar.gz -C /data
```

### 问题 4: 连接超时

```bash
# 检查防火墙
sudo ufw status

# 检查 Docker 网络
docker network inspect bridge

# 尝试使用 127.0.0.1 而不是 localhost
# .env: REDIS_URL=redis://127.0.0.1:6379
```

## 💡 最佳实践

1. **使用 docker-compose**: 更易于管理和配置
2. **启用持久化**: 使用 AOF 或 RDB 避免数据丢失
3. **设置密码**: 生产环境建议设置密码
4. **限制内存**: 避免 Redis 占用过多内存
5. **定期备份**: 重要数据定期备份

## 🔒 安全配置（生产环境）

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --requirepass your_password_here
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
    environment:
      - REDIS_PASSWORD=your_password_here
```

对应的 .env 配置：
```env
REDIS_URL=redis://:your_password_here@localhost:6379
```

## 📚 相关文档

- [Redis 官方文档](https://redis.io/documentation)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Redis Python 客户端](https://redis-py.readthedocs.io/)

## ✅ 检查清单

- [ ] Docker 已安装并运行
- [ ] Redis 容器已启动
- [ ] 端口 6379 未被占用
- [ ] .env 文件配置正确
- [ ] `python check_setup.py` 通过
- [ ] 应用可以连接 Redis

完成以上检查后，你的 Redis 就配置好了！🎉

