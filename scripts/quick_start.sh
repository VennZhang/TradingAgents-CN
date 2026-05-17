#!/bin/bash
# ============================================
# TradingAgents-CN 快速启动脚本（Docker 容器内版本）
# ============================================
# 用法：bash scripts/quick_start.sh [--skip-redis]
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

SKIP_REDIS=false
for arg in "$@"; do
    case $arg in --skip-redis) SKIP_REDIS=true ;; esac
done

info()    { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[FAIL]${NC} $1"; }

# 检查端口是否有活跃进程监听
port_alive() {
    local port=$1
    local pids=$(netstat -tlnp 2>/dev/null | grep ":${port} " | awk '{print $NF}' | cut -d/ -f1 | sort -u)
    for pid in $pids; do
        if [ -n "$pid" ] && [ "$pid" != "-" ]; then
            local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
            if [ "$stat" != "Z" ]; then return 0; fi
        fi
    done
    return 1
}

# 检查 mongod 是否有活跃进程（非僵尸）
mongod_alive() {
    for pid in $(pgrep -x mongod 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && return 0
    done
    return 1
}

# 检查 redis 是否有活跃进程（非僵尸）
redis_alive() {
    for pid in $(pgrep -x redis-server 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && return 0
    done
    return 1
}

# 清理僵尸进程（启动前执行）
clean_zombies() {
    local zombie_count=$(ps -eo stat 2>/dev/null | grep -c "^Z" 2>/dev/null || echo "0")
    zombie_count=$(echo "$zombie_count" | tr -d '[:space:]')
    if [ "$zombie_count" -eq 0 ]; then return 0; fi

    info "发现 $zombie_count 个僵尸进程，尝试清理..."
    # 找到属于本项目的僵尸父进程
    for ppid in $(ps -eo pid,ppid,stat | awk '$3=="Z" {print $2}' | sort -u); do
        if [ "$ppid" = "1" ] || [ -z "$ppid" ]; then continue; fi
        local pcmd=$(ps -o comm= -p "$ppid" 2>/dev/null || echo "")
        local cwd=$(readlink /proc/$ppid/cwd 2>/dev/null || echo "")
        case "$pcmd" in
            bash|sh)
                if [[ "$cwd" == *"TradingAgents"* ]]; then
                    kill -9 "$ppid" 2>/dev/null || true
                fi
                ;;
        esac
    done
    sleep 1
}

# 清理残留端口占用
cleanup_ports() {
    info "清理残留进程..."
    for port in 8000 3000; do
        local pids=$(netstat -tlnp 2>/dev/null | grep ":${port} " | awk '{print $NF}' | cut -d/ -f1 | sort -u)
        for pid in $pids; do
            if [ -n "$pid" ] && [ "$pid" != "-" ]; then
                local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
                if [ "$stat" != "Z" ]; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
        done
    done
    sleep 1
    rm -f "$PROJECT_ROOT/.frontend.pid" "$PROJECT_ROOT/.backend.pid"
}

echo -e "${CYAN}"
cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║     TradingAgents-CN 快速启动脚本 (Docker 容器版)          ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

cd "$PROJECT_ROOT" || { error "项目目录不存在: $PROJECT_ROOT"; exit 1; }

# ---- 预清理 ----
clean_zombies
cleanup_ports

# ---- 步骤 1：MongoDB ----
if mongod_alive; then
    success "MongoDB 已在运行"
else
    info "启动 MongoDB..."
    mkdir -p /data/db /var/log/mongodb
    chown -R mongodb:mongodb /data/db /var/log/mongodb 2>/dev/null || true

    mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log \
           --fork --bind_ip 0.0.0.0 --auth 2>/dev/null \
    || mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log \
              --fork --bind_ip 0.0.0.0 2>/dev/null

    sleep 3
    if mongod_alive; then
        success "MongoDB 启动成功"
    else
        error "MongoDB 启动失败，查看: /var/log/mongodb/mongod.log"
        tail -20 /var/log/mongodb/mongod.log 2>/dev/null
        exit 1
    fi
fi

# ---- 步骤 2：Redis ----
if $SKIP_REDIS; then
    info "跳过 Redis（--skip-redis）"
else
    if redis_alive && redis-cli -a tradingagents123 ping 2>/dev/null | grep -q PONG; then
        success "Redis 已在运行"
    elif command -v redis-server &>/dev/null; then
        info "启动 Redis..."
        redis-server --daemonize yes --port 6379 \
                     --requirepass tradingagents123 --save "" --appendonly no
        sleep 2
        redis-cli -a tradingagents123 ping 2>/dev/null | grep -q PONG \
            && success "Redis 启动成功" \
            || warn "Redis 启动失败（不影响核心功能）"
    else
        warn "Redis 未安装，跳过"
    fi
fi

# ---- 步骤 3：后端 ----
if port_alive 8000; then
    success "后端已在运行 (http://localhost:8000)"
else
    info "启动后端 (uvicorn)..."
    cd "$PROJECT_ROOT"
    nohup python3 -m uvicorn app.main:app \
        --host 0.0.0.0 --port 8000 --reload \
        > /tmp/uvicorn.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/.backend.pid"

    info "等待后端启动（最多 30 秒）..."
    for i in $(seq 1 30); do
        port_alive 8000 && break
        sleep 1
    done
    if port_alive 8000; then
        success "后端启动成功 (PID: $BACKEND_PID, http://localhost:8000)"
    else
        error "后端启动超时，查看: /tmp/uvicorn.log"
        tail -20 /tmp/uvicorn.log 2>/dev/null
        exit 1
    fi
fi

# ---- 步骤 4：前端 ----
if port_alive 3000; then
    success "前端已在运行 (http://localhost:3000)"
else
    info "启动前端 (vite)..."
    cd "$PROJECT_ROOT/frontend"
    nohup npx vite --host 0.0.0.0 --port 3000 > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"

    info "等待前端启动（最多 20 秒）..."
    for i in $(seq 1 20); do
        port_alive 3000 && break
        sleep 1
    done
    if port_alive 3000; then
        success "前端启动成功 (PID: $FRONTEND_PID, http://localhost:3000)"
    else
        warn "前端启动超时，查看: /tmp/frontend.log"
        tail -10 /tmp/frontend.log 2>/dev/null
    fi
fi

# ---- 状态汇总 ----
echo ""
echo -e "${CYAN}========== 服务状态 ==========${NC}"
mongod_alive && success "MongoDB:  运行中 (27017)" || error "MongoDB:  未运行"
if ! $SKIP_REDIS; then
    redis_alive && success "Redis:    运行中 (6379)" || warn "Redis:    未运行"
fi
port_alive 8000 && success "后端:     运行中 (http://localhost:8000)" || error "后端:     未运行"
port_alive 3000 && success "前端:     运行中 (http://localhost:3000)" || warn "前端:     未运行"
ZOMBIE_COUNT=$(ps -eo stat 2>/dev/null | grep -c "^Z" 2>/dev/null || echo "0")
ZOMBIE_COUNT=$(echo "$ZOMBIE_COUNT" | tr -d '[:space:]')
echo -e "  僵尸进程: ${ZOMBIE_COUNT} 个"
echo ""
echo -e "${GREEN}访问:${NC}  前端 http://localhost:3000 | 后端 http://localhost:8000 | 文档 http://localhost:8000/docs"
echo -e "${GREEN}停止:${NC}  bash scripts/quick_stop.sh [--all]"
echo -e "${GREEN}重启:${NC}  bash scripts/restart.sh"
