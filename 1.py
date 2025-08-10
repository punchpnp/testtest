import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
from datetime import datetime

# =============================
# App Config
# =============================
st.set_page_config(
    page_title="AI Agent • Company Compare",
    page_icon="🤖",
    layout="wide",
)

# =============================
# Helpers & Mock Data
# =============================
@st.cache_data(show_spinner=False)
def generate_mock(company_names, start_year=2019, end_year=datetime.now().year):
    rng = np.random.default_rng(7)
    years = list(range(start_year, end_year + 1))
    rows = []
    for co in company_names:
        base = rng.uniform(8_000, 60_000)  # revenue in millions
        growth = rng.normal(0.08, 0.04)
        margin = rng.uniform(0.06, 0.24)
        rev = base
        for y in years:
            rev = max(500, rev * (1 + growth + rng.normal(0, 0.06)))
            cogs = rev * rng.uniform(0.5, 0.75)
            opex = rev * rng.uniform(0.15, 0.35)
            gross = rev - cogs
            ebit = gross - opex
            net = max(0, ebit - 0.02 * rev) * (1 - 0.2)
            # blend to desired margin a bit
            net = 0.5 * net + 0.5 * margin * rev
            mc = rev * rng.uniform(2.2, 4.8)
            rows.append({
                "Company": co,
                "Year": y,
                "Revenue (M)": round(rev, 2),
                "Gross Profit (M)": round(gross, 2),
                "Opex (M)": round(opex, 2),
                "Net Profit (M)": round(net, 2),
                "Net Margin": round(net / rev, 4),
                "Market Cap (M)": round(mc, 2),
            })
    return pd.DataFrame(rows)

# Placeholder for real-world data hook
# Return a dataframe with the same schema as generate_mock() or None if not available
@st.cache_data(show_spinner=True)
def fetch_real_financials(companies: list, start_year: int, end_year: int):
    # TODO: Replace with actual API/database connector (e.g., FinancialModelingPrep, Alpha Vantage, custom DB)
    # Keep the same columns as mock for drop-in replacement
    return None

# ===============
# Agent System
# ===============
class AgentResult:
    def __init__(self, title: str, content: str, data: dict | None = None):
        self.title = title
        self.content = content
        self.data = data or {}

class BaseAgent:
    name = "Agent"
    role = ""
    def run(self, df: pd.DataFrame) -> AgentResult:
        raise NotImplementedError

class DataCatalogAgent(BaseAgent):
    name = "Data Catalog Specialist"
    role = "Describes the dataset and fields."
    def run(self, df: pd.DataFrame) -> AgentResult:
        schema = {
            "Company": "Company name",
            "Year": "Fiscal year",
            "Revenue (M)": "Revenue in millions",
            "Gross Profit (M)": "Gross profit in millions",
            "Opex (M)": "Operating expenses in millions",
            "Net Profit (M)": "Net profit in millions",
            "Net Margin": "Net profit / Revenue",
            "Market Cap (M)": "Market capitalization (proxy) in millions",
        }
        cols = [f"• **{k}** — {v}" for k, v in schema.items() if k in df.columns]
        text = ".join(cols)"
        return AgentResult("Data Catalog", text, {"schema": schema})

