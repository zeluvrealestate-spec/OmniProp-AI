import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px
import plotly.io as pio

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(page_title="Zeluv.io", page_icon="🏢", layout="wide")

LOGO_URL = "https://z-cdn-media.chatglm.cn/files/ddb3a8de-d171-47f6-8d86-5c827f6ca5a5.png?auth_key=1886107572-89f8ef77610746cdb1d35b0f0c9c94b3-0-ae7928019b3f9fc4512fcb26fdee9a29"

# Read the URL securely from Streamlit Cloud
REDIS_URL = st.secrets["REDIS_URL"]

# ==========================================
# THEME / STYLING
# ==========================================
ACCENT = "#D4AF37"      # muted gold accent
BG_MAIN = "#0B0E11"     # near-black background
BG_PANEL = "#14181D"    # panel/card background
BORDER = "#242A31"
TEXT_PRIMARY = "#F2F2F2"
TEXT_MUTED = "#9AA3AC"

st.markdown(f"""
<style>
    .stApp {{
        background-color: {BG_MAIN};
        color: {TEXT_PRIMARY};
    }}

    [data-testid="stHeader"] {{
        background-color: {BG_MAIN};
    }}

    /* Metric cards */
    [data-testid="stMetric"] {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 18px 20px;
    }}
    [data-testid="stMetricLabel"] {{
        color: {TEXT_MUTED} !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    [data-testid="stMetricValue"] {{
        color: {ACCENT} !important;
        font-weight: 700;
    }}

    /* Headings */
    h1, h2, h3, h4 {{
        color: {TEXT_PRIMARY} !important;
        font-family: 'Georgia', 'Times New Roman', serif;
    }}

    /* Expander (report cards) */
    .streamlit-expanderHeader {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 8px;
        color: {TEXT_PRIMARY} !important;
        font-weight: 600;
    }}
    .streamlit-expanderContent {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-top: none;
        border-radius: 0 0 8px 8px;
    }}

    /* Info / warning boxes recolored to fit dark theme */
    div[data-testid="stAlertContainer"] {{
        background-color: #1B2027 !important;
        border: 1px solid {BORDER} !important;
        color: {TEXT_PRIMARY} !important;
        border-radius: 8px;
    }}

    hr {{
        border-color: {BORDER};
    }}

    .zeluv-subtitle {{
        text-align: right;
        color: {TEXT_MUTED};
        font-size: 0.95rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-top: 6px;
    }}

    .zeluv-divider {{
        border-top: 1px solid {BORDER};
        margin: 1.2rem 0 1.6rem 0;
    }}
</style>
""", unsafe_allow_html=True)

# Dark plotly template used across all charts
pio.templates["zeluv_dark"] = pio.templates["plotly_dark"]
pio.templates["zeluv_dark"].layout.paper_bgcolor = BG_PANEL
pio.templates["zeluv_dark"].layout.plot_bgcolor = BG_PANEL
pio.templates["zeluv_dark"].layout.font.color = TEXT_PRIMARY
pio.templates.default = "zeluv_dark"

GOLD_SCALE = ["#D4AF37", "#B8860B", "#8C6D1F", "#6E5B2E", "#4F4526"]


def load_data():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    market_keys = r.keys("*")
    all_reports = []

    for market in market_keys:
        latest_json = r.lindex(market, 0)
        if latest_json:
            try:
                data = json.loads(latest_json)
                data['market_key'] = market.split()[0]
                all_reports.append(data)
            except Exception:
                pass

    return pd.DataFrame(all_reports)


# ==========================================
# DASHBOARD UI
# ==========================================

# Header: title on the left, logo on the right
header_left, header_right = st.columns([3, 1])
with header_left:
    st.markdown("<h1 style='margin-bottom:0;'>Zeluv.io</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='zeluv-subtitle' style='text-align:left;'>"
        "Global Real Estate Investment Intelligence</div>",
        unsafe_allow_html=True,
    )
with header_right:
    st.image(LOGO_URL, width=180)

st.markdown("<div class='zeluv-divider'></div>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("No reports found in the database yet. Make sure the GitHub Action has successfully finished running!")
else:
    if 'purchase_price' in df:
        df['purchase_price'] = df['purchase_price'].astype(float)
        df['annual_roi_pct'] = df['annual_roi_pct'].astype(float)
        df['cap_rate'] = df['cap_rate'].astype(float)
        df['monthly_cashflow'] = df['monthly_cashflow'].astype(float)

    st.markdown("#### Portfolio Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Global Markets Tracked", len(df))
    col2.metric("Highest Cap Rate", "{:.2f}%".format(df['cap_rate'].max()) if not df.empty else "N/A")
    col3.metric("Best Cash-on-Cash ROI", "{:.2f}%".format(df['annual_roi_pct'].max()) if not df.empty else "N/A")
    col4.metric("Highest Legal Risk", df['legal_risk_level'].mode()[0] if not df.empty else "N/A")

    st.markdown("<div class='zeluv-divider'></div>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### Cap Rate by Market")
        fig_cap = px.bar(
            df, x='market_key', y='cap_rate', color='market_key', text='cap_rate',
            color_discrete_sequence=GOLD_SCALE,
        )
        fig_cap.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_cap.update_layout(
            showlegend=False, xaxis_title="", yaxis_title="Cap Rate (%)",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_cap, use_container_width=True)

    with col_chart2:
        st.markdown("##### Monthly Cash Flow by Market")
        fig_cash = px.bar(
            df, x='market_key', y='monthly_cashflow', color='market_key', text='monthly_cashflow',
            color_discrete_sequence=GOLD_SCALE,
        )
        fig_cash.update_traces(texttemplate='$%{text}', textposition='outside')
        fig_cash.update_layout(
            showlegend=False, xaxis_title="", yaxis_title="Monthly Cash Flow ($)",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_cash, use_container_width=True)

    st.markdown("<div class='zeluv-divider'></div>", unsafe_allow_html=True)

    st.markdown("#### 📋 Latest Executive Reports")
    for index, row in df.iterrows():
        title = "🌍 {} — {}".format(row['market_key'], row.get('property_address', 'Unknown'))
        with st.expander(title):
            c1, c2 = st.columns([1, 2])
            with c1:
                price_str = "${:,.0f}".format(row['purchase_price'])
                rent_str = "${:,.0f}".format(row.get('monthly_rent', 0))
                cashflow_str = "${:,.2f}".format(row['monthly_cashflow'])
                cap_str = "{:.2f}%".format(row['cap_rate'])

                st.markdown(f"**Purchase Price:** {price_str}")
                st.markdown(f"**Monthly Rent:** {rent_str}")
                st.markdown(f"**Monthly Cashflow:** {cashflow_str}")
                st.markdown(f"**Cap Rate:** {cap_str}")
                st.markdown(f"**1% Rule:** {row.get('one_percent_rule', 'N/A')}")
                st.markdown(f"**Legal Risk:** {row.get('legal_risk_level', 'N/A')}")
            with c2:
                st.markdown("**Executive Summary:**")
                st.info(row.get('executive_summary', 'N/A'))
                st.markdown("**Recommendation:**")
                st.warning(row.get('actionable_recommendation', 'N/A'))
