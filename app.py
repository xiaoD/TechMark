"""
TechMark 教育沙盘模拟 - Streamlit Web界面 (支持中英文 + 分布式提交)
启动: streamlit run app.py

URL 参数:
  ?company=A     -> 玩家模式（A公司决策提交页面）
  ?admin=1       -> 主持人模式（总控页面）
  无参数         -> 选择页面（选择公司或主持人）
"""
import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path
import matplotlib.pyplot as plt

from models import GameState
from game_engine import GameEngine
from round_rules import get_round_rule, get_all_rules_summary
from csv_handler import save_round_results, save_final_ranking
from snapshot_manager import (
    save_pre_round_snapshot, load_pre_round_snapshot,
    has_snapshot, delete_snapshot, delete_all_snapshots,
)
from submission_manager import (
    save_submission, load_submission, list_submissions,
    get_all_submissions, save_results_to_file, load_results_from_file,
    get_latest_completed_round, load_all_results,
    clear_submission, clear_all_submissions,
)
from i18n import get_text
import config

st.set_page_config(page_title="PalFish Business MindSet", page_icon="🎮", layout="wide")

# ============== 样式 ==============
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: bold; color: #1f77b4; text-align: center; }
    .round-title { font-size: 1.6rem; font-weight: bold; color: #ff7f0e; margin: 0.5rem 0; }
    .matrix-title { font-size: 1.1rem; font-weight: bold; color: #333; margin: 1rem 0 0.3rem 0; }
    .info-box { background-color: #f0f2f6; padding: 1rem; border-radius: 10px; }
    .submitted-badge { background-color: #d4edda; color: #155724; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; }
    .pending-badge { background-color: #f8d7da; color: #721c24; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; }
    .link-box { background-color: #e8f4f8; padding: 8px 12px; border-radius: 6px; font-family: monospace; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 游戏配置管理（持久化到文件，供所有会话共享）
# =============================================================================
GAME_CONFIG_PATH = Path("data/game_config.json")

def load_game_config() -> dict:
    """从文件加载游戏配置"""
    if not GAME_CONFIG_PATH.exists():
        return None
    with open(GAME_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_game_config(companies: list, current_round: int = 0):
    """保存游戏配置到文件"""
    GAME_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "companies": companies,
        "current_round": current_round,
        "created_at": pd.Timestamp.now().isoformat(),
    }
    with open(GAME_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def reset_game():
    """重置游戏（删除所有配置、提交、结果）"""
    if GAME_CONFIG_PATH.exists():
        GAME_CONFIG_PATH.unlink()
    clear_all_submissions()
    for f in Path("data/results").glob("*.json"):
        f.unlink()
    for f in Path("data/saves/snapshots").glob("*.json"):
        f.unlink()


def get_base_url():
    """获取当前页面的基础URL（用于生成链接）"""
    # Streamlit 不直接提供完整URL，使用相对路径
    return ""


# =============================================================================
# 状态初始化
# =============================================================================
def init_state():
    if 'lang' not in st.session_state:
        st.session_state.lang = "en"

init_state()


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
    return get_text(key, st.session_state.lang)


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

            if first_col in ['t1', 't2', 't3'] and current_matrix and row_idx < 3:
                vals = []
                for j in range(1, min(4, len(line))):
                    try:
                        v = float(line[j]) if line[j] != '' and str(line[j]) != 'nan' else 0
                        vals.append(v)
                    except:
                        vals.append(0)
                while len(vals) < 3:
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
                    dec["teachers"] = int(teacher_matrix[i][j])
                if round_rule.round_num >= 3:
                    dec["sales"] = int(sales_matrix[i][j])
                if round_rule.enable_pricing:
                    dec["price"] = pricing_matrix[i][j]
                elif round_rule.use_default_prices:
                    dec["price"] = config.DEFAULT_PRICES[market][ptype]
                decisions[pid] = dec

        return decisions
    except Exception as e:
        st.error(f"Error parsing CSV: {e}")
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
                # APP 产品不需要教师
                if ptype == "APP":
                    dec["teachers"] = 0
                else:
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
            # APP 产品不需要教师
            if var_name == "teachers" and ptype == "APP":
                val = 0
            row.append(val)
        values.append(row)
    return pd.DataFrame(values, index=markets, columns=products)


# =============================================================================
# 显示结果函数
# =============================================================================
def show_final_results():
    st.markdown(f'<div class="round-title">{t("game_over")}</div>', unsafe_allow_html=True)
    
    # 从文件加载 game_state 来计算最终排名
    config_data = load_game_config()
    if not config_data:
        st.error(t("game_not_created"))
        return
    
    state = GameState()
    for name in config_data["companies"]:
        state.add_company(name)
    
    # 重放所有轮次来恢复最终状态
    latest_round = get_latest_completed_round()
    for rn in range(1, latest_round + 1):
        all_decisions = get_all_submissions(rn, config_data["companies"])
        if all_decisions and len(all_decisions) == len(config_data["companies"]):
            engine = GameEngine(state)
            engine.run_round(all_decisions, rn)
    
    engine = GameEngine(state)
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
    st.balloons()

    # 历史趋势
    st.markdown("---")
    st.markdown(f"### {t('history')}")
    hist = []
    all_results = load_all_results(latest_round)
    for rn, res in all_results.items():
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


def show_round_results(res, view_company=None):
    """
    显示轮次结果
    view_company: 如果指定，则只显示该公司的详细数据（玩家模式）；
                  为 None 时显示所有公司数据（admin 模式）
    """
    st.divider()
    current_r = res.get("round", 0)
    st.markdown(f"### {t('result_summary').format(current_r, '')}")

    companies = list(res["companies"].keys())
    is_player_view = view_company is not None

    # 市场概览
    st.markdown(f"#### {t('market_overview')}")
    mc = st.columns(len(companies) + 1)
    with mc[0]:
        st.markdown(f"<div style='text-align:center'><b>{t('market')}</b></div>", unsafe_allow_html=True)
        for m, total in res["market_totals"].items():
            cap = config.MARKET_CAPACITY[m]
            pct = total / cap * 100
            st.markdown(f"<div style='text-align:center'>{m}: {total:,}/{cap:,} ({pct:.1f}%)</div>", unsafe_allow_html=True)

    for i, cn in enumerate(companies):
        with mc[i + 1]:
            d = res["companies"][cn]
            st.markdown(f"<div style='text-align:center'><b>{cn}</b></div>", unsafe_allow_html=True)
            if is_player_view and cn != view_company:
                # 玩家模式下，其他公司只显示占位符，隐藏真实财务数据
                st.markdown(f"<div style='text-align:center'>💰 ---</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center'>📈 ---</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center'>💰 {d['cash']:,.0f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center'>📈 {d['net_profit']:,.0f}</div>", unsafe_allow_html=True)

    # 图表区域：营收 + 净利润 + 净资产
    st.markdown("---")
    chart_cols = st.columns(3)
    company_list = list(res["companies"].keys())

    def _draw_bar_chart(ax, values, ylabel, title_color):
        if is_player_view:
            colors = ['#1f77b4' if cn == view_company else '#d3d3d3' for cn in company_list]
        else:
            colors = ['#1f77b4'] * len(company_list)
        bars = ax.bar(company_list, values, color=colors, edgecolor='white', linewidth=0.5)
        ax.set_ylabel(ylabel)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        for bar, cn in zip(bars, company_list):
            h = bar.get_height()
            label = f'{h:.1f}' if (not is_player_view or cn == view_company) else '---'
            color = 'black' if (not is_player_view or cn == view_company) else 'gray'
            ax.text(bar.get_x() + bar.get_width() / 2., h, label,
                    ha='center', va='bottom', fontsize=7, color=color, fontweight='bold')
        plt.setp(ax.get_xticklabels(), rotation=20, ha='right', fontsize=8)

    with chart_cols[0]:
        st.markdown("**📊 Revenue (10K)**")
        fig1, ax1 = plt.subplots(figsize=(3.8, 3.2))
        revenues = [res["companies"][cn]["total_revenue"] / 10000 for cn in company_list]
        _draw_bar_chart(ax1, revenues, "Revenue (10K)", "#1f77b4")
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    with chart_cols[1]:
        st.markdown("**📈 Net Profit (10K)**")
        fig2, ax2 = plt.subplots(figsize=(3.8, 3.2))
        profits = [res["companies"][cn]["net_profit"] / 10000 for cn in company_list]
        _draw_bar_chart(ax2, profits, "Profit (10K)", "#2ca02c")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    with chart_cols[2]:
        st.markdown("**💰 Net Worth (10K)**")
        fig3, ax3 = plt.subplots(figsize=(3.8, 3.2))
        net_worths = [(res["companies"][cn]["cash"] - res["companies"][cn]["debt"]) / 10000 for cn in company_list]
        _draw_bar_chart(ax3, net_worths, "Net Worth (10K)", "#ff7f0e")
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

    # 公开信息（市场情报）—— 所有玩家都能看到
    st.markdown("---")
    st.markdown(f"#### {t('public_info')}")
    
    public_data = []
    for pid in config.ALL_PRODUCTS:
        row = {"Product": pid}
        for cn in companies:
            p = res["companies"][cn]["products"][pid]
            row[f"{cn}"] = f"{p['students']} / {p['price']:,.0f}"
        public_data.append(row)
    
    pub_df = pd.DataFrame(public_data)
    st.dataframe(pub_df, hide_index=True, use_container_width=True)

    # 品牌排名 —— 公开信息
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

    # 产品明细 —— 玩家模式下只显示自己的，admin 显示全部
    st.markdown("---")
    st.markdown(f"#### {t('product_detail')}")

    for cn in companies:
        # 玩家模式下跳过其他公司
        if is_player_view and cn != view_company:
            continue

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
            
            # 税收指标（兼容旧结果文件）
            t1, t2, t3, t4 = st.columns(4)
            t1.metric(t("vat_tax"), f"{d.get('vat_tax', 0):,.0f}")
            t2.metric(t("income_tax"), f"{d.get('income_tax', 0):,.0f}")
            t3.metric(t("total_tax"), f"{d.get('total_tax', 0):,.0f}")
            t4.metric(t("net_profit"), f"{d['net_profit']:,.0f}")
            
            # ====== 简短总结 ======
            st.markdown("**📝 Summary**")
            summary = generate_summary(cn, d, res, input_data if 'input_data' in dir() else [])
            st.info(summary)
    
# =============================================================================
# 单公司决策输入组件（供玩家页面和主持人页面共用）
# =============================================================================
def render_company_input(company_name, state, rule, round_num, prefill_decisions=None, is_admin=False):
    """
    渲染单个公司的决策输入界面
    返回: (decisions_dict, submitted)
    """
    company = state.companies[company_name]
    
    with st.expander(f"🏢 {company_name}", expanded=True):
        # 公司状态
        c1, c2, c3 = st.columns(3)
        c1.metric(t("cash"), f"{company.cash:,.0f}")
        c2.metric(t("debt"), f"{company.debt:,.0f}")
        c3.metric(t("net_worth"), f"{company.cash - company.debt:,.0f}")

        # 两种输入方式
        input_mode = st.radio(t("input_method"), [t("matrix_input"), t("csv_upload")], horizontal=True, key=f"input_mode_{company_name}_r{round_num}")

        if input_mode == t("csv_upload"):
            uploaded = st.file_uploader(f"Upload {company_name} CSV", type=['csv'], key=f"up_{company_name}_r{round_num}")
            if uploaded:
                decisions = parse_uploaded_file(uploaded, rule)
                if decisions:
                    st.success(f"✅ Parsed {company_name} CSV")
                    preview = []
                    for pid, dec in decisions.items():
                        preview.append({"Product": pid, **dec})
                    st.dataframe(pd.DataFrame(preview), hide_index=True)
                    return decisions, True
            return None, False
        else:
            # 矩阵表格填写模式
            if rule.enable_rd:
                st.markdown(f'<div class="matrix-title">{t("rd_cost")}</div>', unsafe_allow_html=True)
                rd_df = st.data_editor(
                    create_prefilled_matrix(prefill_decisions, company_name, "rd", rule),
                    key=f"rd_{company_name}_r{round_num}",
                    num_rows="fixed", use_container_width=True,
                    column_config={"1V1": st.column_config.NumberColumn(min_value=0, step=1), "Class": st.column_config.NumberColumn(min_value=0, step=1), "APP": st.column_config.NumberColumn(min_value=0, step=1)}
                )
            else:
                rd_df = create_matrix_df()

            if rule.enable_marketing:
                st.markdown(f'<div class="matrix-title">{t("marketing_cost")}</div>', unsafe_allow_html=True)
                marketing_df = st.data_editor(
                    create_prefilled_matrix(prefill_decisions, company_name, "marketing", rule),
                    key=f"mk_{company_name}_r{round_num}",
                    num_rows="fixed", use_container_width=True,
                    column_config={"1V1": st.column_config.NumberColumn(min_value=0, step=1), "Class": st.column_config.NumberColumn(min_value=0, step=1), "APP": st.column_config.NumberColumn(min_value=0, step=1)}
                )
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
                # APP 产品不需要教师，强制为 0
                teacher_prefill = create_prefilled_matrix(prefill_decisions, company_name, "teachers", rule)
                teacher_prefill["APP"] = 0
                teacher_df = st.data_editor(
                    teacher_prefill,
                    key=f"th_{company_name}_r{round_num}",
                    num_rows="fixed", use_container_width=True,
                    column_config={
                        "1V1": st.column_config.NumberColumn(min_value=0, step=1),
                        "Class": st.column_config.NumberColumn(min_value=0, step=1),
                        "APP": st.column_config.NumberColumn(min_value=0, step=1, disabled=True),
                    }
                )
            else:
                teacher_df = create_matrix_df()

            if round_num >= 3:
                st.markdown(f'<div class="matrix-title">{t("sales")}</div>', unsafe_allow_html=True)
                sales_df = st.data_editor(
                    create_prefilled_matrix(prefill_decisions, company_name, "sales", rule),
                    key=f"sa_{company_name}_r{round_num}",
                    num_rows="fixed", use_container_width=True,
                    column_config={"1V1": st.column_config.NumberColumn(min_value=0, step=1), "Class": st.column_config.NumberColumn(min_value=0, step=1), "APP": st.column_config.NumberColumn(min_value=0, step=1)}
                )
            else:
                sales_df = create_matrix_df()

            if rule.enable_pricing:
                st.markdown(f'<div class="matrix-title">{t("pricing")}</div>', unsafe_allow_html=True)
                default_prices = [[config.DEFAULT_PRICES[m][p] for p in ["1V1", "Class", "APP"]] for m in ["T1", "T2", "T3"]]
                pricing_df = st.data_editor(
                    create_prefilled_matrix(prefill_decisions, company_name, "price", rule, default_values=default_prices),
                    key=f"pr_{company_name}_r{round_num}",
                    num_rows="fixed", use_container_width=True,
                    column_config={"1V1": st.column_config.NumberColumn(min_value=0, step=100), "Class": st.column_config.NumberColumn(min_value=0, step=100), "APP": st.column_config.NumberColumn(min_value=0, step=100)}
                )
            else:
                pricing_df = create_matrix_df([[config.DEFAULT_PRICES[m][p] for p in ["1V1", "Class", "APP"]] for m in ["T1", "T2", "T3"]])

            decisions = matrix_to_decisions(rd_df, marketing_df, teacher_df, sales_df, pricing_df, rule)
            return decisions, True


# =============================================================================
# 玩家页面（单公司提交）
# =============================================================================
def show_player_page(company_name: str):
    """显示单个公司的决策提交页面"""
    st.markdown(f'<div class="main-header">{t("title")}</div>', unsafe_allow_html=True)
    
    config_data = load_game_config()
    if not config_data:
        st.error(t("game_not_created"))
        st.info(t("create_game_first"))
        return
    
    if company_name not in config_data["companies"]:
        st.error(f"Company '{company_name}' not found in game.")
        return
    
    # 从文件读取最新结果来确定当前轮次
    latest_completed = get_latest_completed_round()
    current_round = latest_completed
    next_round = current_round + 1
    
    if next_round > config.TOTAL_ROUNDS:
        st.success("🎉 游戏已结束！")
        # 显示最终结果（玩家只能看到自己的数据）
        all_results = load_all_results(current_round)
        if all_results:
            show_round_results(all_results[current_round], view_company=company_name)
        return
    
    rule = get_round_rule(next_round)
    
    st.markdown(f'<div class="round-title">{t("company_page_title").format(company_name, next_round)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box">{rule.description}</div>', unsafe_allow_html=True)
    
    # 检查是否已提交
    existing = load_submission(next_round, company_name)
    if existing:
        st.success(f"✅ {t('submitted_wait')}")
        st.caption(f"{t('submitted_at')}: {existing.get('submitted_at', '')}")
        
        # 显示上次提交的内容（只读）
        with st.expander("📋 查看已提交的决策"):
            preview = []
            for pid, dec in existing["decisions"].items():
                row = {"Product": pid}
                if "rd" in dec:
                    row["R&D(万)"] = f"{dec['rd']/10000:.1f}"
                if "teachers" in dec:
                    row["教师"] = dec["teachers"]
                if "sales" in dec:
                    row["销售"] = dec["sales"]
                if "marketing" in dec:
                    row["营销(万)"] = f"{dec['marketing']/10000:.1f}"
                if "price" in dec:
                    row["定价"] = f"{dec['price']:,.0f}"
                preview.append(row)
            if preview:
                st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)
        
        # 显示本轮结果（如果主持人已运行）
        results = load_results_from_file(next_round)
        if results:
            st.divider()
            st.markdown(f"### 📊 第 {next_round} 轮结果已公布")
            show_round_results(results, view_company=company_name)
        return
    
    # 显示本轮结果（如果主持人已运行但自己还没提交下一轮）
    if current_round > 0:
        results = load_results_from_file(current_round)
        if results:
            with st.expander(f"📊 {t('view_results')} (Round {current_round})"):
                show_round_results(results, view_company=company_name)
    
    # 重建 game_state（用于显示公司当前状态）
    state = GameState()
    for name in config_data["companies"]:
        state.add_company(name)
    
    # 重放历史轮次恢复状态
    for rn in range(1, next_round):
        all_decisions = get_all_submissions(rn, config_data["companies"])
        if all_decisions and len(all_decisions) == len(config_data["companies"]):
            engine = GameEngine(state)
            engine.run_round(all_decisions, rn)
    
    # 决策输入
    decisions, _ = render_company_input(company_name, state, rule, next_round)
    
    # 提交按钮
    st.divider()
    cc1, cc2, cc3 = st.columns([1, 2, 1])
    with cc2:
        if st.button(t("submit_decisions"), type="primary", use_container_width=True):
            # 校验营销上限
            cap_wan = config.ROUND_MARKETING_CAP_WAN.get(next_round)
            if cap_wan:
                total_mk = sum(d.get("marketing", 0) for d in decisions.values()) / 10000
                if total_mk > cap_wan:
                    st.error(f"⚠️ {t('mk_over')}! {t('mk_used')} {total_mk:.0f} / {t('mk_cap')} {cap_wan}")
                    st.stop()
            
            save_submission(next_round, company_name, decisions)
            st.success(f"✅ {company_name} 第 {next_round} 轮决策已提交！")
            st.balloons()
            st.info(t("submitted_wait"))


# =============================================================================
# 主持人页面（总控）
# =============================================================================
def show_admin_page():
    """显示主持人总控页面"""
    st.markdown(f'<div class="main-header">{t("title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="round-title">{t("admin_title")}</div>', unsafe_allow_html=True)
    
    config_data = load_game_config()
    
    # 侧边栏：游戏创建/管理
    with st.sidebar:
        st.markdown(f"## {t('control_panel')}")
        
        if not config_data:
            st.markdown(f"### {t('create_game')}")
            num = st.number_input(t("player_count"), 2, 6, 2)
            names = []
            cols = st.columns(2)
            for i in range(num):
                with cols[i % 2]:
                    default_name = f"Company {chr(65+i)}"
                    names.append(st.text_input(f"{t('player_name')} {i+1}", value=default_name, key=f"admin_c{i}"))
            if st.button(t("create_btn"), type="primary"):
                save_game_config(names, 0)
                st.success("✅ 游戏已创建")
                st.rerun()
        else:
            st.markdown(f"**{t('players')}**: {', '.join(config_data['companies'])}")
            st.markdown(f"**{t('current_round')}**: {config_data['current_round']} / {config.TOTAL_ROUNDS}")
            
            # 生成链接
            st.markdown("---")
            st.markdown(f"### 🔗 {t('player_link')}")
            for name in config_data["companies"]:
                link = f"?company={name}"
                st.markdown(f"<div class='link-box'>{name}: {link}</div>", unsafe_allow_html=True)
            
            st.markdown(f"### 🔗 {t('admin_link')}")
            st.markdown(f"<div class='link-box'>?admin=1</div>", unsafe_allow_html=True)
            
            if st.button(t("restart")):
                reset_game()
                st.success("✅ 游戏已重置")
                st.rerun()
    
    if not config_data:
        st.info(t("create_game_first"))
        return
    
    companies = config_data["companies"]
    latest_completed = get_latest_completed_round()
    current_round = latest_completed
    next_round = current_round + 1
    
    # 显示轮次状态
    st.markdown(f"### {t('round_status').format(next_round)}")
    
    if next_round > config.TOTAL_ROUNDS:
        st.success("🎉 游戏已结束！")
        show_final_results()
        return
    
    rule = get_round_rule(next_round)
    st.markdown(f'<div class="info-box">{rule.description}</div>', unsafe_allow_html=True)
    
    # 提交状态表格
    st.markdown(f"### {t('submission_status')}")
    submissions = list_submissions(next_round, companies)
    
    sub_data = []
    pending_count = 0
    for company, submitted, submitted_at in submissions:
        if submitted:
            sub_data.append({
                "Company": company,
                "Status": f"<span class='submitted-badge'>{t('submitted')}</span>",
                "Time": submitted_at[:19] if submitted_at else "",
            })
        else:
            pending_count += 1
            sub_data.append({
                "Company": company,
                "Status": f"<span class='pending-badge'>{t('not_submitted')}</span>",
                "Time": "",
            })
    
    sub_df = pd.DataFrame(sub_data)
    st.markdown(sub_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # 显示已提交数量
    submitted_count = len(companies) - pending_count
    if pending_count == 0:
        st.success(t("all_submitted"))
    else:
        st.warning(t("waiting_for").format(pending_count))
    
    # 管理员可清除已提交（让玩家重新提交）
    if submitted_count > 0:
        st.markdown("---")
        st.markdown("#### 🗑️ Clear Submissions")
        st.caption("Click to clear a company's submission so they can resubmit.")
        clear_cols = st.columns(min(len(companies), 5))
        for i, (company, submitted, _) in enumerate(submissions):
            if submitted:
                with clear_cols[i % 5]:
                    if st.button(f"🗑️ {company}", key=f"clear_{company}_{next_round}", use_container_width=True):
                        clear_submission(next_round, company)
                        st.success(f"✅ {company}'s submission cleared.")
                        st.rerun()
    
    # 运行按钮
    st.divider()
    can_run = (pending_count == 0)
    
    cc1, cc2, cc3 = st.columns([1, 2, 1])
    with cc2:
        run_btn = st.button(
            t("run_round_admin").format(next_round),
            type="primary",
            use_container_width=True,
            disabled=not can_run
        )
        if run_btn and can_run:
            with st.spinner("Running..."):
                # 重建 game_state
                state = GameState()
                for name in companies:
                    state.add_company(name)
                
                # 重放历史轮次
                for rn in range(1, next_round):
                    hist_decisions = get_all_submissions(rn, companies)
                    if hist_decisions and len(hist_decisions) == len(companies):
                        engine = GameEngine(state)
                        engine.run_round(hist_decisions, rn)
                
                # 获取本轮所有决策
                all_decisions = get_all_submissions(next_round, companies)
                
                # 保存快照
                all_hist_results = load_all_results(current_round)
                save_pre_round_snapshot(
                    round_num=next_round,
                    game_state=state,
                    input_decisions=all_decisions,
                    round_results=all_hist_results,
                )
                
                # 运行引擎
                engine = GameEngine(state)
                results = engine.run_round(all_decisions, next_round)
                results["input_decisions"] = all_decisions
                
                # 保存结果到文件
                save_results_to_file(next_round, results)
                save_round_results(results)
                save_game_config(companies, next_round)
                
                st.success(f"✅ 第 {next_round} 轮运行完成！")
                st.rerun()
    
    # 显示历史结果
    if current_round > 0:
        st.markdown("---")
        st.markdown(f"### 📊 历史结果")
        for rn in range(1, current_round + 1):
            res = load_results_from_file(rn)
            if res:
                with st.expander(f"第 {rn} 轮结果", expanded=(rn == current_round)):
                    show_round_results(res)


# =============================================================================
# 选择页面（无URL参数时显示）
# =============================================================================
def show_landing_page():
    """显示选择页面"""
    st.markdown(f'<div class="main-header">{t("title")}</div>', unsafe_allow_html=True)
    
    config_data = load_game_config()
    
    st.markdown(f"### {t('landing_title')}")
    
    if not config_data:
        st.info("🎮 游戏尚未创建。请访问主持人页面创建游戏。")
        st.markdown("---")
        if st.button("🎙️ " + t("i_am_admin"), type="primary", use_container_width=True):
            st.query_params["admin"] = "1"
            st.rerun()
        return
    
    companies = config_data["companies"]
    latest_completed = get_latest_completed_round()
    next_round = latest_completed + 1
    
    st.info(f"📋 当前游戏: {', '.join(companies)} | 已完成 {latest_completed}/{config.TOTAL_ROUNDS} 轮")
    
    # 公司选择
    st.markdown("---")
    st.markdown("#### 🏢 玩家入口")
    cols = st.columns(min(len(companies), 3))
    for i, company in enumerate(companies):
        with cols[i % 3]:
            # 检查是否已提交
            submitted = load_submission(next_round, company) is not None
            emoji = "✅" if submitted else "📝"
            if st.button(f"{emoji} {t('i_am_company').format(company)}", use_container_width=True):
                st.query_params["company"] = company
                st.rerun()
    
    # 主持人入口
    st.markdown("---")
    st.markdown("#### 🎙️ 主持人入口")
    if st.button(t("i_am_admin"), type="primary", use_container_width=True):
        st.query_params["admin"] = "1"
        st.rerun()


# =============================================================================
# 主逻辑
# =============================================================================
# 语言选择放在最顶部
lang_cols = st.columns([6, 1])
with lang_cols[1]:
    selected_lang = st.selectbox(t("language"), ["中文", "English"], index=0 if st.session_state.lang == "zh" else 1, label_visibility="collapsed")
    new_lang = "zh" if selected_lang == "中文" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

# 读取 URL 参数
query_params = st.query_params
url_company = query_params.get("company", "")
url_admin = query_params.get("admin", "") == "1"

# 路由到对应页面
if url_admin:
    show_admin_page()
elif url_company:
    show_player_page(url_company)
else:
    show_landing_page()