class DataInsightAgent(BaseAgent):
    name = "Data Insight"
    role = "Surfaces quick insights and growth."
    def run(self, df: pd.DataFrame) -> AgentResult:
        yrs = sorted(df["Year"].unique())
        latest = yrs[-1]
        scope = df[df["Year"] == latest]
        # Leaders
        lead_rev = scope.loc[scope["Revenue (M)"].idxmax()][["Company", "Revenue (M)"]]
        lead_net = scope.loc[scope["Net Profit (M)"].idxmax()][["Company", "Net Profit (M)"]]
        # CAGR
        def cagr(series):
            if len(series) < 2:
                return np.nan
            start, end = series.iloc[0], series.iloc[-1]
            n = len(series) - 1
            if start <= 0 or end <= 0:
                return np.nan
            return (end / start) ** (1 / n) - 1
        pivot_rev = df.pivot_table(index="Company", columns="Year", values="Revenue (M)")
        pivot_net = df.pivot_table(index="Company", columns="Year", values="Net Profit (M)")
        cagr_rev = pivot_rev.apply(cagr, axis=1).sort_values(ascending=False)
        cagr_net = pivot_net.apply(cagr, axis=1).sort_values(ascending=False)
        msg = (
            f"Latest year: **{latest}**"
            f"• Revenue leader: **{lead_rev['Company']}** — {lead_rev['Revenue (M)']:.0f} M"
            f"• Net profit leader: **{lead_net['Company']}** — {lead_net['Net Profit (M)']:.0f} M"
            f"• Fastest revenue CAGR: **{cagr_rev.index[0]}** — {cagr_rev.iloc[0]*100:.1f}%/yr"
            f"• Fastest net profit CAGR: **{cagr_net.index[0]}** — {cagr_net.iloc[0]*100:.1f}%/yr"
        )
        return AgentResult("Key Insights", msg, {
            "latest": int(latest),
            "revenue_leader": lead_rev.to_dict(),
            "net_leader": lead_net.to_dict(),
            "cagr_rev": cagr_rev.to_dict(),
            "cagr_net": cagr_net.to_dict(),
        })

class FinancialAnalysisAgent(BaseAgent):
    name = "Financial Analyst"
    role = "Analyzes margins, efficiency, and consistency."
    def run(self, df: pd.DataFrame) -> AgentResult:
        g = df.groupby("Company").agg(
            avg_margin=("Net Margin", "mean"),
            margin_vol=("Net Margin", "std"),
            avg_opex_ratio=("Opex (M)", lambda s: (s / df.loc[s.index, "Revenue (M)"]).mean()),
        ).reset_index()
        g["score_profitability"] = (g["avg_margin"] - g["margin_vol"].fillna(0)).rank(ascending=False)
        top = g.sort_values(["score_profitability", "avg_margin"], ascending=[True, False]).iloc[0]
        msg = (
            f"Avg net margin (best): **{top['Company']}** — {top['avg_margin']*100:.1f}%"
            f"Opex ratio (mean): {top['avg_opex_ratio']*100:.1f}%"
            f"Margin volatility (stdev): {(top['margin_vol'] or 0)*100:.1f}%"
        )
        return AgentResult("Financial Analysis", msg, {"table": g.to_dict(orient="records")})

class TranslatorAgent(BaseAgent):
    name = "Translator"
    role = "Summarizes results in English/Thai."
    def __init__(self, language: str = "en"):
        self.language = language
    def run(self, df: pd.DataFrame, summaries: list[str] | None = None) -> AgentResult:
        text = ".join(summaries or [])"
        if self.language == "th":
            text_th = (
                "สรุปผลการเปรียบเทียบ (เดโม):" +
                text
                .replace("Latest year:", "ปีล่าสุด:")
                .replace("Revenue leader:", "รายได้สูงสุด:")
                .replace("Net profit leader:", "กำไรสุทธิสูงสุด:")
                .replace("Fastest revenue CAGR:", "อัตราเติบโตเฉลี่ยรายได้ (CAGR) สูงสุด:")
                .replace("Fastest net profit CAGR:", "อัตราเติบโตเฉลี่ยกำไรสุทธิ (CAGR) สูงสุด:")
                .replace("Avg net margin (best):", "อัตรากำไรสุทธิเฉลี่ย (ดีที่สุด):")
                .replace("Opex ratio (mean):", "สัดส่วนค่าใช้จ่ายในการดำเนินงานเฉลี่ย:")
                .replace("Margin volatility (stdev):", "ความผันผวนของมาร์จิ้น (ส่วนเบี่ยงเบนมาตรฐาน):")
            )
            return AgentResult("Translator (TH)", text_th)
        else:
            return AgentResult("Translator (EN)", text)

