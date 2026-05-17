"""
TechMark 教育沙盘模拟 - 国际化（中英文）
"""

TRANSLATIONS = {
    "zh": {
        "title": "📚 PalFish Business MindSet",
        "subtitle": "TechMark 框架下的教育企业商业模拟经营",
        "control_panel": "🎮 控制面板",
        "create_game": "创建游戏",
        "player_count": "玩家数量",
        "player_name": "玩家",
        "create_btn": "🚀 创建新游戏",
        "current_round": "当前轮次",
        "players": "玩家",
        "full_rules": "📖 完整规则",
        "restart": "🔄 重新开始",
        "welcome": "👈 请在侧边栏创建游戏",
        "players_range": "2-6家",
        "rounds": "5轮",
        "initial_cash": "1000万",
        "round_title": "第 {} 轮：{}",
        "input_decisions": "📝 填写决策",
        "input_method": "输入方式",
        "matrix_input": "矩阵表格填写",
        "csv_upload": "上传CSV文件",
        "company": "公司",
        "round": "轮次",
        "net_profit": "净利润",
        "cash": "现金",
        "debt": "负债",
        "net_worth": "净资产",
        "rd_cost": "💰 研发费用（万元）",
        "marketing_cost": "📢 市场投入（万元）",
        "teachers": "👨‍🏫 教师人数",
        "sales": "💼 销售人数",
        "pricing": "💵 产品定价（元）",
        "rd": "研发费用",
        "marketing": "市场投入",
        "price": "产品定价",
        "run_round": "🚀 运行第 {} 轮",
        "csv_template": "📥 CSV模板说明",
        "csv_notes": """CSV文件格式（英文表头）：

```csv
RD,1V1,Class,APP
T1,50,100,0
T2,50,100,0
T3,0,100,100

Marketing,1V1,Class,APP
T1,100,0,0
T2,50,100,0
T3,0,100,100

Teachers,1V1,Class,APP
T1,100,10,0
T2,10,50,0
T3,10,10,0
```

**单位说明：**
- RD / Marketing = 万元
- Teachers = 人
- Price = 元（第2轮起）
- Sales = 人（第3轮起）
""",
        "download_template": "⬇️ 下载CSV模板",
        "result_summary": "✅ 第 {} 轮结果",
        "market_overview": "📊 市场概览",
        "market": "市场",
        "product_detail": "📋 产品经营明细",
        "total_revenue": "总收入",
        "teacher_cost": "教师成本",
        "acquisition_cost": "获客成本",
        "rd_expense": "研发成本",
        "interest": "利息",
        "product": "产品",
        "market_name": "市场",
        "type": "类型",
        "quality": "质量分",
        "students": "学员",
        "teacher_count": "教师",
        "capacity": "上限",
        "fill_rate": "满班率",
        "refund": "退费",
        "mk_wan": "营销(万)",
        "rd_wan": "研发(万)",
        "game_over": "🏆 游戏结束",
        "final_ranking": "最终排名",
        "history": "📈 历史趋势",
        "cash_trend": "现金趋势",
        "profit_trend": "净利润",
        "decision_vars": "📋 本轮决策变量",
        "mechanics": "⚙️ 生效机制",
        "language": "🌐 语言 / Language",
        "total_mk": "市场投入总计",
        "mk_remaining": "剩余",
        "mk_used": "已用",
        "mk_cap": "上限",
        "mk_over": "市场投入超额",
        "brand_ranking": "🏆 品牌排名",
        "brand_rank": "排名",
        "brand_boost": "竞争力加成",
        "brand_discount": "获客折扣",
        "best_product": "标杆产品",
        "rerun_round": "🔄 重新运行本轮",
        "rerun_hint": "发现输入有误？可以重新运行本轮，修改决策后覆盖之前的结果。",
        "rerun_success": "已恢复上轮开始前的状态，请修改决策后重新运行。",
        "public_info": "📢 公开信息（市场情报）",
        "students_price": "学员/售价",
        "landing_title": "👋 请选择你的身份",
        "i_am_company": "我是 {}",
        "i_am_admin": "🎙️ 我是主持人",
        "submit_decisions": "✅ 提交决策",
        "submitted_wait": "✅ 已提交，等待主持人运行本轮",
        "admin_title": "🎙️ 主持人控制台",
        "submission_status": "📋 提交状态",
        "submitted": "已提交",
        "not_submitted": "未提交",
        "run_round_admin": "🚀 运行第 {} 轮",
        "all_submitted": "✅ 所有公司已提交，可以运行本轮",
        "waiting_for": "⏳ 等待 {} 家公司提交",
        "game_not_created": "⚠️ 游戏尚未创建",
        "create_game_first": "请在右侧边栏创建游戏",
        "view_results": "📊 查看结果",
        "company_page_title": "🏢 {} - 第 {} 轮决策",
        "round_status": "第 {} 轮",
        "download_results": "⬇️ 下载本轮结果",
        "submitted_at": "提交时间",
        "player_link": "玩家链接",
        "admin_link": "主持人链接",
        "copy_link": "复制链接",
        "link_copied": "链接已复制",
        "market_distribution": "📊 市场分布",
        "revenue_comparison": "📊 营收对比",
        "revenue_10k": "营收 (万)",
    },
    "en": {
        "title": "📚 PalFish Business MindSet",
        "subtitle": "Business simulation for education companies under TechMark framework",
        "control_panel": "🎮 Control Panel",
        "create_game": "Create Game",
        "player_count": "Player Count",
        "player_name": "Player",
        "create_btn": "🚀 Create New Game",
        "current_round": "Current Round",
        "players": "Players",
        "full_rules": "📖 Full Rules",
        "restart": "🔄 Restart",
        "welcome": "👈 Please create a game in the sidebar",
        "players_range": "2-6 Companies",
        "rounds": "5 Rounds",
        "initial_cash": "10M CNY",
        "round_title": "Round {}: {}",
        "input_decisions": "📝 Input Decisions",
        "input_method": "Input Method",
        "matrix_input": "Matrix Input",
        "csv_upload": "Upload CSV",
        "company": "Company",
        "round": "Round",
        "net_profit": "Net Profit",
        "cash": "Cash",
        "debt": "Debt",
        "net_worth": "Net Worth",
        "rd_cost": "💰 R&D (10K CNY)",
        "marketing_cost": "📢 Marketing (10K CNY)",
        "teachers": "👨‍🏫 Teachers",
        "sales": "💼 Sales Staff",
        "pricing": "💵 Pricing (CNY)",
        "rd": "R&D",
        "marketing": "Marketing",
        "price": "Price",
        "run_round": "🚀 Run Round {}",
        "csv_template": "📥 CSV Template",
        "csv_notes": """CSV format (English headers):

```csv
RD,1V1,Class,APP
T1,50,100,0
T2,50,100,0
T3,0,100,100

Marketing,1V1,Class,APP
T1,100,0,0
T2,50,100,0
T3,0,100,100

Teachers,1V1,Class,APP
T1,100,10,0
T2,10,50,0
T3,10,10,0
```

**Unit Notes:**
- RD / Marketing = 10K CNY
- Teachers = people
- Price = CNY (from Round 2)
- Sales = people (from Round 3)
""",
        "download_template": "⬇️ Download CSV Template",
        "result_summary": "✅ Round {} Results",
        "market_overview": "📊 Market Overview",
        "market": "Market",
        "product_detail": "📋 Product Details",
        "total_revenue": "Revenue",
        "teacher_cost": "Teacher Cost",
        "acquisition_cost": "Acquisition Cost",
        "rd_expense": "R&D Cost",
        "interest": "Interest",
        "product": "Product",
        "market_name": "Market",
        "type": "Type",
        "quality": "Quality",
        "students": "Students",
        "teacher_count": "Teachers",
        "capacity": "Capacity",
        "fill_rate": "Fill Rate",
        "refund": "Refund",
        "mk_wan": "Mkt(10K)",
        "rd_wan": "R&D(10K)",
        "game_over": "🏆 Game Over",
        "final_ranking": "Final Ranking",
        "history": "📈 History",
        "cash_trend": "Cash Trend",
        "profit_trend": "Net Profit",
        "decision_vars": "📋 Decision Variables",
        "mechanics": "⚙️ Active Mechanics",
        "language": "🌐 语言 / Language",
        "total_mk": "Total Marketing",
        "mk_remaining": "Remaining",
        "mk_used": "Used",
        "mk_cap": "Cap",
        "mk_over": "Marketing Over Limit",
        "brand_ranking": "🏆 Brand Ranking",
        "brand_rank": "Rank",
        "brand_boost": "Competitiveness Boost",
        "brand_discount": "Acquisition Discount",
        "best_product": "Best Product",
        "rerun_round": "🔄 Rerun This Round",
        "rerun_hint": "Found an input error? You can rerun this round and overwrite the previous results.",
        "rerun_success": "Restored to pre-round state. Please modify decisions and rerun.",
        "public_info": "📢 Public Information (Market Intelligence)",
        "students_price": "Students/Price",
        "landing_title": "👋 Select Your Role",
        "i_am_company": "I am {}",
        "i_am_admin": "🎙️ I am Admin",
        "submit_decisions": "✅ Submit Decisions",
        "submitted_wait": "✅ Submitted, waiting for admin to run round",
        "admin_title": "🎙️ Admin Console",
        "submission_status": "📋 Submission Status",
        "submitted": "Submitted",
        "not_submitted": "Not Submitted",
        "run_round_admin": "🚀 Run Round {}",
        "all_submitted": "✅ All companies submitted, ready to run",
        "waiting_for": "⏳ Waiting for {} companies",
        "game_not_created": "⚠️ Game not created",
        "create_game_first": "Please create game in the sidebar",
        "view_results": "📊 View Results",
        "company_page_title": "🏢 {} - Round {} Decisions",
        "round_status": "Round {}",
        "download_results": "⬇️ Download Round Results",
        "submitted_at": "Submitted At",
        "player_link": "Player Link",
        "admin_link": "Admin Link",
        "copy_link": "Copy Link",
        "link_copied": "Link copied",
        "market_distribution": "📊 Market Distribution",
        "revenue_comparison": "📊 Revenue Comparison",
        "revenue_10k": "Revenue (10K)",
    }
}


def get_text(key: str, lang: str = "zh") -> str:
    """获取翻译文本"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)
