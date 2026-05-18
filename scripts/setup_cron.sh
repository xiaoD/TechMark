#!/bin/bash
# 设置每5分钟自动备份
# 用法: ./setup_cron.sh

SCRIPT_PATH="/opt/palfish-mindset/scripts/backup.sh"
CRON_JOB="*/5 * * * * cd /opt/palfish-mindset && ./scripts/backup.sh auto >/dev/null 2>&1"

echo "🕐 Setting up auto-backup every 5 minutes..."

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "backup.sh"; then
    echo "⚠️  Auto-backup already configured"
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Auto-backup configured: every 5 minutes"
fi

echo ""
echo "📋 Current crontab:"
crontab -l | grep backup || echo "   (none)"
echo ""
echo "To disable: crontab -e and remove the backup line"