# Registry for future extensibility
AGENT_REGISTRY = {
    "catalog": DataCatalogAgent(),
    "insight": DataInsightAgent(),
    "fin": FinancialAnalysisAgent(),
}

# =============================
# State & Flow helpers
# =============================
def reset_flow():
    st.session_state.stage = "input"
    st.session_state.chat = []
    st.session_state.result_df = None
    st.session_state.agent_summaries = []


def ensure_keys():
    # Ensure widget-backed keys exist even after reruns/reloads
    st.session_state.setdefault("co1", "Centara")
    st.session_state.setdefault("co2", "Iberry")


if "stage" not in st.session_state:
    reset_flow()
# Always ensure company keys exist before any access
ensure_keys()

# =============================
# Header
# =============================
st.title("🤖 AI Agent • Company Compare Dashboard")
st.caption("Enter two companies → Compare → Watch multi‑agent analysis run → See charts & summaries (mock data, real‑data hook ready).")

# =============================
# Sidebar • Settings
# =============================
st.sidebar.header("Settings")
lang = st.sidebar.selectbox("Summary language", ["en", "th"], index=0)
use_real = st.sidebar.toggle("Use real data (if connector implemented)", value=False, help="If enabled and a connector is implemented, the app will fetch real data; otherwise mock data is used.")
start_year_sb, end_year_sb = st.sidebar.select_slider(
    "Default year range",
    options=list(range(2016, datetime.now().year + 1)),
    value=(2019, datetime.now().year),
)

# =============================
# Stage: Input Canvas
# =============================
if st.session_state.stage == "input":
    with st.container(border=True):
        st.subheader("Canvas • Choose Companies")
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            company_1 = st.text_input("Company 1", value=st.session_state.co1, key="co1")
        with c2:
            company_2 = st.text_input("Company 2", value=st.session_state.co2, key="co2")
        with c3:
            st.write("")
            st.write("")
            compare_clicked = st.button("Compare", type="primary")

    if compare_clicked:
        co1 = st.session_state.get("co1", "").strip()
        co2 = st.session_state.get("co2", "").strip()
        if not co1 or not co2:
            st.error("Please enter both company names.")
        else:
            st.session_state.stage = "running"
            st.rerun()

# =============================
# Stage: Agent Running (animated + multi‑agent)
# =============================
if st.session_state.stage == "running":
    placeholder = st.empty()

    co1 = st.session_state.get("co1", "Company 1")
    co2 = st.session_state.get("co2", "Company 2")

    with placeholder.container():
        st.subheader("AI Agent • Processing…")
        st.chat_message("assistant").write(f"Okay! I'll compare **{co1}** and **{co2}** using a team of agents.")
        status = st.status("Thinking…", expanded=True)
        with status:
            st.write("🔎 Interpreting your request")
            time.sleep(0.4)
            st.write("🔌 Choosing data source (real vs mock)")
            time.sleep(0.4)
        status.update(label="Fetching data…")

    # fetch data (real or mock)
    df_real = None
    if use_real:
        df_real = fetch_real_financials([co1, co2], start_year_sb, end_year_sb)
    df = df_real if df_real is not None else generate_mock([co1, co2], start_year_sb, end_year_sb)

    # Run agents sequentially and show a live log
    with placeholder.container():
        status2 = st.status("Running multi‑agent analysis…", expanded=True)
        with status2:
            # Data Catalog
            st.write("📚 **Data Catalog Specialist** is documenting fields…")
            cat = AGENT_REGISTRY["catalog"].run(df)
            st.chat_message("assistant").markdown(cat.content)
            time.sleep(0.4)

            # Insights
            st.write("💡 **Data Insight Agent** is extracting trends…")
            ins = AGENT_REGISTRY["insight"].run(df)
            st.chat_message("assistant").markdown(ins.content)
            time.sleep(0.4)

            # Financial Analysis
            st.write("📈 **Financial Analyst** is evaluating margins & efficiency…")
            fin = AGENT_REGISTRY["fin"].run(df)
            st.chat_message("assistant").markdown(fin.content)
            time.sleep(0.4)

            # Translator
            st.write("🌐 **Translator** is preparing the summary…")
            tr = TranslatorAgent(language=lang).run(df, [ins.content, fin.content])
            st.chat_message("assistant").markdown(tr.content)

        status2.update(label="Done", state="complete")

    # Save state for results page
    st.session_state.result_df = df
    st.session_state.agent_summaries = [cat.content, ins.content, fin.content, tr.content]
    st.session_state.stage = "done"
    time.sleep(0.2)
    st.rerun()

