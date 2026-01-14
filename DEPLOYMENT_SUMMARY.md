
### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d api

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
docker-compose logs -f api
docker-compose logs -f web
```

### 知识库管理

```bash
# 构建知识库
docker-compose exec api python scripts/build_knowledge_base.py

# 查看统计
docker-compose exec api python scripts/manage_kb.py stats

# 列出文档
docker-compose exec api python scripts/manage_kb.py list
```

### 调试

```bash
# 进入容器
docker-compose exec api bash

# 查看环境变量
docker-compose exec api env

# 测试 Redis 连接
docker-compose exec api ping redis
docker-compose exec redis redis-cli ping
```

### 水平扩展

```bash
# 扩展 API 服务到 3 个实例
docker-compose up -d --scale api=3

# 需要配置负载均衡器（Nginx）
```

### 使用 Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署 stack
docker stack deploy -c docker-compose.yml rag

# 扩展服务
docker service scale rag_api=3
```

### 常见问题

1. **容器无法启动**
   ```bash
   docker-compose logs api
   docker-compose config
   ```

2. **无法连接 Redis**
   ```bash
   docker-compose exec api ping redis
   docker network inspect rag_rag-network
   ```

3. **内存不足**
   ```bash
   docker stats
   # 增加 Docker Desktop 内存限制
   ```

4. **端口冲突**
   ```bash
   # 修改 docker-compose.yml 中的端口映射
   ports:
     - "9000:8000"  # 使用 9000 代替 8000
   ```
