"""
TechMark 教育沙盘模拟 - 渐进式轮次规则

每轮解锁新的决策变量和游戏机制
"""

from typing import List, Dict


class RoundRule:
    """单轮规则配置"""
    
    def __init__(
        self,
        round_num: int,
        name: str,
        name_en: str,
        description: str,
        description_en: str,
        # 决策变量
        enable_rd: bool = False,           # 研发费用
        enable_teachers: bool = False,     # 教师配置
        enable_marketing: bool = False,    # 市场投入
        enable_pricing: bool = False,      # 产品定价
        # 游戏机制
        use_default_prices: bool = True,   # 使用默认定价
        enable_budget_constraint: bool = False,  # 学员预算约束
        enable_brand_discount: bool = False,     # 品牌折扣
        enable_capacity_refund: bool = False,    # 师资不足退费
        enable_market_cap: bool = False,         # 市场容量上限
        # 市场波动（模拟外部环境影响）
        market_shocks: Dict[str, Dict] = None,  # {市场: {budget_factor, capacity_factor, demand_factor}}
        # 其他
        rd_affects_quality: bool = False,  # 研发影响质量分
    ):
        self.round_num = round_num
        self.name = name
        self.name_en = name_en
        self.description = description
        self.description_en = description_en
    
        self.enable_rd = enable_rd
        self.enable_teachers = enable_teachers
        self.enable_marketing = enable_marketing
        self.enable_pricing = enable_pricing
        
        self.use_default_prices = use_default_prices
        self.enable_budget_constraint = enable_budget_constraint
        self.enable_brand_discount = enable_brand_discount
        self.enable_capacity_refund = enable_capacity_refund
        self.enable_market_cap = enable_market_cap
        
        # 市场波动：默认无波动（factor=1.0）
        self.market_shocks = market_shocks if market_shocks else {}
        for m in ["T1", "T2", "T3"]:
            if m not in self.market_shocks:
                self.market_shocks[m] = {"budget_factor": 1.0, "capacity_factor": 1.0, "demand_factor": 1.0}
        
        self.rd_affects_quality = rd_affects_quality
    
    def get_description(self, lang: str = "zh") -> str:
        return self.description_en if lang == "en" else self.description
    
    def get_name(self, lang: str = "zh") -> str:
        return self.name_en if lang == "en" else self.name
    
    @property
    def decision_variables(self) -> List[str]:
        """返回本轮可用的决策变量列表"""
        variables = []
        if self.enable_rd:
            variables.append("研发费用 (R&D)")
        if self.enable_teachers:
            variables.append("教师配置 (Teachers)")
        if self.enable_marketing:
            variables.append("市场投入 (Marketing)")
        if self.enable_pricing:
            variables.append("产品定价 (Price)")
        return variables
    
    @property
    def active_mechanics(self) -> List[str]:
        """返回本轮生效的游戏机制"""
        mechanics = ["基础财务结算"]
        if self.enable_capacity_refund:
            mechanics.append("师资约束与退费")
        if self.enable_budget_constraint:
            mechanics.append("学员预算约束")
        if self.enable_brand_discount:
            mechanics.append("品牌效应（竞争力加成 + 获客成本折扣）")
        if self.enable_market_cap:
            mechanics.append("市场容量上限")
        if self.rd_affects_quality:
            mechanics.append("研发投入提升质量分")
        return mechanics


# ==================== 5轮渐进式规则定义 ====================

