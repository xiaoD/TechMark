"""
TechMark 教育沙盘模拟 - Streamlit Web界面 (支持中英文)
启动: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import os

from models import GameState
from game_engine import GameEngine
from round_rules import get_round_rule, get_all_rules_summary
from csv_handler import save_round_results, save_final_ranking
from snapshot_manager import (
    save_pre_round_snapshot, load_pre_round_snapshot,
    has_snapshot, delete_snapshot, delete_all_snapshots,
)
from i18n import get_text
import config

st.set_page_config(page_title="TechMark Education Simulation", page_icon="🎮", layout="wide")

# ============== 样式 ==============
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: bold; color: #1f77b4; text-align: center; }
    .round-title { font-size: 1.6rem; font-weight: bold; color: #ff7f0e; margin: 0.5rem 0; }
    .matrix-title { font-size: 1.1rem; font-weight: bold; color: #333; margin: 1rem 0 0.3rem 0; }
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 状态初始化
# =============================================================================
def init_state():
    if 'game_state' not in st.session_state:
        st.session_state.game_state = None
    if 'current_round' not in st.session_state:
        st.session_state.current_round = 0
    if 'round_results' not in st.session_state:
        st.session_state.round_results = {}
    if 'companies' not in st.session_state:
        st.session_state.companies = ["Company A", "Company B"]
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'lang' not in st.session_state:
        st.session_state.lang = "zh"

init_state()

lang = st.session_state.lang


# =============================================================================
# 辅助函数
# =============================================================================
def create_matrix_df(values=None):
    if values is None:
        values = [[0]*3 for _ in range(3)]
    return pd.DataFrame(
        values,
        index=["T1", "T2", "T3"],
        columns=["1V1", "Class", "APP"]
    )


def t(key):
    """快捷翻译函数"""
    return get_text(key, lang)


def parse_uploaded_file(uploaded_file, round_rule):
    """解析英文CSV文件"""
    try:
        df = pd.read_csv(uploaded_file, header=None)
        lines = df.values.tolist()

        rd_matrix = [[0]*3 for _ in range(3)]
        marketing_matrix = [[0]*3 for _ in range(3)]
        teacher_matrix = [[0]*3 for _ in range(3)]
        sales_matrix = [[0]*3 for _ in range(3)]
        pricing_matrix = [[0]*3 for _ in range(3)]

        current_matrix = None
        row_idx = 0

        for line in lines:
            if all(str(x) in ['nan', '', '0', 0] for x in line):
                continue

            first_col = str(line[0]).strip().lower() if len(line) > 0 else ""
            if first_col in ['rd', '研发']:
                current_matrix = 'rd'
                row_idx = 0
                continue
            elif first_col in ['marketing', '市场', 'market']:
                current_matrix = 'marketing'
                row_idx = 0
                continue
            elif first_col in ['teachers', '教师', 'teacher']:
                current_matrix = 'teacher'
                row_idx = 0
                continue
            elif first_col in ['sales', '销售', 'sale']:
                current_matrix = 'sales'
                row_idx = 0
                continue
            elif first_col in ['price', '定价', 'pricing']:
                current_matrix = 'pricing'
                row_idx = 0
                continue

            if current_matrix and row_idx < 3:
                vals = []
                for i in range(1, 4):
                    if i < len(line):
                        try:
                            v = float(line[i])
                            vals.append(int(v) if not pd.isna(v) else 0)
                        except:
                            vals.append(0)
                    else:
                        vals.append(0)

                if current_matrix == 'rd':
                    rd_matrix[row_idx] = vals
                elif current_matrix == 'marketing':
                    marketing_matrix[row_idx] = vals
                elif current_matrix == 'teacher':
                    teacher_matrix[row_idx] = vals
                elif current_matrix == 'sales':
                    sales_matrix[row_idx] = vals
                elif current_matrix == 'pricing':
                    pricing_matrix[row_idx] = vals
                row_idx += 1

        # 转换为决策字典
        decisions = {}
        markets = ["T1", "T2", "T3"]
        products = ["1V1", "Class", "APP"]

        for i, market in enumerate(markets):
            for j, ptype in enumerate(products):
                pid = f"{market}_{ptype}"
                dec = {}
                if round_rule.enable_rd:
                    dec["rd"] = rd_matrix[i][j] * 10000
                if round_rule.enable_marketing:
                    dec["marketing"] = marketing_matrix[i][j] * 10000
                if round_rule.enable_teachers:
                    dec["teachers"] = teacher_matrix[i][j]
                if round_rule.round_num >= 3:
                    dec["sales"] = sales_matrix[i][j]
                if round_rule.enable_pricing:
                    price = pricing_matrix[i][j]
                    if price > 0:
                        dec["price"] = price
                    else:
                        dec["price"] = config.DEFAULT_PRICES[market][ptype]
                elif round_rule.use_default_prices:
                    dec["price"] = config.DEFAULT_PRICES[market][ptype]
                decisions[pid] = dec

        return decisions
    except Exception as e:
        st.error(f"Parse error: {e}")
        return None


def matrix_to_decisions(rd_df, marketing_df, teacher_df, sales_df, pricing_df, round_rule):
    """将矩阵DataFrame转换为决策字典"""
    decisions = {}
    markets = ["T1", "T2", "T3"]
    products = ["1V1", "Class", "APP"]

    for i, market in enumerate(markets):
        for j, ptype in enumerate(products):
            pid = f"{market}_{ptype}"
            dec = {}
            if round_rule.enable_rd:
                dec["rd"] = rd_df.iloc[i, j] * 10000
            if round_rule.enable_marketing:
                dec["marketing"] = marketing_df.iloc[i, j] * 10000
            if round_rule.enable_teachers:
                dec["teachers"] = int(teacher_df.iloc[i, j])
            if round_rule.round_num >= 3:
                dec["sales"] = int(sales_df.iloc[i, j])
            if round_rule.enable_pricing:
                dec["price"] = pricing_df.iloc[i, j]
            elif round_rule.use_default_prices:
                dec["price"] = config.DEFAULT_PRICES[market][ptype]
            decisions[pid] = dec

    return decisions


def get_prefilled_value(decisions, company_name, var_name, market_idx, prod_idx, default=0):
    """从上次决策中获取预填充值"""
    if decisions is None or company_name not in decisions:
        return default
    markets = ["T1", "T2", "T3"]
    products = ["1V1", "Class", "APP"]
    pid = f"{markets[market_idx]}_{products[prod_idx]}"
    val = decisions[company_name].get(pid, {}).get(var_name, default)
    if var_name in ("rd", "marketing") and val != 0:
        val = val / 10000
    return val


def create_prefilled_matrix(prefill_decisions, company_name, var_name, round_rule, default_values=None):
    """创建预填充的矩阵DataFrame（用于重跑时恢复上次输入）"""
    markets = ["T1", "T2", "T3"]
    products = ["1V1", "Class", "APP"]
    values = []
    for i, market in enumerate(markets):
        row = []
        for j, ptype in enumerate(products):
            default = default_values[i][j] if default_values else 0
            val = get_prefilled_value(prefill_decisions, company_name, var_name, i, j, default)
            row.append(val)
        values.append(row)
    return pd.DataFrame(values, index=markets, columns=products)


# =============================================================================
# 显示结果函数
# =============================================================================
def show_final_results():
    st.markdown(f'<div class="round-title">{t("game_over")}</div>', unsafe_allow_html=True)
    engine = GameEngine(st.session_state.game_state)
    rankings = engine.get_final_ranking()

    rank_data = []
    for rank, (name, cash, debt, net) in enumerate(rankings, 1):
        em = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
        rank_data.append({
            t("final_ranking").split()[0] if ' ' in t("final_ranking") else "Rank": f"{em} #{rank}",
            t("company"): name,
            "Net Worth": f"{net:,.0f}",
            "Cash": f"{cash:,.0f}",
            "Debt": f"{debt:,.0f}"
        })

    st.dataframe(pd.DataFrame(rank_data), hide_index=True, use_container_width=True)
    save_final_ranking(rankings)
    # 游戏结束，清理所有快照
    delete_all_snapshots()
    st.balloons()

    # 历史趋势
    st.markdown("---")
    st.markdown(f"### {t('history')}")
    hist = []
    for rn in range(1, config.TOTAL_ROUNDS + 1):
        if rn in st.session_state.round_results:
            res = st.session_state.round_results[rn]
            for cn, d in res["companies"].items():
                hist.append({"Round": rn, "Company": cn, "Cash": d["cash"], "Profit": d["net_profit"], "Revenue": d["total_revenue"]})

    if hist:
        dfh = pd.DataFrame(hist)
        st.markdown(f"**{t('cash_trend')}**")
        st.line_chart(dfh.pivot(index="Round", columns="Company", values="Cash"))
        st.markdown(f"**{t('profit_trend')}**")
        st.bar_chart(dfh.pivot(index="Round", columns="Company", values="Profit"))


def generate_summary(company_name, company_data, all_results, input_data):
    """生成简短的经营总结"""
    d = company_data
    
    # 基础数据
    total_students = sum(p["students"] for p in d["products"].values())
    total_refund = sum(p["refund_count"] for p in d["products"].values())
    total_rd = sum(p["rd_budget"] for p in d["products"].values())
    total_mk = sum(p["marketing_budget"] for p in d["products"].values())
    total_teachers = sum(p["teachers"] for p in d["products"].values())
    
    # 找出收入最高的产品
    top_product = max(d["products"].items(), key=lambda x: x[1]["revenue"])
    
    # 找出有退费的产品
    refund_products = [pid for pid, p in d["products"].items() if p["refund_count"] > 0]
    
    # 计算利润率
    profit_rate = d["net_profit"] / d["total_revenue"] * 100 if d["total_revenue"] > 0 else 0
    
    # 与其他公司对比
    all_profits = {cn: all_results["companies"][cn]["net_profit"] for cn in all_results["companies"]}
    rank = sorted(all_profits.items(), key=lambda x: x[1], reverse=True)
    rank_str = ""
    for i, (name, profit) in enumerate(rank, 1):
        if name == company_name:
            rank_str = f"净利润排名第{i}"
            break
    
    # 构建总结
    parts = []
    
    # 整体盈亏
    if d["net_profit"] > 0:
        parts.append(f"✅ 本**盈利** {d['net_profit']:,.0f}元（{rank_str}），利润率 {profit_rate:.1f}%")
    else:
        parts.append(f"❌ 本**亏损** {abs(d['net_profit']):,.0f}元（{rank_str}）")
    
    # 学员情况
    parts.append(f"👨‍🎓 总学员 {total_students:,}人，主要收入来源 **{top_product[0]}**（{top_product[1]['revenue']:,.0f}元）")
    
    # 投入情况
    parts.append(f"💰 投入：研发 {total_rd/10000:.0f}万 | 营销 {total_mk/10000:.0f}万 | 教师 {total_teachers}人")
    
    # 问题提示
    issues = []
    if total_refund > 0:
        issues.append(f"有 {total_refund} 人退费（{'、'.join(refund_products[:3])}）")
    if d["debt"] > 0:
        issues.append(f"负债 {d['debt']:,.0f}元，下轮需支付利息")
    
    if issues:
        parts.append(f"⚠️ 注意：{'；'.join(issues)}")
    
    return " | ".join(parts)


def show_round_results(res):
    st.divider()
    st.markdown(f"### {t('result_summary').format(st.session_state.current_round, '')}")

    # 市场概览
    st.markdown(f"#### {t('market_overview')}")
    mc = st.columns(len(st.session_state.companies) + 1)
    with mc[0]:
        st.markdown(f"<div style='text-align:center'><b>{t('market')}</b></div>", unsafe_allow_html=True)
        for m, total in res["market_totals"].items():
            cap = config.MARKET_CAPACITY[m]
            pct = total / cap * 100
            st.markdown(f"<div style='text-align:center'>{m}: {total:,}/{cap:,} ({pct:.1f}%)</div>", unsafe_allow_html=True)

    for i, cn in enumerate(st.session_state.companies):
        with mc[i + 1]:
            d = res["companies"][cn]
            st.markdown(f"<div style='text-align:center'><b>{cn}</b></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center'>💰 {d['cash']:,.0f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center'>📈 {d['net_profit']:,.0f}</div>", unsafe_allow_html=True)

    # 品牌排名
    if res.get("brand_rankings"):
        st.markdown("---")
        st.markdown(f"#### {t('brand_ranking')}")
        brand_cols = st.columns(3)
        for i, market in enumerate(["T1", "T2", "T3"]):
            rankings = res["brand_rankings"].get(market, [])
            if rankings:
                with brand_cols[i]:
                    st.markdown(f"**{market}**")
                    for rank, (company_name, score, best_product) in enumerate(rankings[:3], 1):
                        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
                        boost = config.BRAND_COMPETITIVENESS_BOOST.get(rank, 0.0) * 100
                        discount = config.BRAND_DISCOUNT.get(rank, 0.0) * 100
                        st.markdown(
                            f"{emoji} **{company_name}** (Q={score:.1f})\n"
                            f"&nbsp;&nbsp;&nbsp;&nbsp;{t('best_product')}: `{best_product}`\n"
                            f"&nbsp;&nbsp;&nbsp;&nbsp;+{boost:.0f}% {t('brand_boost')} | -{discount:.0f}% {t('brand_discount')}"
                        )

    # 公开信息（市场情报）
    st.markdown("---")
    st.markdown(f"#### {t('public_info')}")
    
    public_data = []
    for pid in config.ALL_PRODUCTS:
        row = {"Product": pid}
        for cn in st.session_state.companies:
            p = res["companies"][cn]["products"][pid]
            row[f"{cn}"] = f"{p['students']} / {p['price']:,.0f}"
        public_data.append(row)
    
    pub_df = pd.DataFrame(public_data)
    st.dataframe(pub_df, hide_index=True, use_container_width=True)

    # 产品明细
    st.markdown("---")
    st.markdown(f"#### {t('product_detail')}")

    for cn in st.session_state.companies:
        d = res["companies"][cn]
        with st.expander(f"🏢 {cn} - {t('cash')} {d['cash']:,.0f} | {t('net_worth')} {d['cash'] - d['debt']:,.0f}", expanded=True):
            
            # ====== 输入决策明细 ======
            st.markdown("**📥 Input Decisions**")
            input_data = []
            if "input_decisions" in res and cn in res["input_decisions"]:
                for pid, dec in res["input_decisions"][cn].items():
                    market, ptype = pid.split('_')
                    row = {"Product": pid}
                    if "rd" in dec:
                        row["R&D(10K)"] = f"{dec['rd']/10000:.1f}"
                    if "teachers" in dec:
                        row["Teachers"] = dec["teachers"]
                    if "sales" in dec:
                        row["Sales"] = dec["sales"]
                    if "marketing" in dec:
                        row["Mkt(10K)"] = f"{dec['marketing']/10000:.1f}"
                    if "price" in dec:
                        row["Price"] = f"{dec['price']:,.0f}"
                    input_data.append(row)
                
                if input_data:
                    st.dataframe(pd.DataFrame(input_data), hide_index=True, use_container_width=True)
            
            # ====== 经营结果 ======
            st.markdown("**📊 Operating Results**")
            product_rows = []
            for pid, p in d["products"].items():
                market, ptype = pid.split('_')
                teacher_cap = config.TEACHER_CAPACITY[ptype]
                if teacher_cap == float('inf'):
                    capacity = "∞"
                    fill_rate = "N/A"
                else:
                    capacity = p["teachers"] * teacher_cap
                    fill_rate = f"{p['students']/capacity*100:.1f}%" if capacity > 0 else "N/A"

                product_rows.append({
                    "Product": pid,
                    "Market": market,
                    "Type": ptype,
                    "Quality": round(p["quality_score"], 1),
                    "Students": p["students"],
                    "Teachers": p["teachers"],
                    "Capacity": capacity,
                    "Fill Rate": fill_rate,
                    "Price": f"{p['price']:,.0f}",
                    "Revenue": f"{p['revenue']:,.0f}",
                    "Refund": p["refund_count"],
                    "Mkt(10K)": f"{p['marketing_budget']/10000:.1f}",
                    "R&D(10K)": f"{p['rd_budget']/10000:.1f}",
                })

            st.dataframe(pd.DataFrame(product_rows), hide_index=True, use_container_width=True)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(t("total_revenue"), f"{d['total_revenue']:,.0f}")
            c2.metric(t("teacher_cost"), f"{d['total_teacher_cost']:,.0f}")
            c3.metric(t("acquisition_cost"), f"{d['total_acquisition_cost']:,.0f}")
            c4.metric(t("rd_expense"), f"{d['total_rd_cost']:,.0f}")
            c5.metric(t("interest"), f"{d['interest_payment']:,.0f}")
            
            # ====== 简短总结 ======
            st.markdown("**📝 Summary**")
            summary = generate_summary(cn, d, res, input_data if 'input_data' in dir() else [])
            st.info(summary)
    
    # ====== 重新运行本轮 ======
    st.markdown("---")
    current_r = st.session_state.current_round
    if has_snapshot(current_r):
        st.markdown(f"#### {t('rerun_round')}")
        st.caption(t("rerun_hint"))
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button(t("rerun_round"), key=f"rerun_{current_r}", use_container_width=True):
                # 从快照恢复
                loaded = load_pre_round_snapshot(current_r)
                if loaded:
                    game_state, input_decisions, round_results = loaded
                    # 恢复状态
                    st.session_state.game_state = game_state
                    st.session_state.round_results = round_results
                    st.session_state.current_round = current_r - 1
                    # 保存上次的输入决策，用于预填充
                    st.session_state.rerun_input_decisions = input_decisions
                    st.session_state.rerun_round = current_r
                    # 删除当前轮的结果文件（可选）
                    if current_r in st.session_state.round_results:
                        del st.session_state.round_results[current_r]
                    st.success(t("rerun_success"))
                    st.rerun()


# =============================================================================
# 游戏进行函数
# =============================================================================
def show_round_play():
    round_num = st.session_state.current_round + 1
    rule = get_round_rule(round_num)
    state = st.session_state.game_state

    # 检查是否处于重跑模式
    is_rerun = False
    prefill_decisions = None
    if hasattr(st.session_state, 'rerun_round') and st.session_state.rerun_round == round_num:
        is_rerun = True
        prefill_decisions = getattr(st.session_state, 'rerun_input_decisions', None)
        st.warning(f"⚠️ {t('rerun_success')}", icon="🔄")
    elif hasattr(st.session_state, 'rerun_round'):
        # 清除过期的重跑标记
        del st.session_state.rerun_round
        if hasattr(st.session_state, 'rerun_input_decisions'):
            del st.session_state.rerun_input_decisions

    st.markdown(f'<div class="round-title">{t("round_title").format(round_num, rule.name)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box">{rule.description}</div>', unsafe_allow_html=True)

    # 显示市场波动信息（如果有）
    has_shock = any(
        shock != {"budget_factor": 1.0, "capacity_factor": 1.0, "demand_factor": 1.0}
        for shock in rule.market_shocks.values()
    )
    if has_shock:
        st.markdown("### ⚡ Market Shock")
        shock_cols = st.columns(3)
        for i, market in enumerate(["T1", "T2", "T3"]):
            shock = rule.market_shocks[market]
            with shock_cols[i]:
                budget_change = (shock["budget_factor"] - 1) * 100
                cap_change = (shock["capacity_factor"] - 1) * 100
                demand_change = (shock["demand_factor"] - 1) * 100
                
                emoji = "📈" if budget_change > 0 else "📉" if budget_change < 0 else "➡️"
                st.markdown(f"**{emoji} {market}**")
                st.markdown(f"Budget: {budget_change:+.0f}%")
                st.markdown(f"Capacity: {cap_change:+.0f}%")
                st.markdown(f"Demand: {demand_change:+.0f}%")

    # 决策变量标签
    st.markdown(f"### {t('decision_vars')}")
    dv = rule.decision_variables
    cols = st.columns(len(dv) if dv else 1)
    for i, var in enumerate(dv):
        cols[i].markdown(f"<div style='text-align:center;padding:8px;background:#e8f4f8;border-radius:8px;'>✏️ {var}</div>", unsafe_allow_html=True)

    st.markdown(f"### {t('mechanics')}")
    st.markdown(" | ".join([f"✅ {m}" for m in rule.active_mechanics]))
    st.divider()

    # 决策输入区域
    st.markdown(f"### {t('input_decisions')}")

    # 两种输入方式
    input_mode = st.radio(t("input_method"), [t("matrix_input"), t("csv_upload")], horizontal=True)

    all_decisions = {}

    for company_name in st.session_state.companies:
        company = state.companies[company_name]

        with st.expander(f"🏢 {company_name}", expanded=True):
            # 公司状态
            c1, c2, c3 = st.columns(3)
            c1.metric(t("cash"), f"{company.cash:,.0f}")
            c2.metric(t("debt"), f"{company.debt:,.0f}")
            c3.metric(t("net_worth"), f"{company.cash - company.debt:,.0f}")

            if input_mode == t("csv_upload"):
                # 文件上传模式
                uploaded = st.file_uploader(f"Upload {company_name} CSV", type=['csv'], key=f"up_{company_name}_r{round_num}")

                if uploaded:
                    decisions = parse_uploaded_file(uploaded, rule)
                    if decisions:
                        all_decisions[company_name] = decisions
                        st.success(f"✅ Parsed {company_name} CSV")
                        preview = []
                        for pid, dec in decisions.items():
                            preview.append({"Product": pid, **dec})
                        st.dataframe(pd.DataFrame(preview), hide_index=True)
                else:
                    st.info("Please upload CSV file")

            else:
                # 矩阵表格填写模式（支持重跑时预填充）
                if rule.enable_rd:
                    st.markdown(f'<div class="matrix-title">{t("rd_cost")}</div>', unsafe_allow_html=True)
                    rd_df = st.data_editor(
                        create_prefilled_matrix(prefill_decisions, company_name, "rd", rule),
                        key=f"rd_{company_name}_r{round_num}",
                        num_rows="fixed",
                        use_container_width=True,
                        column_config={
                            "1V1": st.column_config.NumberColumn(min_value=0, step=1),
                            "Class": st.column_config.NumberColumn(min_value=0, step=1),
                            "APP": st.column_config.NumberColumn(min_value=0, step=1),
                        }
                    )
                else:
                    rd_df = create_matrix_df()

                if rule.enable_marketing:
                    st.markdown(f'<div class="matrix-title">{t("marketing_cost")}</div>', unsafe_allow_html=True)
                    marketing_df = st.data_editor(
                        create_prefilled_matrix(prefill_decisions, company_name, "marketing", rule),
                        key=f"mk_{company_name}_r{round_num}",
                        num_rows="fixed",
                        use_container_width=True,
                        column_config={
                            "1V1": st.column_config.NumberColumn(min_value=0, step=1),
                            "Class": st.column_config.NumberColumn(min_value=0, step=1),
                            "APP": st.column_config.NumberColumn(min_value=0, step=1),
                        }
                    )
                    # 显示总市场投入
                    total_mk = marketing_df.sum().sum()
                    cap_wan = config.ROUND_MARKETING_CAP_WAN.get(round_num)
                    if cap_wan:
                        remaining = cap_wan - total_mk
                        if remaining < 0:
                            st.error(f"⚠️ {t('mk_over')}! {t('mk_used')} {total_mk:.0f} / {t('mk_cap')} {cap_wan}, {t('mk_over')} {abs(remaining):.0f}")
                        else:
                            st.info(f"💡 {t('total_mk')}: {t('mk_used')} **{total_mk:.0f}** / {t('mk_cap')} **{cap_wan}**, {t('mk_remaining')} **{remaining:.0f}**")
                    else:
                        st.info(f"💡 {t('total_mk')}: **{total_mk:.0f}**")
                else:
                    marketing_df = create_matrix_df()

                if rule.enable_teachers:
                    st.markdown(f'<div class="matrix-title">{t("teachers")}</div>', unsafe_allow_html=True)
                    teacher_df = st.data_editor(
                        create_prefilled_matrix(prefill_decisions, company_name, "teachers", rule),
                        key=f"th_{company_name}_r{round_num}",
                        num_rows="fixed",
                        use_container_width=True,
                        column_config={
                            "1V1": st.column_config.NumberColumn(min_value=0, step=1),
                            "Class": st.column_config.NumberColumn(min_value=0, step=1),
                            "APP": st.column_config.NumberColumn(min_value=0, step=1),
                        }
                    )
                else:
                    teacher_df = create_matrix_df()

                # 第3轮起：销售人数
                if round_num >= 3:
                    st.markdown(f'<div class="matrix-title">{t("sales")}</div>', unsafe_allow_html=True)
                    sales_df = st.data_editor(
                        create_prefilled_matrix(prefill_decisions, company_name, "sales", rule),
                        key=f"sa_{company_name}_r{round_num}",
                        num_rows="fixed",
                        use_container_width=True,
                        column_config={
                            "1V1": st.column_config.NumberColumn(min_value=0, step=1),
                            "Class": st.column_config.NumberColumn(min_value=0, step=1),
                            "APP": st.column_config.NumberColumn(min_value=0, step=1),
                        }
                    )
                else:
                    sales_df = create_matrix_df()

                if rule.enable_pricing:
                    st.markdown(f'<div class="matrix-title">{t("pricing")}</div>', unsafe_allow_html=True)
                    default_prices = [[config.DEFAULT_PRICES[m][p] for p in ["1V1", "Class", "APP"]] for m in ["T1", "T2", "T3"]]
                    pricing_df = st.data_editor(
                        create_prefilled_matrix(prefill_decisions, company_name, "price", rule, default_values=default_prices),
                        key=f"pr_{company_name}_r{round_num}",
                        num_rows="fixed",
                        use_container_width=True,
                        column_config={
                            "1V1": st.column_config.NumberColumn(min_value=0, step=100),
                            "Class": st.column_config.NumberColumn(min_value=0, step=100),
                            "APP": st.column_config.NumberColumn(min_value=0, step=100),
                        }
                    )
                else:
                    pricing_df = create_matrix_df([[config.DEFAULT_PRICES[m][p] for p in ["1V1", "Class", "APP"]] for m in ["T1", "T2", "T3"]])

                # 转换为决策
                decisions = matrix_to_decisions(rd_df, marketing_df, teacher_df, sales_df, pricing_df, rule)
                all_decisions[company_name] = decisions

    # CSV模板下载
    if input_mode == t("csv_upload"):
        st.divider()
        st.markdown(f"### {t('csv_template')}")

        has_pricing = rule.enable_pricing
        has_sales = round_num >= 3

        st.markdown(t("csv_notes"))

        # 生成英文CSV模板
        template = """RD,1V1,Class,APP
