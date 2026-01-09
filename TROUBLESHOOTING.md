# 故障排查指南

## 常见问题和解决方案

### 问题1: Web界面无法连接到API (ERR_CONNECTION_REFUSED)

**症状**:
```
POST http://localhost:8000/api/v1/chat/stream net::ERR_CONNECTION_REFUSED
发送消息失败: TypeError: Failed to fetch
```

**原因**: API 端口未正确映射到主机

**诊断**:
```bash
# 运行诊断脚本
bash diagnose-connection.sh

# 或手动检查
docker ps | grep rag-api
```

**期望输出**:
```
rag-api ... 0.0.0.0:8000->8000/tcp ...  # ✅ 正确
```

**错误输出**:
```
rag-api ... 8000/tcp ...  # ❌ 端口未映射
```

**解决方案**:

1. **重启容器**（推荐）:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **检查 docker-compose.yml**:
   确保 API 服务有正确的端口映射：
   ```yaml
   api:
     ports:
       - "8000:8000"  # 必须有这一行
   ```

3. **验证修复**:
   ```bash
   # 测试 API 连接
   curl http://localhost:8000/health
   
   # 应该返回:
   # {"status":"healthy","timestamp":...}
   ```

4. **刷新浏览器**:
   - 清除缓存或硬刷新 (Ctrl+Shift+R / Cmd+Shift+R)
   - 重新访问 http://localhost:8080

---

### 问题2: 容器启动但端口未绑定

**症状**: 容器运行但无法从主机访问

**解决方案**:
```bash
# 1. 停止所有容器
docker-compose down

# 2. 检查端口是否被占用
lsof -i :8000
lsof -i :8080

# 3. 如果端口被占用，停止占用进程或修改端口
# 修改 docker-compose.yml:
# ports:
#   - "9000:8000"  # 使用 9000 代替 8000

# 4. 重新启动
docker-compose up -d
```

---

### 问题3: Redis 连接失败

**症状**: API 日志显示 Redis 连接错误

**解决方案**:
```bash
# 1. 检查 Redis 状态
docker-compose ps redis

# 2. 测试 Redis 连接
docker-compose exec redis redis-cli ping
# 应该返回: PONG

# 3. 从 API 容器测试
docker-compose exec api ping redis

# 4. 重启 Redis
docker-compose restart redis
```

---

### 问题4: 模型下载失败

**症状**: API 启动时卡在模型下载

**解决方案**:

1. **手动下载模型**:
   ```bash
   docker-compose exec api python -c "
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('BAAI/bge-large-zh')
   print('模型下载完成')
   "
   ```

2. **使用本地模型**:
   ```bash
   # 在主机上下载模型
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-zh')"
   
   # 模型会保存在 ~/.cache/huggingface/
   # 挂载到容器:
   # volumes:
   #   - ~/.cache/huggingface:/root/.cache/huggingface
   ```

---

### 问题5: 知识库为空

**症状**: 查询时提示"知识库为空"

**解决方案**:
```bash
# 1. 添加文档
cp your_documents/* data/raw_documents/

# 2. 构建知识库
docker-compose exec api python scripts/build_knowledge_base.py

# 3. 验证
docker-compose exec api python scripts/manage_kb.py stats
```

---

### 问题6: 内存不足

**症状**: 容器被 OOM killed

**解决方案**:

1. **增加 Docker 内存限制**:
   - Docker Desktop: Settings -> Resources -> Memory
   - 建议至少 4GB

2. **限制容器内存**:
   ```yaml
   # docker-compose.yml
   api:
     deploy:
       resources:
         limits:
           memory: 4G
   ```

---

### 问题7: 权限错误

**症状**: 无法写入文件或目录

**解决方案**:
```bash
# 1. 检查目录权限
ls -la data/

# 2. 修复权限
chmod -R 755 data/
chmod -R 755 logs/

# 3. 如果使用 Docker Desktop，确保目录在共享列表中
# Settings -> Resources -> File Sharing
```

---

### 问题8: 网络连接问题

**症状**: 容器之间无法通信

**解决方案**:
```bash
# 1. 检查网络
docker network ls
docker network inspect rag_rag-network

# 2. 重建网络
docker-compose down
docker network prune
docker-compose up -d

# 3. 测试容器间连接
docker-compose exec api ping redis
docker-compose exec web ping api
```

---

## 诊断工具

### 1. 连接诊断
```bash
bash diagnose-connection.sh
```

### 2. 查看日志
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs -f redis

# 最近 100 行
docker-compose logs --tail=100 api
```

### 3. 检查容器状态
```bash
# 列出容器
docker-compose ps

# 详细信息
docker inspect rag-api

# 资源使用
docker stats
```

### 4. 进入容器调试
```bash
# 进入 API 容器
docker-compose exec api bash

# 进入 Redis 容器
docker-compose exec redis sh

# 以 root 用户进入
docker-compose exec -u root api bash
```

---

## 完全重置

如果所有方法都失败，尝试完全重置：

```bash
# 1. 停止并删除所有容器
docker-compose down -v

# 2. 删除镜像
docker rmi rag-api rag-web

# 3. 清理 Docker 系统
docker system prune -a

# 4. 重新构建
bash docker-build.sh

# 5. 重新部署
bash docker-deploy.sh
```

---

## 获取帮助

如果问题仍然存在：

1. **收集信息**:
   ```bash
   # 系统信息
   docker version
   docker-compose version
   
   # 容器状态
   docker-compose ps
   
   # 日志
   docker-compose logs > docker-logs.txt
   ```

2. **检查文档**:
   - [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
   - [README.md](README.md)

3. **常见错误模式**:
   - 端口冲突 → 修改端口映射
   - 内存不足 → 增加 Docker 内存
   - 网络问题 → 重建网络
   - 权限问题 → 检查文件权限

---

## 预防措施

1. **定期备份**:
   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz data/
   ```

2. **监控资源**:
   ```bash
   docker stats
   ```

3. **保持更新**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

4. **使用健康检查**:
   已在 docker-compose.yml 中配置

---

**快速修复命令**:
```bash
# 最常用的修复方法
docker-compose down && docker-compose up -d
```

