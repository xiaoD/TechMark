# 🛡️ 数据保障手册

## 正式运行前必做

### 1. 开启自动备份（服务器上执行）
```bash
cd /opt/palfish-mindset/scripts
chmod +x *.sh
./setup_cron.sh
```
> 每5分钟自动备份一次，保留最近15个备份

### 2. 每轮运行前手动备份（推荐）
```bash
cd /opt/palfish-mindset/scripts
./backup.sh "before_round_X"
```

---

## 崩溃后恢复流程

### 第一步：检查状态
```bash
cd /opt/palfish-mindset/scripts
./check_status.sh
```
输出会告诉你：
- 当前进行到哪一轮
- 各公司提交是否完整
- 哪些数据完好 / 哪些丢失

### 第二步：根据情况处理

**情况A：只是服务崩溃，数据文件都在**
```bash
sudo systemctl restart palfish-mindset
```

**情况B：数据文件损坏/丢失**
```bash
# 查看可用备份
ls -lt /opt/palfish-mindset/backups/

# 恢复到某个备份
./restore.sh /opt/palfish-mindset/backups/backup_20260517_143000_before_round_3.tar.gz
```

### 第三步：验证恢复
```bash
./check_status.sh
```
确认当前轮次和提交状态正确后，继续游戏。

---

## 数据文件说明

| 文件/目录 | 内容 | 重要性 |
|---|---|---|
| `data/game_config.json` | 公司列表、当前轮次 | ⭐⭐⭐ 最重要 |
| `data/submissions/round_X/` | 每轮各公司的决策提交 | ⭐⭐⭐ |
| `data/results/` | 每轮运行结果 | ⭐⭐ |
| `data/saves/snapshots/` | 每轮运行前的完整快照 | ⭐⭐ 可重建 |
