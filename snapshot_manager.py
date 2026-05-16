"""
TechMark 教育沙盘模拟 - 轮次快照管理
支持：运行前自动快照、重新运行本轮、从快照恢复
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from models import GameState

SNAPSHOT_DIR = "data/saves/snapshots"


def _snapshot_path(round_num: int) -> str:
    return f"{SNAPSHOT_DIR}/round_{round_num}_pre.json"


def ensure_dir():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def save_pre_round_snapshot(round_num: int, game_state: GameState,
                            input_decisions: Dict, round_results: Dict) -> str:
    """
    保存本轮开始前的快照
    
    包含：
    - round_num: 本轮编号
    - game_state: 本轮开始前的完整状态（上一轮结束后的状态）
    - input_decisions: 用户本轮输入的原始决策（用于重跑时预填充）
    - round_results: 本轮之前的历史结果（用于恢复历史图表）
    """
    ensure_dir()
    
    save_data = {
        "version": 1,
        "saved_at": datetime.now().isoformat(),
        "round_num": round_num,
        "game_state": game_state.to_dict(),
        "input_decisions": input_decisions,
        "round_results": round_results,
    }
    
    filepath = _snapshot_path(round_num)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    return filepath


def load_pre_round_snapshot(round_num: int) -> Optional[Tuple]:
    """
    加载本轮开始前的快照
    
    返回: (game_state, input_decisions, round_results_before) 或 None
    """
    filepath = _snapshot_path(round_num)
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    game_state = GameState.from_dict(data["game_state"])
    return game_state, data["input_decisions"], data["round_results"]


def has_snapshot(round_num: int) -> bool:
    """检查是否存在某轮的快照"""
    return os.path.exists(_snapshot_path(round_num))


def delete_snapshot(round_num: int):
    """删除某轮快照"""
    filepath = _snapshot_path(round_num)
    if os.path.exists(filepath):
        os.remove(filepath)


def delete_all_snapshots():
    """删除所有快照（游戏结束后清理）"""
    if os.path.exists(SNAPSHOT_DIR):
        for f in os.listdir(SNAPSHOT_DIR):
            if f.endswith(".json"):
                os.remove(f"{SNAPSHOT_DIR}/{f}")
