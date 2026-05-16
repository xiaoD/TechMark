"""
TechMark 教育沙盘模拟 - 主程序

使用方法：
1. 首次运行：python main.py --init
   - 生成初始状态文件和决策模板
2. 每轮运行：python main.py --round N
   - 读取第N轮决策，计算结果
3. 完整运行：python main.py --play-all
   - 依次运行所有5轮（使用已填写的决策文件）
4. 查看排名：python main.py --rank
   - 查看当前最终排名

CSV决策文件格式 (data/decisions_round_N.csv):
company_name, product_id, price, teachers, marketing_budget

示例:
公司A, T1_1V1, 5000, 5, 50000
公司A, T1_Class, 2000, 10, 30000
"""

import argparse
import os
import sys

from models import GameState
from game_engine import GameEngine
from csv_handler import (
    load_initial_state, save_initial_state, load_decisions,
    save_decisions_template, save_round_results, save_final_ranking,
    print_round_summary
)
import config


def init_game():
    """初始化游戏"""
    print("🎮 TechMark 教育沙盘模拟 - 初始化")
    print("="*60)
    
    # 创建游戏状态
    state = GameState()
    
    # 输入玩家数量
    while True:
        try:
            num_players = int(input("请输入玩家数量 (2-6): "))
            if 2 <= num_players <= 6:
                break
            print("请输入2-6之间的数字")
        except ValueError:
            print("请输入有效数字")
    
    # 输入公司名称
    for i in range(num_players):
        name = input(f"请输入第{i+1}家公司名称: ").strip()
        if not name:
            name = f"公司{chr(65+i)}"  # 公司A, 公司B...
        state.add_company(name)
    
    # 保存初始状态
    save_initial_state(state)
    
    # 生成第1轮决策模板
    save_decisions_template(state, 1)
    
    print("\n✅ 初始化完成！")
    print("请编辑 data/decisions_round_1.csv 填写第1轮决策")
    print("\n决策说明:")
    print("  - price: 产品单价")
    print("  - teachers: 分配的教师人数")
    print("  - marketing_budget: 市场投入预算（用于获客）")
    
    return state


def run_round(round_num: int, state: GameState = None):
    """运行单轮"""
    print(f"\n🎲 正在运行第 {round_num} 轮...")
    
    # 加载状态
    if state is None:
        state = load_initial_state()
    
    # 加载决策
    decisions = load_decisions(round_num)
    
    if not decisions:
        print(f"❌ 错误: 未找到第{round_num}轮决策文件")
        print(f"请创建文件: data/decisions_round_{round_num}.csv")
        return None
    
    # 检查所有公司是否都有决策
    missing = []
    for company_name in state.companies:
        if company_name not in decisions:
            missing.append(company_name)
    
    if missing:
        print(f"⚠️ 警告: 以下公司缺少决策: {', '.join(missing)}")
    
    # 运行游戏引擎
    engine = GameEngine(state)
    results = engine.run_round(decisions)
    
    # 打印摘要
    print_round_summary(results)
    
    # 保存结果
    save_round_results(results)
    
    # 生成下轮决策模板（如果不是最后一轮）
    if round_num < config.TOTAL_ROUNDS:
        save_decisions_template(state, round_num + 1)
        print(f"\n📝 已生成第{round_num+1}轮决策模板: data/decisions_round_{round_num+1}.csv")
    
    return state


def play_all():
    """运行完整游戏"""
    print("🎮 TechMark 教育沙盘模拟 - 完整游戏")
    print("="*60)
    
    state = load_initial_state()
    
    for round_num in range(1, config.TOTAL_ROUNDS + 1):
        state = run_round(round_num, state)
        if state is None:
            print(f"❌ 游戏在第{round_num}轮中断")
            return
    
    # 最终排名
    engine = GameEngine(state)
    rankings = engine.get_final_ranking()
    
    print("\n" + "="*60)
    print("🏆 最终排名")
    print("="*60)
    
    for rank, (name, cash, debt, net_worth) in enumerate(rankings, 1):
        print(f"  第{rank}名: {name} | 净资产: {net_worth:,.0f} | 现金: {cash:,.0f} | 负债: {debt:,.0f}")
    
    save_final_ranking(rankings)
    print("\n✅ 游戏结束！")