T1,0,0,0
T2,0,0,0
T3,0,0,0

Marketing,1V1,Class,APP
T1,0,0,0
T2,0,0,0
T3,0,0,0

Teachers,1V1,Class,APP
T1,0,0,0
T2,0,0,0
T3,0,0,0
"""
        if has_sales:
            template += """
Sales,1V1,Class,APP
T1,0,0,0
T2,0,0,0
T3,0,0,0
"""
        if has_pricing:
            template += """
Price,1V1,Class,APP
T1,3000,1000,150
T2,3000,1000,150
T3,3000,1000,150
"""
        st.download_button(t("download_template"), template, f"decisions_round_{round_num}.csv", "text/csv")

    # 运行按钮
    st.divider()
    cc1, cc2, cc3 = st.columns([1, 2, 1])
    with cc2:
        if st.button(t("run_round").format(round_num), type="primary", use_container_width=True):
            missing = [cn for cn in st.session_state.companies if cn not in all_decisions]
            if missing:
                st.error(f"Missing decisions: {', '.join(missing)}")
            else:
                # 校验总营销投入上限
                cap_wan = config.ROUND_MARKETING_CAP_WAN.get(round_num)
                if cap_wan:
                    over_limit = []
                    for cn, decisions in all_decisions.items():
                        total_mk = sum(d.get("marketing", 0) for d in decisions.values()) / 10000
                        if total_mk > cap_wan:
                            over_limit.append(f"{cn}: {total_mk:.0f} / cap {cap_wan}")
                    if over_limit:
                        st.error("⚠️ " + t("mk_over") + "\n" + "\n".join(over_limit))
                        st.stop()

                with st.spinner("Running..."):
                    # 1. 保存本轮开始前的快照（用于后续可能的重跑）
                    save_pre_round_snapshot(
                        round_num=round_num,
                        game_state=state,
                        input_decisions=all_decisions,
                        round_results=dict(st.session_state.round_results),
                    )
                    
                    # 2. 运行引擎
                    engine = GameEngine(state)
                    results = engine.run_round(all_decisions, round_num)
                    # 保存输入决策到结果中
                    results["input_decisions"] = all_decisions
                    st.session_state.round_results[round_num] = results
                    st.session_state.current_round = round_num
                    # 清除重跑标记（如果本次是重跑后的重新运行）
                    if hasattr(st.session_state, 'rerun_round'):
                        del st.session_state.rerun_round
                    if hasattr(st.session_state, 'rerun_input_decisions'):
                        del st.session_state.rerun_input_decisions
                    os.makedirs("data/results", exist_ok=True)
                    save_round_results(results)
                    st.rerun()

    # 显示本轮结果
    cr = st.session_state.current_round
    if cr > 0 and cr in st.session_state.round_results:
        show_round_results(st.session_state.round_results[cr])


# =============================================================================
# 主逻辑
# =============================================================================

# 语言选择放在最顶部
lang_cols = st.columns([6, 1])
with lang_cols[1]:
    selected_lang = st.selectbox(t("language"), ["中文", "English"], index=0 if lang == "zh" else 1, label_visibility="collapsed")
    new_lang = "zh" if selected_lang == "中文" else "en"
    if new_lang != lang:
        st.session_state.lang = new_lang
        st.rerun()

# 初始化状态
init_state()
lang = st.session_state.lang

# ============== 侧边栏 ==============
with st.sidebar:
    st.markdown(f"## {t('control_panel')}")

    # 语言切换
    sidebar_lang = st.selectbox(t("language"), ["中文", "English"], index=0 if lang == "zh" else 1)
    new_sidebar_lang = "zh" if sidebar_lang == "中文" else "en"
    if new_sidebar_lang != lang:
        st.session_state.lang = new_sidebar_lang
        st.rerun()

    if not st.session_state.initialized:
        st.markdown(f"### {t('create_game')}")
        num = st.number_input(t("player_count"), 2, 6, 2)
        names = []
        cols = st.columns(2)
        for i in range(num):
            with cols[i % 2]:
                default_name = f"Company {chr(65+i)}" if lang == "en" else f"公司{chr(65+i)}"
                names.append(st.text_input(f"{t('player_name')} {i+1}", value=default_name, key=f"c{i}"))
        if st.button(t("create_btn"), type="primary"):
            state = GameState()
            for n in names:
                state.add_company(n)
            st.session_state.game_state = state
            st.session_state.companies = names
            st.session_state.initialized = True
            st.session_state.current_round = 0
            st.session_state.round_results = {}
            st.rerun()
    else:
        st.success(f"✅ {t('current_round')}: {st.session_state.current_round} / {config.TOTAL_ROUNDS}")
        if st.session_state.current_round > 0:
            r = get_round_rule(st.session_state.current_round)
            st.markdown(f"**{t('current_round')}**: {r.name}")
        st.markdown(f"**{t('players')}**: {', '.join(st.session_state.companies)}")
        st.divider()
        with st.expander(t("full_rules")):
            st.markdown(get_all_rules_summary())
        if st.button(t("restart")):
            for k in ['game_state','current_round','round_results','initialized']:
                if k in st.session_state:
                    del st.session_state[k]
            init_state()
            st.rerun()

# ============== 主页面 ==============
st.markdown(f'<div class="main-header">{t("title")}</div>', unsafe_allow_html=True)

if not st.session_state.initialized:
    st.info(t("welcome"))
    c1, c2, c3 = st.columns(3)
    c1.metric(t("players"), t("players_range"))
    c2.metric(t("rounds"), "5")
    c3.metric(t("initial_cash"), t("initial_cash"))
else:
    state = st.session_state.game_state
    cr = st.session_state.current_round

    if cr >= config.TOTAL_ROUNDS:
        show_final_results()
    else:
        show_round_play()
