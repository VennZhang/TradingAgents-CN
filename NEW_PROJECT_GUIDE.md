# TradingAgents-CN 新项目启动指南

## 项目目录结构

- **源代码目录**: `/mnt/g/workspace/refrence/TradingAgents-CN-main`
- **原始代码目录**: `/mnt/g/workspace/TradingAgents-CN` (已恢复)

## 配置迁移说明

所有配置文件和脚本已经从原始目录迁移到新目录：

### 已迁移的文件
1. **`.env`** - 环境配置文件，包含数据库连接、API密钥等
2. **`scripts/quick_start.sh`** - 快速启动脚本（已修复路径问题）
3. **`scripts/quick_stop.sh`** - 快速停止脚本（已修复路径问题）

### 路径修复说明
- 所有硬编码的路径 `PROJECT_DIR="/mnt/g/workspace/TradingAgents-CN"` 已替换为动态检测
- 脚本现在会自动检测当前项目根目录，无需手动修改路径

## 启动步骤

### 1. 进入新项目目录
```bash
cd /mnt/g/workspace/refrence/TradingAgents-CN-main
```

### 2. 启动服务
```bash
# 开发模式（默认，禁用Redis以节省资源）
bash scripts/quick_start.sh

# 生产模式（启用Redis）
REDIS_ENABLED=true bash scripts/quick_start.sh
```

### 3. 访问服务
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 4. 停止服务
```bash
bash scripts/quick_stop.sh
```

## 验证配置

### 检查环境变量
```bash
grep -E "(MONGODB_|REDIS_)" .env
```

### 检查脚本路径
```bash
head -10 scripts/quick_start.sh
# 应该显示动态路径检测代码，而不是硬编码路径
```

## 故障排除

### 如果启动失败
1. **检查日志文件**:
   - 启动日志: `logs/quick_start.log`
   - 后端日志: `/tmp/uvicorn.log`
   - 前端日志: `/tmp/frontend.log`

2. **检查端口占用**:
   ```bash
   netstat -tuln | grep -E ":(8000|3000|27017|6379)"
   ```

3. **清理进程**:
   ```bash
   pkill -f "uvicorn\|vite\|yarn"
   ```

### 如果数据库连接失败
1. **确保MongoDB运行**:
   ```bash
   mongosh mongodb://admin:tradingagents123@localhost:27017/admin --eval "db.adminCommand('ping')"
   ```

2. **确保Redis运行**（如果启用）:
   ```bash
   redis-cli -a tradingagents123 ping
   ```

## 注意事项

- **数据库和缓存服务是独立的**，删除或移动项目目录不会影响数据
- **两个项目目录共享相同的数据库**，因为 `.env` 文件中的数据库配置相同
- **建议一次只运行一个项目的实例**，避免端口冲突
- **开发模式默认禁用Redis**，以减少资源占用和加快启动速度

## 备份建议

在进行重大修改前，建议备份重要数据：

```bash
# 备份数据库
mongodump --host localhost:27017 --username admin --password tradingagents123 --authenticationDatabase admin --out ./backups/mongodb_$(date +%Y%m%d_%H%M%S)
```

现在您可以在 `/mnt/g/workspace/refrence/TradingAgents-CN-main` 目录中安全地进行开发工作！