def show_ranking():
    """显示当前排名"""
    state = load_initial_state()
    engine = GameEngine(state)
    rankings = engine.get_final_ranking()
    
    print("\n🏆 当前排名")
    print("="*60)
    for rank, (name, cash, debt, net_worth) in enumerate(rankings, 1):
        print(f"  第{rank}名: {name} | 净资产: {net_worth:,.0f}")


def show_rules():
    """显示游戏规则"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           TechMark 教育沙盘模拟 - 游戏规则                       ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  【基础设置】                                                    ║
║  • 玩家: 2-6家教育企业                                           ║
║  • 轮数: 5轮                                                     ║
║  • 初始资金: 1,000万                                             ║
║                                                                  ║
║  【市场】                                                        ║
║  • T1(一线): 上限10,000人, 学员预算10,000                        ║
║  • T2(二线): 上限30,000人, 学员预算4,000                         ║
║  • T3(三线): 上限100,000人, 学员预算2,000                        ║
║                                                                  ║
║  【产品矩阵】3市场 × 3产品 = 9个产品                             ║
║  • 1V1: 教师配比 1:20, 默认新增100人/轮                         ║
║  • Class: 教师配比 1:10, 默认新增300人/轮                        ║
║  • APP: 无需教师, 默认新增1000人/轮                              ║
║                                                                  ║
║  【决策变量】每轮为每个产品决定:                                   ║
║  1. price: 产品单价                                              ║
║  2. teachers: 分配教师人数                                       ║
║  3. marketing_budget: 市场投入预算（用于获客）                   ║
║                                                                  ║
║  【品牌效应】按该市场3个产品质量分总和排名                         ║
║  • 第1名: 获客成本降低20%                                        ║
║  • 第2名: 获客成本降低10%                                        ║
║                                                                  ║
║  【退费规则】                                                      ║
║  • 师资不足: 超出服务能力部分退费                                ║
║  • 预算超限: 单价超过学员预算则全部退费                          ║
║  • 退费惩罚: 该产品下轮质量分降低20%                             ║
║                                                                  ║
║  【财务】                                                        ║
║  • 收入 = 学员数 × 单价                                          ║
║  • 教师成本 = 教师数 × 1万/轮                                    ║
║  • 获客成本 = 学员数 × 单位获客成本 × (1-折扣)                   ║
║  • 负债利息 = 负债 × 8%/轮                                       ║
║                                                                  ║
║  【胜利条件】5轮后净资产最高者获胜                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description='TechMark 教育沙盘模拟')
    parser.add_argument('--init', action='store_true', help='初始化游戏')
    parser.add_argument('--round', type=int, help='运行指定轮次')
    parser.add_argument('--play-all', action='store_true', help='运行完整游戏')
    parser.add_argument('--rank', action='store_true', help='显示当前排名')
    parser.add_argument('--rules', action='store_true', help='显示游戏规则')
    parser.add_argument('--template', type=int, help='生成指定轮次的决策模板')
    
    args = parser.parse_args()
    
    # 确保data目录存在
    os.makedirs('data/results', exist_ok=True)
    
    if args.rules:
        show_rules()
    elif args.init:
        init_game()
    elif args.template:
        state = load_initial_state()
        save_decisions_template(state, args.template)
    elif args.round:
        run_round(args.round)
    elif args.play_all:
        play_all()
    elif args.rank:
        show_ranking()
    else:
        # 默认显示帮助
        parser.print_help()
        print("\n💡 提示: 首次运行请使用 --init 初始化游戏")


if __name__ == "__main__":
    main()
