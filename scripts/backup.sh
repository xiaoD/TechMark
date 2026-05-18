#!/bin/bash
# PalFish Business MindSet - 游戏数据备份脚本
# 用法: ./backup.sh [备份备注]

set -e

GAME_DIR="/opt/palfish-mindset"
BACKUP_DIR="/opt/palfish-mindset/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NOTE="${1:-auto}"
BACKUP_NAME="backup_${TIMESTAMP}_${NOTE}"

echo "🎮 PalFish MindSet Backup"
echo "=========================="
echo "Time: $(date)"
echo "Note: $NOTE"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 打包关键数据
cd "$GAME_DIR"
tar czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    data/game_config.json \
    data/submissions/ \
    data/results/ \
    data/saves/ \
    2>/dev/null || true

echo "✅ Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""
echo "📦 Backup size: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)"
echo ""

# 保留最近15个备份，删除旧的
echo "🧹 Cleaning old backups (keep last 15)..."
ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +16 | xargs -r rm -f
echo "✅ Done"
echo ""
echo "📂 Current backups:"
ls -lh "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | awk '{print $9, "(" $5 ")"}'
