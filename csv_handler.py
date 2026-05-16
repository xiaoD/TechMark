"""
TechMark 教育沙盘模拟 - CSV文件处理
"""
import csv
import os
from typing import Dict, List
from models import GameState, Company, Product
import config


def load_initial_state(filepath: str = "data/initial_state.csv") -> GameState:
    """从CSV加载初始状态（公司列表）"""
    state = GameState()
    
    if not os.path.exists(filepath):
        # 如果没有初始状态文件，创建默认的2家公司
        state.add_company("公司A")
        state.add_company("公司B")
        return state
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['company_name'].strip()
            state.add_company(name)
    
    return state


def save_initial_state(state: GameState, filepath: str = "data/initial_state.csv"):
    """保存初始状态"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['company_name'])
        for company in state.companies.values():
            writer.writerow([company.name])


def load_decisions(round_num: int, filepath: str = None) -> Dict:
    """
    从CSV加载某轮的决策
    
    CSV格式：
    company_name, product_id, price, teachers, marketing_budget
    
    返回: {公司名称: {产品ID: {"price": x, "teachers": x, "marketing": x}}}
    """
    if filepath is None:
        filepath = f"data/decisions_round_{round_num}.csv"
    
    decisions = {}
    
    if not os.path.exists(filepath):
        print(f"警告: 决策文件不存在: {filepath}")
        return decisions
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row['company_name'].strip()
            product_id = row['product_id'].strip()
            
            if company not in decisions:
                decisions[company] = {}
            
            decisions[company][product_id] = {
                "price": float(row['price']),
                "teachers": int(row['teachers']),
                "marketing": float(row['marketing_budget']),
            }
    
    return decisions


def save_decisions_template(state: GameState, round_num: int, filepath: str = None, force: bool = False):
    """
    生成决策模板CSV，方便玩家填写
    
    CSV格式：
    company_name, product_id, price, teachers, marketing_budget
    """
    if filepath is None:
        filepath = f"data/decisions_round_{round_num}.csv"
    
    # 如果文件已存在且不强制覆盖，跳过
    if os.path.exists(filepath) and not force:
        print(f"决策文件已存在，跳过生成: {filepath}")
        return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['company_name', 'product_id', 'price', 'teachers', 'marketing_budget'])
        
        for company in state.companies.values():
            for pid in config.ALL_PRODUCTS:
                product = company.products[pid]
                writer.writerow([
                    company.name,
                    pid,
                    0,  # price
                    0,  # teachers
                    0,  # marketing_budget
                ])
    
    print(f"已生成决策模板: {filepath}")


def save_round_results(results: Dict, filepath: str = None):
    """
    保存某轮结果到CSV
    
    生成两个文件：
    1. 公司汇总结果
    2. 产品明细结果
    """
    round_num = results['round']
    
    if filepath is None:
        base_path = f"data/results"
    else:
        base_path = os.path.dirname(filepath)
    
    os.makedirs(base_path, exist_ok=True)
    
    # 1. 保存公司汇总
    company_file = f"{base_path}/round_{round_num}_companies.csv"
    with open(company_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'company_name', 'cash', 'debt', 'net_profit', 
            'total_revenue', 'total_teacher_cost', 'total_acquisition_cost',
            'interest_payment', 'total_students', 'total_teachers'
        ])
        
        for company_name, data in results['companies'].items():
            writer.writerow([
                company_name,
                data['cash'],
                data['debt'],
                data['net_profit'],
                data['total_revenue'],
                data['total_teacher_cost'],
                data['total_acquisition_cost'],
                data['interest_payment'],
                sum(p['students'] for p in data['products'].values()),
                sum(p['teachers'] for p in data['products'].values()),
            ])
    
    # 2. 保存产品明细
    product_file = f"{base_path}/round_{round_num}_products.csv"
    with open(product_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'company_name', 'product_id', 'market', 'product_type',
            'quality_score', 'price', 'teachers', 'marketing_budget',
            'students', 'valid_students', 'refund_count',
            'revenue', 'teacher_cost', 'acquisition_cost'
        ])
        
        for company_name, data in results['companies'].items():
            for product_id, p in data['products'].items():
                market, ptype = product_id.split('_')
                writer.writerow([
                    company_name,
                    product_id,
                    market,
                    ptype,
                    p['quality_score'],
                    p['price'],
                    p['teachers'],
                    p['marketing_budget'],
                    p['students'],
                    p['valid_students'],
                    p['refund_count'],
                    p['revenue'],
                    p['teacher_cost'],
                    p['acquisition_cost'],
                ])
    
    # 3. 保存市场汇总
    market_file = f"{base_path}/round_{round_num}_markets.csv"
    with open(market_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['market', 'total_students', 'capacity', 'utilization_rate'])
        
        for market, total in results['market_totals'].items():
            capacity = config.MARKET_CAPACITY[market]
            utilization = total / capacity if capacity > 0 else 0
            writer.writerow([
                market,
                total,
                capacity,
                f"{utilization:.2%}"
            ])
    
    print(f"第{round_num}轮结果已保存到 {base_path}/")


def save_final_ranking(rankings: List, filepath: str = "data/results/final_ranking.csv"):
    """保存最终排名"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'company_name', 'cash', 'debt', 'net_worth'])
        
        for rank, (name, cash, debt, net_worth) in enumerate(rankings, 1):
            writer.writerow([rank, name, cash, debt, net_worth])
    
    print(f"最终排名已保存: {filepath}")


def print_round_summary(results: Dict):
    """打印本轮摘要到控制台"""
    print("\n" + "="*80)
    print(f"第 {results['round']} 轮结果摘要")
    print("="*80)
    
    # 市场情况
    print("\n📊 市场学员情况:")
    for market, total in results['market_totals'].items():
        capacity = config.MARKET_CAPACITY[market]
        pct = total / capacity * 100
        print(f"  {market}: {total:,} / {capacity:,} ({pct:.1f}%)")
    
    # 各公司情况
    print("\n💰 公司财务情况:")
    for company_name, data in results['companies'].items():
        print(f"\n  {company_name}:")
        print(f"    现金: {data['cash']:,.0f} | 负债: {data['debt']:,.0f} | 净利润: {data['net_profit']:,.0f}")
        print(f"    收入: {data['total_revenue']:,.0f} | 教师成本: {data['total_teacher_cost']:,.0f} | 获客成本: {data['total_acquisition_cost']:,.0f} | 利息: {data['interest_payment']:,.0f}")
        
        # 产品明细
        print("    产品明细:")
        for pid, p in data['products'].items():
            if p['students'] > 0 or p['marketing_budget'] > 0:
                print(f"      {pid}: 学员{p['students']}人 | 定价{p['price']:,.0f} | 质量分{p['quality_score']:.1f} | 收入{p['revenue']:,.0f}")
