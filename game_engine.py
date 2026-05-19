"""
TechMark 教育沙盘模拟 - 核心游戏引擎（支持渐进式规则）
"""
import math
from typing import Dict, List, Tuple
from models import GameState, Company, Product
from round_rules import get_round_rule, RoundRule
import config


class GameEngine:
    """游戏引擎：处理每轮的核心逻辑"""
    
    def __init__(self, state: GameState):
        self.state = state
        self.current_rule: RoundRule = None
    
    def run_round(self, decisions: Dict[str, Dict], round_num: int = None) -> Dict:
        """
        运行一轮游戏
        
        decisions: {公司名称: {产品ID: {"price": 单价, "teachers": 教师数, 
                                         "marketing": 市场投入, "rd": 研发费用}}}
        """
        if round_num is None:
            self.state.round_number += 1
        else:
            self.state.round_number = round_num
        
        round_num = self.state.round_number
        self.current_rule = get_round_rule(round_num)
        
        print(f"\n🎲 正在运行第 {round_num} 轮：{self.current_rule.name}")
        
        # 1. 重置各公司本轮数据 + 市场累计人数
        for company in self.state.companies.values():
            company.reset_round()
        for m in config.MARKETS:
            self.state.market_students[m] = 0
        
        # 2. 应用玩家决策
        self._apply_decisions(decisions)
        
        # 3. 处理研发费用 → 质量分提升（在分配学员前应用）
        if self.current_rule.rd_affects_quality:
            self._apply_rd_effects()
        
        # 4. 计算品牌效应（获客成本折扣 + 竞争力加成）
        discounts, boosts, brand_rankings = self._calculate_brand_effects()
        self._brand_rankings = brand_rankings  # 保存供结果输出
        
        # 5. 分配学员（核心逻辑）
        self._allocate_students(discounts, boosts)
        
        # 6. 检查师资约束和退费
        if self.current_rule.enable_capacity_refund:
            self._check_capacity_and_refund()
        
        # 7. 检查预算约束和退费
        if self.current_rule.enable_budget_constraint:
            self._check_budget_and_refund()
        
        # 8. 计算财务
        self._calculate_finance(discounts)
        
        # 9. 更新市场学员总数统计
        self._update_market_totals()
        
        # 10. 更新质量分（退费惩罚）
        if self.current_rule.enable_capacity_refund or self.current_rule.enable_budget_constraint:
            self._update_quality_scores()
        
        return self._get_round_results()
    
    def _apply_decisions(self, decisions: Dict):
        """应用玩家决策"""
        for company_name, company_decisions in decisions.items():
            if company_name not in self.state.companies:
                continue
            company = self.state.companies[company_name]
            
            for product_id, decision in company_decisions.items():
                if product_id not in company.products:
                    continue
                product = company.products[product_id]
                
                # 根据本轮规则应用决策
                if self.current_rule.enable_pricing:
                    product.price = float(decision.get("price", 0))
                elif self.current_rule.use_default_prices:
                    market, ptype = product_id.split('_')
                    product.price = config.DEFAULT_PRICES[market][ptype]
                
                if self.current_rule.enable_teachers:
                    market, ptype = product_id.split('_')
                    # APP 产品不需要教师
                    if ptype == "APP":
                        product.teachers = 0
                    else:
                        product.teachers = int(decision.get("teachers", 0))
                
                if self.current_rule.round_num >= 3:
                    product.sales = int(decision.get("sales", 0))
                
                if self.current_rule.enable_marketing:
                    product.marketing_budget = float(decision.get("marketing", 0))
                
                if self.current_rule.enable_rd:
                    product.rd_budget = float(decision.get("rd", 0))
    
    def _apply_rd_effects(self):
        """应用研发费用对质量分的提升"""
        for company in self.state.companies.values():
            for product in company.products.values():
                if product.rd_budget > 0:
                    # 每1万元研发提升1分质量分
                    quality_increase = product.rd_budget * config.RD_TO_QUALITY_RATIO
                    product.quality_score = min(
                        config.MAX_QUALITY,
                        product.quality_score + quality_increase
                    )
    
    def _calculate_brand_effects(self) -> Tuple[Dict, Dict, Dict]:
        """
        计算品牌效应
        排名规则：由市场内【最高单个产品质量分】决定
        
        返回: (discounts, boosts, rankings)
            discounts: {市场: {公司名称: 获客成本折扣率}}
            boosts:    {市场: {公司名称: 竞争力加成率}}
            rankings:  {市场: [(公司名, 产品ID, 质量分), ...]}
        """
        discounts = {m: {} for m in config.MARKETS}
        boosts = {m: {} for m in config.MARKETS}
        rankings = {m: [] for m in config.MARKETS}
        
        if not self.current_rule.enable_brand_discount:
            # 品牌折扣未启用
            for market in config.MARKETS:
                for company in self.state.companies.values():
                    discounts[market][company.name] = 0.0
                    boosts[market][company.name] = 0.0
            return discounts, boosts, rankings
        
        for market in config.MARKETS:
            # 计算各公司在该市场的【最高单个产品】质量分
            scores = []
            for company in self.state.companies.values():
                max_quality = company.get_market_max_quality(market)
                # 找出是哪个产品获得了最高分
                best_product = ""
                for ptype in config.PRODUCT_TYPES:
                    pid = f"{market}_{ptype}"
                    if abs(company.products[pid].quality_score - max_quality) < 0.001:
                        best_product = pid
                        break
                scores.append((company.name, max_quality, best_product))
            
            # 按最高单个产品质量分排序（降序）
            scores.sort(key=lambda x: x[1], reverse=True)
            rankings[market] = scores
            
            # 分配品牌效应：获客折扣 + 竞争力加成
            for rank, (company_name, score, best_product) in enumerate(scores, 1):
                discounts[market][company_name] = config.BRAND_DISCOUNT.get(rank, 0.0)
                boosts[market][company_name] = config.BRAND_COMPETITIVENESS_BOOST.get(rank, 0.0)
        
        return discounts, boosts, rankings
    
    def _allocate_students(self, discounts: Dict, boosts: Dict):
        """分配学员到各公司各产品"""
        for market in config.MARKETS:
            for ptype in config.PRODUCT_TYPES:
                self._allocate_product_students(market, ptype, discounts, boosts)
    
    def _allocate_product_students(self, market: str, ptype: str, discounts: Dict, boosts: Dict):
        """分配某个市场-产品组合的学员"""
        product_id = f"{market}_{ptype}"
        base_cost = config.ACQUISITION_COST[market][ptype]
        # 应用市场波动：默认新增 × 需求因子
        default_new = int(config.DEFAULT_NEW_STUDENTS[ptype] * self.current_rule.market_shocks[market]["demand_factor"])
        
        # 计算各公司的获客能力
        company_attractiveness = {}
        total_marketing = 0.0
        
        for company in self.state.companies.values():
            product = company.products[product_id]
            discount = discounts[market].get(company.name, 0.0)
            effective_cost = base_cost * (1 - discount)
            
            # 营销预算可带来的最大获客数
            if effective_cost > 0 and product.marketing_budget > 0:
                max_from_marketing = int(product.marketing_budget / effective_cost)
            else:
                max_from_marketing = 0
            
            # 计算价格因子（第2轮起）
            price_factor = 1.0
            if self.current_rule.enable_pricing or self.current_rule.use_default_prices:
                default_price = config.DEFAULT_PRICES[market][ptype]
                actual_price = product.price if product.price > 0 else default_price
                
                if actual_price > default_price:
                    # 计算溢价率
                    premium_rate = (actual_price - default_price) / default_price
                    
                    # 第3轮起：销售对冲高价惩罚（上限30%）
                    sales_buffer = 0.0
                    if self.current_rule.round_num >= 3:
                        sales_buffer = product.sales * config.SALES_BUFFER_PER_PERSON
                        sales_buffer = min(sales_buffer, config.MAX_SALES_BUFFER)
                        sales_buffer = min(sales_buffer, premium_rate)
                    
                    effective_premium = max(0, premium_rate - sales_buffer)
                    elasticity = config.PRICE_ELASTICITY[market]
                    price_factor = max(config.MIN_PRICE_FACTOR, 1.0 - effective_premium * elasticity)
            
            # 品牌竞争力加成
            brand_boost = boosts[market].get(company.name, 0.0)
            
            # 产品类型竞争权重（1V1 > Class > APP）
            type_weight = config.PRODUCT_TYPE_WEIGHT.get(ptype, 1.0)
            
            # 吸引力 = 质量分 × 可获客数 × 价格因子 × (1 + 品牌竞争力加成) × 产品类型权重
            attractiveness = product.quality_score * max_from_marketing * price_factor * (1 + brand_boost) * type_weight
            company_attractiveness[company.name] = {
                "attractiveness": attractiveness,
                "max_from_marketing": max_from_marketing,
                "effective_cost": effective_cost,
                "quality": product.quality_score,
                "price_factor": price_factor,
            }
            total_marketing += max_from_marketing
        
        # 总新增需求
        total_demand = default_new + total_marketing
        
        # 检查市场容量（应用市场波动：容量 × 容量因子）
        if self.current_rule.enable_market_cap:
            current_market_total = self.state.market_students[market]
            market_cap = int(config.MARKET_CAPACITY[market] * self.current_rule.market_shocks[market]["capacity_factor"])
            
            if current_market_total + total_demand <= market_cap:
                allocation_ratio = 1.0
            else:
                remaining = market_cap - current_market_total
                if remaining <= 0:
                    allocation_ratio = 0.0
                elif total_demand > 0:
                    allocation_ratio = remaining / total_demand
                else:
                    allocation_ratio = 0.0
        else:
            allocation_ratio = 1.0
        
        # 分配学员
        # 修改：默认学生（自然流量）平均分配，不依赖营销投入
        # 营销获客部分按 attractiveness 比例分配
        total_attractiveness = sum(
            info["attractiveness"] for info in company_attractiveness.values()
        )
        
        for company in self.state.companies.values():
            info = company_attractiveness[company.name]
            product = company.products[product_id]
            
            # 默认学生：平均分配（自然流量，与营销投入无关）
            default_share = int(default_new / len(self.state.companies) * allocation_ratio)
            
            # 营销获客：按 attractiveness 比例分配
            if total_attractiveness > 0 and total_marketing > 0:
                marketing_share = int(total_marketing * info["attractiveness"] / total_attractiveness * allocation_ratio)
            else:
                marketing_share = int(total_marketing / len(self.state.companies) * allocation_ratio)
            
            max_possible = info["max_from_marketing"]
            
            # 营销获客受预算限制
            extra = min(marketing_share, max_possible)
            extra = max(0, extra)
            
            final_allocated = default_share + extra
            
            # 学员数 = 本轮分配到的数量
            product.students = final_allocated
            # 记录通过营销投入获得的学员数（用于计算获客成本）
            product.marketing_students = extra
        
        # 分配完成后，实时累加市场总人数（用于下一个产品类型的容量检查）
        self.state.market_students[market] += sum(
            c.products[product_id].students for c in self.state.companies.values()
        )
    
    def _check_capacity_and_refund(self):
        """检查师资约束，超出部分退费"""
        for company in self.state.companies.values():
            for product in company.products.values():
                capacity = product.teacher_capacity
                if product.students > capacity:
                    refund = product.students - capacity
                    product.refund_count += refund
                    product.students = capacity
    
    def _check_budget_and_refund(self):
        """检查学员预算约束，超出付费能力退费（应用市场波动）"""
        for company in self.state.companies.values():
            for product in company.products.values():
                # 动态预算上限 = 默认上限 × 波动因子
                market_budget = int(config.MARKET_BUDGET[product.market] * 
                                   self.current_rule.market_shocks[product.market]["budget_factor"])
                if product.price > market_budget:
                    product.refund_count += product.students
                    product.students = 0
    
    def _calculate_finance(self, discounts: Dict):
        """计算财务"""
        for company in self.state.companies.values():
            for product in company.products.values():
                product.valid_students = product.students
                
                # 收入
                product.revenue = product.valid_students * product.price
                
                # 教师成本
                product.teacher_cost = product.teachers * config.TEACHER_SALARY
                
                # 销售成本
                product.sales_cost = product.sales * config.SALES_SALARY
                
                # 获客成本（仅计算通过营销投入获得的学员）
                discount = discounts[product.market].get(company.name, 0.0)
                base_cost = config.ACQUISITION_COST[product.market][product.product_type]
                effective_cost = base_cost * (1 - discount)
                product.acquisition_cost = product.marketing_students * effective_cost
                
                # 研发费用（当轮支出）
                rd_cost = product.rd_budget if self.current_rule.enable_rd else 0
                
                # 汇总到公司
                company.total_revenue += product.revenue
                company.total_teacher_cost += product.teacher_cost
                company.total_sales_cost += product.sales_cost
                company.total_acquisition_cost += product.acquisition_cost
                company.total_rd_cost += rd_cost
            
            # 计算负债利息
            company.interest_payment = company.debt * config.INTEREST_RATE
            
            # 计算税收
            company.vat_tax = company.total_revenue * config.VAT_RATE
            pre_tax_profit = (
                company.total_revenue
                - company.total_teacher_cost
                - company.total_sales_cost
                - company.total_acquisition_cost
                - company.total_rd_cost
                - company.interest_payment
                - company.vat_tax
            )
            company.income_tax = max(pre_tax_profit, 0) * config.INCOME_TAX_RATE
            company.total_tax = company.vat_tax + company.income_tax
            
            # 净利润
            company.net_profit = pre_tax_profit - company.income_tax
            
            # 更新资金
            company.cash += company.net_profit
            
            # 处理负债
            if company.cash < 0:
                company.debt += abs(company.cash)
                company.cash = 0
            elif company.debt > 0:
                if company.cash >= company.debt:
                    company.cash -= company.debt
                    company.debt = 0
                else:
                    company.debt -= company.cash
                    company.cash = 0
    
    def _update_market_totals(self):
        """更新各市场学员总数"""
        for market in config.MARKETS:
            total = 0
            for company in self.state.companies.values():
                for ptype in config.PRODUCT_TYPES:
                    pid = f"{market}_{ptype}"
                    total += company.products[pid].students
            self.state.market_students[market] = total
    
    def _update_quality_scores(self):
        """更新质量分（退费惩罚）"""
        for company in self.state.companies.values():
            for product in company.products.values():
                if product.refund_count > 0:
                    product.quality_score *= (1 - config.QUALITY_PENALTY)
                    product.quality_score = max(config.MIN_QUALITY, product.quality_score)
    
    def _get_round_results(self) -> Dict:
        """获取本轮结果"""
        results = {
            "round": self.state.round_number,
            "rule": {
                "name": self.current_rule.name,
                "description": self.current_rule.description,
                "decision_variables": self.current_rule.decision_variables,
                "active_mechanics": self.current_rule.active_mechanics,
            },
            "market_totals": dict(self.state.market_students),
            "brand_rankings": getattr(self, '_brand_rankings', {}),
            "companies": {},
        }
        
        for company in self.state.companies.values():
            company_data = {
                "cash": company.cash,
                "debt": company.debt,
                "net_profit": company.net_profit,
                "total_revenue": company.total_revenue,
                "total_teacher_cost": company.total_teacher_cost,
                "total_sales_cost": company.total_sales_cost,
                "total_acquisition_cost": company.total_acquisition_cost,
                "total_rd_cost": company.total_rd_cost,
                "interest_payment": company.interest_payment,
                "vat_tax": company.vat_tax,
                "income_tax": company.income_tax,
                "total_tax": company.total_tax,
                "products": {},
            }
            
            for pid, product in company.products.items():
                company_data["products"][pid] = {
                    "quality_score": round(product.quality_score, 2),
                    "students": product.students,
                    "teachers": product.teachers,
                    "price": product.price,
                    "marketing_budget": product.marketing_budget,
                    "rd_budget": product.rd_budget,
                    "revenue": product.revenue,
                    "teacher_cost": product.teacher_cost,
                    "sales_cost": product.sales_cost,
                    "acquisition_cost": product.acquisition_cost,
                    "refund_count": product.refund_count,
                    "valid_students": product.valid_students,
                    "marketing_students": product.marketing_students,
                }
            
            results["companies"][company.name] = company_data
        
        return results
    
    def get_final_ranking(self) -> List[Tuple[str, float, float, float]]:
        """获取最终排名"""
        rankings = []
        for company in self.state.companies.values():
            net_worth = company.cash - company.debt
            rankings.append((company.name, company.cash, company.debt, net_worth))
        
        rankings.sort(key=lambda x: x[3], reverse=True)
        return rankings
