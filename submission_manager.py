"""
TechMark 教育沙盘模拟 - 分布式提交管理
每组通过独立链接提交决策，数据保存到共享存储
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, List, Tuple, Any
from pathlib import Path


def _to_native(obj: Any) -> Any:
    """递归转换 numpy 类型为原生 Python 类型（用于 JSON 序列化）"""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_to_native(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

SUBMISSION_DIR = Path("data/submissions")
RESULTS_DIR = Path("data/results")


def _ensure_dirs():
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _submission_path(round_num: int, company: str) -> Path:
    return SUBMISSION_DIR / f"round_{round_num}" / f"{company}.json"


def _results_path(round_num: int) -> Path:
    return RESULTS_DIR / f"round_{round_num}_results.json"


def save_submission(round_num: int, company: str, decisions: Dict):
    """保存某公司的本轮决策提交"""
    _ensure_dirs()
    filepath = _submission_path(round_num, company)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "company": company,
        "round": round_num,
        "submitted_at": datetime.now().isoformat(),
        "decisions": _to_native(decisions),
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_submission(round_num: int, company: str) -> Optional[Dict]:
    """读取某公司的本轮决策提交"""
    filepath = _submission_path(round_num, company)
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # 文件损坏，删除并返回 None
        filepath.unlink(missing_ok=True)
        return None


def list_submissions(round_num: int, companies: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
    """
    列出某轮所有公司的提交状态
    返回: [(公司名, 是否已提交, 提交时间或None), ...]
    """
    results = []
    for company in companies:
        sub = load_submission(round_num, company)
        if sub:
            results.append((company, True, sub.get("submitted_at")))
        else:
            results.append((company, False, None))
    return results


def get_all_submissions(round_num: int, companies: List[str]) -> Dict[str, Dict]:
    """获取某轮所有已提交的决策 {公司名: decisions}"""
    all_decisions = {}
    for company in companies:
        sub = load_submission(round_num, company)
        if sub:
            all_decisions[company] = sub["decisions"]
    return all_decisions


def clear_submission(round_num: int, company: str):
    """清除某公司的本轮提交"""
    filepath = _submission_path(round_num, company)
    if filepath.exists():
        filepath.unlink()


def clear_submissions(round_num: int):
    """清除某轮所有提交（游戏重置时使用）"""
    round_dir = SUBMISSION_DIR / f"round_{round_num}"
    if round_dir.exists():
        for f in round_dir.glob("*.json"):
            f.unlink()


def clear_all_submissions():
    """清除所有提交"""
    if SUBMISSION_DIR.exists():
        for f in SUBMISSION_DIR.rglob("*.json"):
            f.unlink()


def save_results_to_file(round_num: int, results: Dict):
    """保存本轮运行结果"""
    _ensure_dirs()
    filepath = _results_path(round_num)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(_to_native(results), f, ensure_ascii=False, indent=2)


def load_results_from_file(round_num: int) -> Optional[Dict]:
    """读取某轮运行结果"""
    filepath = _results_path(round_num)
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        filepath.unlink(missing_ok=True)
        return None


def get_latest_completed_round() -> int:
    """获取最新已完成（有结果文件）的轮次"""
    latest = 0
    if RESULTS_DIR.exists():
        for f in RESULTS_DIR.glob("round_*_results.json"):
            try:
                rn = int(f.stem.replace("round_", "").replace("_results", ""))
                latest = max(latest, rn)
            except ValueError:
                pass
    return latest


def load_all_results(max_round: int) -> Dict[int, Dict]:
    """加载所有已完成轮次的结果"""
    results = {}
    for rn in range(1, max_round + 1):
        res = load_results_from_file(rn)
        if res:
            results[rn] = res
    return results