ROUND_RULES = {
    1: RoundRule(
        round_num=1,
        name="基础运营",
        name_en="Basic Operations",
        description="""
        🎯 Round 1 Goal: Master the Basics
        
        You need to decide for each product:
        1. R&D spending → Improve quality score
        2. Teacher allocation → Ensure service capacity
        3. Marketing investment → Acquire more students
        
        Pricing uses system defaults this round. Student budget constraints are not yet active.
        Focus on understanding: the relationship between R&D and quality, teacher-student ratios, and marketing vs. student acquisition.
        """,
        description_en="""
        🎯 Round 1 Goal: Master the Basics
        
        You need to decide for each product:
        1. R&D spending → Improve quality score
        2. Teacher allocation → Ensure service capacity
        3. Marketing investment → Acquire more students
        
        Pricing uses system defaults this round. Student budget constraints are not yet active.
        Focus on understanding: the relationship between R&D and quality, teacher-student ratios, and marketing vs. student acquisition.
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=False,
        use_default_prices=True,
        enable_budget_constraint=False,
        enable_brand_discount=False,
        enable_capacity_refund=True,
        enable_market_cap=True,
        rd_affects_quality=True,
    ),
    
    2: RoundRule(
        round_num=2,
        name="定价策略",
        name_en="Pricing Strategy",
        description="""
        🎯 Round 2 Goal: Master Pricing Strategy
        
        New decision: Product Pricing
        
        Student budget constraints are now active!
        - T1 student budget cap: 10,000 CNY
        - T2 student budget cap: 4,000 CNY
        - T3 student budget cap: 2,000 CNY
        
        If your price exceeds the student budget, all students will request refunds!
        Find the balance between high price/high margin and low price/high volume.
        """,
        description_en="""
        🎯 Round 2 Goal: Master Pricing Strategy
        
        New decision: Product Pricing
        
        Student budget constraints are now active!
        - T1 student budget cap: 10,000 CNY
        - T2 student budget cap: 4,000 CNY
        - T3 student budget cap: 2,000 CNY
        
        If your price exceeds the student budget, all students will request refunds!
        Find the balance between high price/high margin and low price/high volume.
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=True,
        use_default_prices=False,
        enable_budget_constraint=True,
        enable_brand_discount=False,
        enable_capacity_refund=True,
        enable_market_cap=True,
        rd_affects_quality=True,
    ),
    
    3: RoundRule(
        round_num=3,
        name="品牌竞争",
        name_en="Brand Competition",
        description="""
        🎯 Round 3 Goal: Build Brand Advantage + Introduce Sales Team
        
        New Mechanism 1: Brand Effect
        Each market is ranked by【highest single product quality score】:
        - 1st place: All products in this market get +20% competitiveness, acquisition cost -20%
        - 2nd place: All products in this market get +10% competitiveness, acquisition cost -10%
        
        New Mechanism 2: Sales Offset
        New decision variable: **Sales Staff**
        - Sales staff can offset demand drop from high pricing
        - Each sales person offsets 3% of premium penalty
        - Example: Price 20% above default, 2 sales staff offset 6%, actual penalty is only 14%
        
        Strategy Tips:
        - Focus resources to build brand advantage in one market
        - High-price/high-quality strategy needs enough sales team
        - Balance development across multiple markets
        """,
        description_en="""
        🎯 Round 3 Goal: Build Brand Advantage + Introduce Sales Team
        
        New Mechanism 1: Brand Effect
        Each market is ranked by【highest single product quality score】:
        - 1st place: All products in this market get +20% competitiveness, acquisition cost -20%
        - 2nd place: All products in this market get +10% competitiveness, acquisition cost -10%
        
        New Mechanism 2: Sales Offset
        New decision variable: **Sales Staff**
        - Sales staff can offset demand drop from high pricing
        - Each sales person offsets 3% of premium penalty
        - Example: Price 20% above default, 2 sales staff offset 6%, actual penalty is only 14%
        
        Strategy Tips:
        - Focus resources to build brand advantage in one market
        - High-price/high-quality strategy needs enough sales team
        - Balance development across multiple markets
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=True,
        use_default_prices=False,
        enable_budget_constraint=True,
        enable_brand_discount=True,
        enable_capacity_refund=True,
        enable_market_cap=True,
        rd_affects_quality=True,
    ),
    
    4: RoundRule(
        round_num=4,
        name="市场饱和 + 市场波动",
        name_en="Market Saturation + Market Shocks",
        description="""
        🎯 Round 4 Goal: Handle Market Saturation + Market Shocks
        
        New Mechanism 1: Strict Market Capacity Cap
        When total market students reach the cap, new students are allocated by each company's marketing investment ratio!
        
        New Mechanism 2: ⚡ Market Shocks (External Environment Changes)
        
        📈 T1 (Tier-1) Market Expansion:
        - Student budget cap +20%
        - Market capacity +10%
        - New demand +15%
        
        📉 T2 (Tier-2) Market Contraction:
        - Student budget cap unchanged
        - Market capacity -20%
        - New demand -25%
        
        T3 (Tier-3) Market unchanged
        
        Strategy Tips:
        - T1 expansion = high-end opportunity window, increase investment
        - T2 contraction = be cautious with pricing and investment
        - Watch market capacity to avoid ineffective competition
        """,
        description_en="""
        🎯 Round 4 Goal: Handle Market Saturation + Market Shocks
        
        New Mechanism 1: Strict Market Capacity Cap
        When total market students reach the cap, new students are allocated by each company's marketing investment ratio!
        
        New Mechanism 2: ⚡ Market Shocks (External Environment Changes)
        
        📈 T1 (Tier-1) Market Expansion:
        - Student budget cap +20%
        - Market capacity +10%
        - New demand +15%
        
        📉 T2 (Tier-2) Market Contraction:
        - Student budget cap unchanged
        - Market capacity -20%
        - New demand -25%
        
        T3 (Tier-3) Market unchanged
        
        Strategy Tips:
        - T1 expansion = high-end opportunity window, increase investment
        - T2 contraction = be cautious with pricing and investment
        - Watch market capacity to avoid ineffective competition
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=True,
        use_default_prices=False,
        enable_budget_constraint=True,
        enable_brand_discount=True,
        enable_capacity_refund=True,
        enable_market_cap=True,
        rd_affects_quality=True,
        market_shocks={
            "T1": {"budget_factor": 1.2, "capacity_factor": 1.1, "demand_factor": 1.15},
            "T2": {"budget_factor": 1.0, "capacity_factor": 0.8, "demand_factor": 0.75},
            "T3": {"budget_factor": 1.0, "capacity_factor": 1.0, "demand_factor": 1.0},
        },
    ),
    
    5: RoundRule(
        round_num=5,
        name="终局之战",
        name_en="Final Battle",
        description="""
        🎯 Round 5 Goal: Final Showdown — Market Boom!
        
        All mechanisms active, market booming!
        
        📈 Market Changes:
        - All markets capacity +30%
        - All markets student budget +20%
        
        Keys to Victory:
        - Quality score accumulation (R&D investment from previous 4 rounds)
        - Brand effect (acquisition cost advantage)
        - Precise pricing strategy
        - Reasonable teacher allocation
        - Effective marketing investment
        
        Winner determined by net worth ranking after this round!
        """,
        description_en="""
        🎯 Round 5 Goal: Final Showdown — Market Boom!
        
        All mechanisms active, market booming!
        
        📈 Market Changes:
        - All markets capacity +30%
        - All markets student budget +20%
        
        Keys to Victory:
        - Quality score accumulation (R&D investment from previous 4 rounds)
        - Brand effect (acquisition cost advantage)
        - Precise pricing strategy
        - Reasonable teacher allocation
        - Effective marketing investment
        
        Winner determined by net worth ranking after this round!
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=True,
        use_default_prices=False,
        enable_budget_constraint=True,
        enable_brand_discount=True,
        enable_capacity_refund=True,
        enable_market_cap=True,
        rd_affects_quality=True,
        market_shocks={
            "T1": {"budget_factor": 1.2, "capacity_factor": 1.3, "demand_factor": 1.0},
            "T2": {"budget_factor": 1.2, "capacity_factor": 1.3, "demand_factor": 1.0},
            "T3": {"budget_factor": 1.2, "capacity_factor": 1.3, "demand_factor": 1.0},
        },
    ),
}


def get_round_rule(round_num: int) -> RoundRule:
    """获取指定轮次的规则"""
    return ROUND_RULES.get(round_num, ROUND_RULES[5])


def get_all_rules_summary() -> str:
    """获取所有轮次的规则摘要"""
    summary = []
    for round_num in range(1, 6):
        rule = ROUND_RULES[round_num]
        summary.append(f"""
{'='*60}
第 {rule.round_num} 轮：{rule.name}
{'='*60}
{rule.description}

📋 决策变量：{', '.join(rule.decision_variables)}
⚙️ 生效机制：{', '.join(rule.active_mechanics)}
""")
    return '\n'.join(summary)
