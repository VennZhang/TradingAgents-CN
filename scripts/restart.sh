#!/bin/bash
# ============================================
# TradingAgents-CN 一键重启脚本
# ============================================
# 用法：bash scripts/restart.sh [--all] [--skip-redis]
#   --all        : 重启时也重启 MongoDB 和 Redis
#   --skip-redis : 不启动 Redis
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'

STOP_ARGS=""
START_ARGS=""
for arg in "$@"; do
    case $arg in
        --all)        STOP_ARGS="$STOP_ARGS --all" ;;
        --skip-redis) START_ARGS="$START_ARGS --skip-redis" ;;
    esac
done

echo -e "${CYAN}"
cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║          TradingAgents-CN 一键重启脚本                     ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# ---- 停止 ----
echo -e "${YELLOW}========== 停止服务 ==========${NC}"
bash "$SCRIPT_DIR/quick_stop.sh" $STOP_ARGS

# ---- 启动 ----
echo ""
echo -e "${CYAN}========== 启动服务 ==========${NC}"
bash "$SCRIPT_DIR/quick_start.sh" $START_ARGS
