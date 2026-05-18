"""
TechMark 教育沙盘模拟 - 数据模型
"""
from dataclasses import dataclass, field
from typing import Dict, List
import config


@dataclass
class Product:
    """单个产品（市场+产品类型）"""
    market: str          # T1/T2/T3
    product_type: str    # 1V1/Class/APP
    
    # 状态（每轮更新）
    quality_score: float = config.INITIAL_QUALITY  # 质量分
    students: int = 0      # 当前学员数

    
    # 决策（每轮输入）
    price: float = 0.0           # 单价
    teachers: int = 0            # 教师数
    sales: int = 0               # 销售人数（第3轮起）
    marketing_budget: float = 0.0  # 市场投入（获客预算）
    rd_budget: float = 0.0       # 研发费用
    
    # 记录
    revenue: float = 0.0         # 本轮收入
    teacher_cost: float = 0.0    # 本轮教师成本
    acquisition_cost: float = 0.0  # 本轮获客成本
    refund_count: int = 0        # 本轮退费人数
    valid_students: int = 0      # 本轮有效学员（扣除退费后）
    marketing_students: int = 0  # 通过营销投入获得的学员数
    
    @property
    def product_id(self) -> str:
        return f"{self.market}_{self.product_type}"
    
    @property
    def teacher_capacity(self) -> int:
        """当前教师可服务的最大学员数"""
        cap = config.TEACHER_CAPACITY[self.product_type]
        if cap == float('inf'):
            return float('inf')
        return self.teachers * cap
    
    def reset_round(self):
        """重置本轮计算数据（保留状态）"""
        self.revenue = 0.0
        self.teacher_cost = 0.0
        self.acquisition_cost = 0.0
        self.refund_count = 0
        self.valid_students = 0
        self.marketing_students = 0
        self.rd_budget = 0.0  # 每轮研发投入清空（决策时重新填）
    
    def to_dict(self) -> Dict:
        """序列化（保存跨轮累积状态）"""
        return {
            "market": self.market,
            "product_type": self.product_type,
            "quality_score": self.quality_score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Product":
        """反序列化"""
        p = cls(
            market=data["market"],
            product_type=data["product_type"],
            quality_score=data["quality_score"],
        )
        return p


@dataclass
class Company:
    """教育企业（玩家）"""
    name: str
    cash: float = config.INITIAL_CASH
    debt: float = 0.0
    
    # 9个产品
    products: Dict[str, Product] = field(default_factory=dict)
    
    # 本轮财务汇总
    total_revenue: float = 0.0
    total_teacher_cost: float = 0.0
    total_acquisition_cost: float = 0.0
    total_rd_cost: float = 0.0
    interest_payment: float = 0.0
    vat_tax: float = 0.0          # 增值税（营收的7%）
    income_tax: float = 0.0       # 所得税（利润的15%）
    total_tax: float = 0.0        # 总税收
    net_profit: float = 0.0
    
    def __post_init__(self):
        """初始化9个产品"""
        if not self.products:
            for market in config.MARKETS:
                for ptype in config.PRODUCT_TYPES:
                    pid = f"{market}_{ptype}"
                    self.products[pid] = Product(market=market, product_type=ptype)
    
    def get_market_quality_total(self, market: str) -> float:
        """获取某市场3个产品的质量分总和"""
        total = 0.0
        for ptype in config.PRODUCT_TYPES:
            pid = f"{market}_{ptype}"
            total += self.products[pid].quality_score
        return total
    
    def get_market_max_quality(self, market: str) -> float:
        """获取某市场内最高单个产品质量分（用于品牌排名）"""
        max_q = 0.0
        for ptype in config.PRODUCT_TYPES:
            pid = f"{market}_{ptype}"
            max_q = max(max_q, self.products[pid].quality_score)
        return max_q
    
    def reset_round(self):
        """重置本轮计算数据"""
        self.total_revenue = 0.0
        self.total_teacher_cost = 0.0
        self.total_acquisition_cost = 0.0
        self.total_rd_cost = 0.0
        self.interest_payment = 0.0
        self.vat_tax = 0.0
        self.income_tax = 0.0
        self.total_tax = 0.0
        self.net_profit = 0.0
        for p in self.products.values():
            p.reset_round()
    
    @property
    def total_students(self) -> int:
        """全公司学员总数"""
        return sum(p.students for p in self.products.values())
    
    @property
    def total_teachers(self) -> int:
        """全公司教师总数"""
        return sum(p.teachers for p in self.products.values())
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            "name": self.name,
            "cash": self.cash,
            "debt": self.debt,
            "products": {pid: p.to_dict() for pid, p in self.products.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Company":
        """反序列化"""
        company = cls(
            name=data["name"],
            cash=data["cash"],
            debt=data["debt"],
        )
        for pid, p_data in data["products"].items():
            company.products[pid] = Product.from_dict(p_data)
        return company


@dataclass
class GameState:
    """游戏全局状态"""
    round_number: int = 0
    companies: Dict[str, Company] = field(default_factory=dict)
    
    # 记录每轮市场总学员数（用于上限检查）
    market_students: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.market_students:
            for m in config.MARKETS:
                self.market_students[m] = 0
    
    def get_company(self, name: str) -> Company:
        return self.companies[name]
    
    def add_company(self, name: str):
        self.companies[name] = Company(name=name)
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            "round_number": self.round_number,
            "market_students": dict(self.market_students),
            "companies": {name: c.to_dict() for name, c in self.companies.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GameState":
        """反序列化"""
        state = cls(
            round_number=data["round_number"],
            market_students=data["market_students"],
        )
        for name, c_data in data["companies"].items():
            state.companies[name] = Company.from_dict(c_data)
        return state
