#!/bin/bash
# PalFish Business MindSet - 游戏状态检查脚本
# 用法: ./check_status.sh

GAME_DIR="/opt/palfish-mindset"
DATA_DIR="$GAME_DIR/data"

echo "🎮 PalFish MindSet - Game Status Check"
echo "======================================="
echo "Time: $(date)"
echo ""

# 检查游戏配置
echo "📋 Game Config:"
if [ -f "$DATA_DIR/game_config.json" ]; then
    cat "$DATA_DIR/game_config.json"
else
    echo "❌ MISSING - game_config.json not found!"
fi
echo ""

# 检查当前轮次
CURRENT_ROUND=$(python3 -c "import json; d=json.load(open('$DATA_DIR/game_config.json')); print(d.get('current_round', 0))" 2>/dev/null || echo "0")
echo "🎯 Current Round: $CURRENT_ROUND"
echo ""

# 检查提交状态
echo "📤 Submissions Status:"
for r in 1 2 3 4 5; do
    SUB_DIR="$DATA_DIR/submissions/round_$r"
    if [ -d "$SUB_DIR" ]; then
        COUNT=$(ls "$SUB_DIR"/*.json 2>/dev/null | wc -l)
        echo "  Round $r: $COUNT submissions"
    else
        echo "  Round $r: 0 submissions (dir not found)"
    fi
done
echo ""

# 检查结果文件
echo "📊 Results Status:"
for r in 1 2 3 4 5; do
    RES_FILE="$DATA_DIR/results/round_${r}_companies.csv"
    if [ -f "$RES_FILE" ]; then
        echo "  Round $r: ✅ Results saved"
    else
        echo "  Round $r: ❌ No results yet"
    fi
done
echo ""

# 检查快照
echo "💾 Snapshots:"
for r in 1 2 3 4 5; do
    SNAP="$DATA_DIR/saves/snapshots/round_${r}_pre.json"
    if [ -f "$SNAP" ]; then
        echo "  Round $r: ✅ Snapshot exists"
    else
        echo "  Round $r: ❌ No snapshot"
    fi
done
echo ""

# 给出恢复建议
echo "🚑 Recovery Recommendation:"
if [ -f "$DATA_DIR/game_config.json" ]; then
    echo "  ✅ Game config intact - can resume from Round $((CURRENT_ROUND + 1))"
    
    # 检查当前轮次提交是否完整
    COMPANIES=$(python3 -c "import json; d=json.load(open('$DATA_DIR/game_config.json')); print(len(d.get('companies', [])))" 2>/dev/null || echo "0")
    NEXT_ROUND=$((CURRENT_ROUND + 1))
    SUB_COUNT=$(ls "$DATA_DIR/submissions/round_$NEXT_ROUND"/*.json 2>/dev/null | wc -l)
    
    if [ "$SUB_COUNT" -eq "$COMPANIES" ] && [ "$COMPANIES" -gt 0 ]; then
        echo "  ✅ All $COMPANIES companies submitted for Round $NEXT_ROUND"
        echo "  👉 Ready to RUN Round $NEXT_ROUND"
    elif [ "$SUB_COUNT" -gt 0 ]; then
        echo "  ⚠️  Round $NEXT_ROUND: $SUB_COUNT / $COMPANIES companies submitted"
        echo "  👉 Wait for remaining submissions before running"
    else
        echo "  ⏳ Round $NEXT_ROUND: No submissions yet"
    fi
else
    echo "  ❌ CRITICAL: game_config.json missing!"
    echo "  👉 Restore from backup immediately"
fi
echo ""
