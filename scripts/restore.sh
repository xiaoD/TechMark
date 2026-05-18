#!/bin/bash
# PalFish Business MindSet - 数据恢复脚本
# 用法: ./restore.sh <备份文件路径>

set -e

if [ -z "$1" ]; then
    echo "❌ Usage: ./restore.sh <backup_file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -1t /opt/palfish-mindset/backups/backup_*.tar.gz 2>/dev/null | head -10
    exit 1
fi

BACKUP_FILE="$1"
GAME_DIR="/opt/palfish-mindset"

echo "🔄 Restoring from: $BACKUP_FILE"
echo "⚠️  This will OVERWRITE current game data!"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# 先备份当前状态（以防万一）
echo "📦 Creating safety backup of current state..."
mkdir -p "$GAME_DIR/backups"
SAFE_BACKUP="$GAME_DIR/backups/safety_$(date +%Y%m%d_%H%M%S).tar.gz"
cd "$GAME_DIR"
tar czf "$SAFE_BACKUP" data/ 2>/dev/null || true
echo "   Safety backup: $SAFE_BACKUP"

# 恢复数据
echo "🔄 Restoring data..."
cd "$GAME_DIR"
tar xzf "$BACKUP_FILE"

# 重启服务
echo "🔄 Restarting service..."
sudo systemctl restart palfish-mindset
sleep 2
sudo systemctl status palfish-mindset --no-pager | head -5

echo ""
echo "✅ Restore complete!"
echo "👉 Check game status: ./check_status.sh"