# =============================
# Stage: Results
# =============================
if st.session_state.stage == "done":
    df = st.session_state.result_df.copy()
    co1 = st.session_state.get("co1", "Company 1")
    co2 = st.session_state.get("co2", "Company 2")

    st.chat_message("assistant").write(
        f"Here are the comparison results for **{co1}** vs **{co2}**. You can adjust the year range below and review the charts and tables."
    )

    # Controls
    yrs = sorted(df["Year"].unique())
    start_year, end_year = st.select_slider(
        "Year range",
        options=yrs,
        value=(yrs[0], yrs[-1]),
        key="year_range",
    )
    scope = df[(df["Year"] >= start_year) & (df["Year"] <= end_year)]
    latest_year = scope["Year"].max()

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    latest = scope[scope["Year"] == latest_year]
    with k1:
        st.metric("Latest Year", int(latest_year))
    with k2:
        st.metric("Total Revenue (M)", f"{latest['Revenue (M)'].sum():,.0f}")
    with k3:
        st.metric("Total Net Profit (M)", f"{latest['Net Profit (M)'].sum():,.0f}")
    with k4:
        lead = latest.sort_values("Net Profit (M)", ascending=False).iloc[0]
        st.metric("Leader (Net Profit)", f"{lead['Company']}", f"{lead['Net Profit (M)']:,.0f}")

    st.divider()

    # Row 1: Trends
    t1, t2 = st.columns([3, 2])
    with t1:
        fig = px.line(
            scope,
            x="Year",
            y="Net Profit (M)",
            color="Company",
            markers=True,
            title="Net Profit Over Time",
        )
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        fig2 = px.line(
            scope,
            x="Year",
            y="Revenue (M)",
            color="Company",
            markers=True,
            title="Revenue Over Time",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2: Latest year head‑to‑head
    st.subheader(f"Head‑to‑Head • {latest_year}")
    ly = scope[scope["Year"] == latest_year]
    c1, c2 = st.columns(2)
    with c1:
        fig_bar = px.bar(
            ly, x="Company", y=["Revenue (M)", "Net Profit (M)"], barmode="group", text_auto=".2s",
            title="Revenue vs Net Profit (Latest Year)")
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        fig_scatter = px.scatter(
            ly,
            x="Revenue (M)", y="Net Margin", color="Company", size="Market Cap (M)",
            hover_data=["Net Profit (M)"], title="Positioning: Revenue vs Net Margin")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Data table
    with st.expander("Show data table"):
        st.dataframe(scope.sort_values(["Year", "Company"]).reset_index(drop=True), use_container_width=True, hide_index=True)

    st.divider()

    # Agent recap
    with st.expander("Agent summaries"):
        for s in st.session_state.agent_summaries:
            st.markdown(s)

    cA, cB = st.columns([1, 1])
    with cA:
        if st.button("← Start over", use_container_width=True):
            reset_flow()
            st.rerun()
    with cB:
        st.caption("Mock or real data • Plug in your API in `fetch_real_financials()`.")
