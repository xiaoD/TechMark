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
        description: str,
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
        self.description = description
        
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
        description="""
        🎯 第1轮目标：熟悉基础运营
        
        你需要为每个产品决定：
        1. 研发费用 → 提升产品质量分
        2. 教师配置 → 确保服务能力
        3. 市场投入 → 获取更多学员
        
        本轮定价使用系统默认值，学员预算约束暂不生效。
        重点理解：研发投入与质量分的关系、师资配比、市场投入与获客的关系。
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=False,
        use_default_prices=True,
        enable_budget_constraint=False,
        enable_brand_discount=False,
        enable_capacity_refund=True,
        enable_market_cap=False,
        rd_affects_quality=True,
    ),
    
    2: RoundRule(
        round_num=2,
        name="定价策略",
        description="""
        🎯 第2轮目标：掌握定价策略
        
        新增决策：产品定价（Price）
        
        学员预算约束生效！
        - T1学员预算上限：10,000元
        - T2学员预算上限：4,000元  
        - T3学员预算上限：2,000元
        
        如果你的定价超过学员预算，将导致全部退费！
        需要在高价高收益与低价高销量之间找到平衡。
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=True,
        use_default_prices=False,
        enable_budget_constraint=True,
        enable_brand_discount=False,
        enable_capacity_refund=True,
        enable_market_cap=False,
        rd_affects_quality=True,
    ),
    
    3: RoundRule(
        round_num=3,
        name="品牌竞争",
        description="""
        🎯 第3轮目标：建立品牌优势 + 引入销售团队
        
        新增机制1：品牌效应
        每个市场按【最高单个产品质量分】排名：
        - 第1名：该公司在该市场所有产品竞争力 +20%，同时获客成本降低 20%
        - 第2名：该公司在该市场所有产品竞争力 +10%，同时获客成本降低 10%
        
        新增机制2：销售对冲
        新增决策变量：**销售人数**
        - 销售人员可以对冲高价带来的需求下降
        - 每个销售可抵消 3% 的溢价惩罚
        - 例如：定价高于默认20%，2个销售可抵消6%，实际只惩罚14%
        
        策略提示：
        - 集中资源打造某个市场的品牌优势
        - 高价高质路线需要配足够的销售团队
        - 注意平衡多个市场的发展
        """,
        enable_rd=True,
        enable_teachers=True,
        enable_marketing=True,
        enable_pricing=True,
        use_default_prices=False,
        enable_budget_constraint=True,
        enable_brand_discount=True,
        enable_capacity_refund=True,
        enable_market_cap=False,
        rd_affects_quality=True,
    ),
    
    4: RoundRule(
        round_num=4,
        name="市场饱和 + 市场波动",
        description="""
        🎯 第4轮目标：应对市场饱和 + 市场波动
        
        新增机制1：市场容量严格上限
        当市场学员总数达到上限后，新增学员将按各公司"市场投入"比例分配！
        
        新增机制2：⚡ 市场波动（外部环境变化）
        
        📈 T1（一线）市场扩大：
        - 学员预算上限 +20%
        - 市场容量 +10%
        - 新增需求 +15%
        
        📉 T2（二线）市场收缩：
        - 学员预算上限 -30%
        - 市场容量 -20%
        - 新增需求 -25%
        
        T3（三线）市场不变
        
        策略提示：
        - T1扩大 = 高端机会窗口，可加大投入
        - T2收缩 = 需谨慎控制定价和投入
        - 关注市场容量，避免无效竞争
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
            "T2": {"budget_factor": 0.7, "capacity_factor": 0.8, "demand_factor": 0.75},
            "T3": {"budget_factor": 1.0, "capacity_factor": 1.0, "demand_factor": 1.0},
        },
    ),
    
    5: RoundRule(
        round_num=5,
        name="终局之战",
        description="""
        🎯 第5轮目标：最终决胜
        
        所有机制全开，市场完全饱和！
        
        决胜关键：
        - 质量分积累（前4轮的研发投入）
        - 品牌效应（获客成本优势）
        - 精准的定价策略
        - 合理的师资配置
        - 有效的市场投入
        
        本轮结束后按净资产排名决定胜负！
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
