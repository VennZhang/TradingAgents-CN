#!/bin/bash
# ============================================
# TradingAgents-CN 快速停止脚本（Docker 容器内版本）
# ============================================
# 用法：bash scripts/quick_stop.sh [--all] [--force]
#   --all   : 同时停止 MongoDB 和 Redis（默认只停止前后端）
#   --force : 强制模式（默认）
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

STOP_ALL=false
for arg in "$@"; do
    case $arg in --all) STOP_ALL=true ;; esac
done

info()    { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[FAIL]${NC} $1"; }

# 检查端口是否有活跃（非僵尸）进程监听
# 返回 0=有活跃进程, 1=无
port_alive() {
    local port=$1
    local pids=$(netstat -tlnp 2>/dev/null | grep ":${port} " | awk '{print $NF}' | cut -d/ -f1 | sort -u)
    for pid in $pids; do
        if [ -n "$pid" ] && [ "$pid" != "-" ]; then
            local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
            if [ "$stat" != "Z" ]; then
                return 0
            fi
        fi
    done
    return 1
}

# 获取监听指定端口的活跃 PID
port_pids() {
    local port=$1
    local pids=""
    for pid in $(netstat -tlnp 2>/dev/null | grep ":${port} " | awk '{print $NF}' | cut -d/ -f1 | sort -u); do
        if [ -n "$pid" ] && [ "$pid" != "-" ]; then
            local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
            if [ "$stat" != "Z" ]; then
                pids="$pids $pid"
            fi
        fi
    done
    echo $pids
}

# 杀死进程及其所有子进程
kill_tree() {
    local pid=$1
    local sig=${2:-TERM}
    if ! ps -p "$pid" > /dev/null 2>&1; then return 0; fi
    local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
    [ "$stat" = "Z" ] && return 0  # 跳过僵尸
    local children=$(pgrep -P "$pid" 2>/dev/null)
    for child in $children; do kill_tree "$child" "$sig"; done
    kill "-$sig" "$pid" 2>/dev/null || true
}

# 通过端口停止服务
stop_by_port() {
    local name=$1
    local port=$2
    local pids=$(port_pids $port)
    if [ -z "$pids" ]; then
        info "$name 未运行 (port $port)"
        return 0
    fi
    info "停止 $name (PID:$pids, port $port)..."
    for pid in $pids; do
        kill_tree "$pid" TERM
    done
    sleep 2
    # 检查是否还活着
    local remaining=$(port_pids $port)
    if [ -n "$remaining" ]; then
        warn "$name 未响应 SIGTERM，发送 SIGKILL..."
        for pid in $remaining; do
            kill_tree "$pid" KILL
        done
        sleep 1
    fi
    remaining=$(port_pids $port)
    if [ -z "$remaining" ]; then
        success "$name 已停止"
    else
        error "$name 停止失败"
    fi
}

# 停止 mongod（通过进程名 + 过滤僵尸）
stop_mongod() {
    local alive_pids=""
    for pid in $(pgrep -x mongod 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && alive_pids="$alive_pids $pid"
    done
    if [ -z "$alive_pids" ]; then
        info "MongoDB 未运行"
        return 0
    fi
    info "停止 MongoDB (PID:$alive_pids)..."
    # 优雅关闭
    mongosh --quiet --eval "db.adminCommand({ shutdown: 1 })" &>/dev/null || true
    sleep 3
    # 检查
    alive_pids=""
    for pid in $(pgrep -x mongod 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && alive_pids="$alive_pids $pid"
    done
    if [ -n "$alive_pids" ]; then
        warn "优雅关闭失败，强制终止..."
        for pid in $alive_pids; do kill -9 "$pid" 2>/dev/null; done
        sleep 1
    fi
    # 最终检查
    alive_pids=""
    for pid in $(pgrep -x mongod 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && alive_pids="$alive_pids $pid"
    done
    [ -z "$alive_pids" ] && success "MongoDB 已停止" || error "MongoDB 停止失败"
}

# 停止 redis-server（通过进程名 + 过滤僵尸）
stop_redis() {
    local alive_pids=""
    for pid in $(pgrep -x redis-server 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && alive_pids="$alive_pids $pid"
    done
    if [ -z "$alive_pids" ]; then
        info "Redis 未运行"
        return 0
    fi
    info "停止 Redis (PID:$alive_pids)..."
    redis-cli -a tradingagents123 shutdown nosave 2>/dev/null || true
    sleep 1
    alive_pids=""
    for pid in $(pgrep -x redis-server 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && alive_pids="$alive_pids $pid"
    done
    if [ -n "$alive_pids" ]; then
        for pid in $alive_pids; do kill -9 "$pid" 2>/dev/null; done
        sleep 1
    fi
    alive_pids=""
    for pid in $(pgrep -x redis-server 2>/dev/null); do
        local stat=$(cat /proc/$pid/stat 2>/dev/null | awk '{print $3}')
        [ "$stat" != "Z" ] && alive_pids="$alive_pids $pid"
    done
    [ -z "$alive_pids" ] && success "Redis 已停止" || error "Redis 停止失败"
}

# 清理僵尸进程
clean_zombies() {
    info "清理僵尸进程..."
    local zombie_ppids=""
    for pid in $(ps -eo pid,ppid,stat | awk '$3=="Z" {print $2}' | sort -u); do
        if [ "$pid" != "1" ] && [ -n "$pid" ]; then
            local pcmd=$(ps -o comm= -p "$pid" 2>/dev/null || echo "")
            case "$pcmd" in
                bash|sh) 
                    # 检查是否是本项目的 shell（通过 /proc/pid/cwd 判断）
                    local cwd=$(readlink /proc/$pid/cwd 2>/dev/null || echo "")
                    if [[ "$cwd" == *"TradingAgents"* ]]; then
                        zombie_ppids="$zombie_ppids $pid"
                    fi
                    ;;
            esac
        fi
    done

    if [ -n "$zombie_ppids" ]; then
        info "终止 $zombie_ppids 的僵尸父进程..."
        for ppid in $zombie_ppids; do
            kill -9 "$ppid" 2>/dev/null || true
        done
        sleep 1
    fi

    local remaining=$(ps -eo stat | grep -c "^Z" 2>/dev/null || echo "0")
    if [ "$remaining" -gt 0 ]; then
        warn "仍有 $remaining 个僵尸进程（PID 1 未回收，不影响运行）"
    else
        success "僵尸进程已清理"
    fi
}

echo -e "${CYAN}"
cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║     TradingAgents-CN 快速停止脚本 (Docker 容器版)          ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# ---- 停止前端 (port 3000) ----
stop_by_port "前端" 3000
rm -f "$PROJECT_ROOT/.frontend.pid"

# ---- 停止后端 (port 8000) ----
stop_by_port "后端" 8000
rm -f "$PROJECT_ROOT/.backend.pid"

# ---- 停止 MongoDB ----
if $STOP_ALL; then
    stop_mongod
else
    info "MongoDB 保持运行（加 --all 可一并停止）"
fi

# ---- 停止 Redis ----
if $STOP_ALL; then
    stop_redis
else
    info "Redis 保持运行（加 --all 可一并停止）"
fi

# ---- 清理僵尸 ----
clean_zombies

# ---- 状态 ----
echo ""
echo -e "${CYAN}========== 服务状态 ==========${NC}"
port_alive 27017 && echo -e "  MongoDB:  ${YELLOW}运行中${NC}" || echo -e "  MongoDB:  ${GREEN}已停止${NC}"
port_alive 6379  && echo -e "  Redis:    ${YELLOW}运行中${NC}" || echo -e "  Redis:    ${GREEN}已停止${NC}"
port_alive 8000  && echo -e "  后端:     ${YELLOW}运行中${NC}" || echo -e "  后端:     ${GREEN}已停止${NC}"
port_alive 3000  && echo -e "  前端:     ${YELLOW}运行中${NC}" || echo -e "  前端:     ${GREEN}已停止${NC}"
ZOMBIE_COUNT=$(ps -eo stat 2>/dev/null | grep -c "^Z" 2>/dev/null || echo "0")
ZOMBIE_COUNT=$(echo "$ZOMBIE_COUNT" | tr -d '[:space:]')
echo -e "  僵尸进程: ${ZOMBIE_COUNT} 个"
echo ""
success "停止脚本执行完成"
