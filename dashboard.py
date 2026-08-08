import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zeluv io", page_icon="🏢", layout="wide")

try:
    REDIS_URL = st.secrets["REDIS_URL"]
except:
    REDIS_URL = None

st.markdown("""
<style>
    .stApp { background-color: #000000; padding-top: 2rem; }
    .stMarkdown, p, span, div, h1, h2, h3 { font-family: 'Helvetica', 'Arial', sans-serif !important; color: #FFFFFF !important; }
    .stMetric { background-color: #1A1A1A; padding: 15px; border-radius: 4px; border: 1px solid #333333; }
    .stMetric label { color: #AAAAAA !important; }
    .stMetric value { color: #FFFFFF !important; }
    footer { visibility: hidden; }
    [data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #333333; }
    .stButton > button { border: 1px solid #333333; background-color: #1A1A1A; color: #FFFFFF; border-radius: 4px; padding: 10px 15px; font-weight: 500; width: 100%; }
    .stButton > button:hover { border-color: #FFFFFF; background-color: #333333; }
    .stSelectbox > div > div { background-color: #1A1A1A; color: #FFFFFF; border: 1px solid #333333; }
    hr { border-color: #333333 !important; }
</style>
""", unsafe_allow_html=True)

def load_data():
    if not REDIS_URL:
        st.error("REDIS_URL secret is missing in Streamlit Cloud settings!")
        return pd.DataFrame()
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        market_keys = r.keys("*")
        all_reports = []
        for market in market_keys:
            latest_json = r.lindex(market, 0)
            if latest_json:
                try:
                    data = json.loads(latest_json)
                    data['market_key'] = market.split()[0] 
                    all_reports.append(data)
                except: pass 
        return pd.DataFrame(all_reports)
    except Exception as e:
        st.error(f"Failed to connect to Redis: {e}")
        return pd.DataFrame()

st.markdown("<h1 style='font-size: 2.2rem; font-weight: 800; margin-bottom: 0; color: #FFFFFF;'>Zeluv io</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.05rem; color: #AAAAAA; margin-top: 0;'>Global Real Estate Investment Intelligence</p>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px; border-color: #333333;'>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("No reports found in the database yet. Make sure the GitHub Action has successfully finished running!")
else:
    for col in ['purchase_price', 'annual_roi_pct', 'cap_rate', 'monthly_cashflow']:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.markdown("### Global Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Markets Tracked", len(df))
    col2.metric("Highest Cap Rate", f"{df['cap_rate'].max()}%")
    col3.metric("Best ROI", f"{df['annual_roi_pct'].max()}%")
    
    if 'legal_risk_level' in df.columns and not df['legal_risk_level'].empty:
        col4.metric("Highest Legal Risk", df['legal_risk_level'].mode()[0])
    else:
        col4.metric("Highest Legal Risk", "N/A")
        
    st.markdown("---")

    st.markdown("### Market Comparison: Cap Rate vs. Cash-on-Cash ROI")
    if 'market_key' in df.columns and 'cap_rate' in df.columns and 'annual_roi_pct' in df.columns:
        df_chart = df[['market_key', 'cap_rate', 'annual_roi_pct']].melt(id_vars=['market_key'], var_name='Metric', value_name='Value')
        df_chart['Metric'] = df_chart['Metric'].replace({'cap_rate': 'Cap Rate', 'annual_roi_pct': 'Cash-on-Cash ROI'})
        fig_comp = px.bar(df_chart, x='market_key', y='Value', color='Metric', barmode='group', text='Value')
        fig_comp.update_traces(texttemplate='%{text}%', textposition='outside', textfont_color='#FFFFFF')
        fig_comp.update_layout(showlegend=True, xaxis_title="", yaxis_title="Percentage (%)", font=dict(size=12, color='#AAAAAA'), plot_bgcolor='#000000', paper_bgcolor='#000000', margin=dict(t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_comp.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='#333333', color='#AAAAAA')
        fig_comp.update_xaxes(showline=True, linewidth=1, linecolor='#333333', color='#AAAAAA')
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.warning("Waiting for financial data to be populated by the AI.")
        
    st.markdown("---")

    st.sidebar.markdown("### Navigation")
    st.sidebar.markdown("Select a market to view SWOT and Forecast.")
    
    if 'market_key' in df.columns:
        selected_market_name = st.sidebar.selectbox("Markets", df['market_key'].unique())

        if selected_market_name:
            row = df[df['market_key'] == selected_market_name].iloc[0]
            st.markdown(f"### {selected_market_name} - {row.get('property_address', 'Unknown')}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("#### Financials & Forecast")
                st.markdown(f"**Purchase Price:** ${row['purchase_price']:,.0f}")
                st.markdown(f"**Cap Rate:** {row['cap_rate']}%")
                st.markdown(f"**Cash-on-Cash ROI:** {row['annual_roi_pct']}%")
                st.markdown(f"**1% Rule:** {row.get('one_percent_rule', 'N/A')}")
                st.markdown("---")
                st.markdown("**📈 Price Forecast:**")
                st.markdown(f"• 1-Year: `{row.get('forecast_1y', 'N/A')}`")
                st.markdown(f"• 3-Year: `{row.get('forecast_3y', 'N/A')}`")
                st.markdown(f"• 5-Year: `{row.get('forecast_5y', 'N/A')}`")
            with c2:
                st.markdown("#### Executive Summary")
                st.info(row.get('executive_summary', 'N/A'))
                st.markdown("#### Recommendation")
                st.warning(row.get('actionable_recommendation', 'N/A'))
                
            st.markdown("---")
            
            st.markdown(f"### {selected_market_name}: SWOT Analysis")
            col_s, col_w, col_o, col_t = st.columns(4)
            with col_s:
                st.markdown("<div style='background-color:#1A1A1A; padding:15px; border-radius:4px; border-top: 3px solid #4A90E2; height: 100%;'><h4 style='color:#4A90E2; margin-bottom:10px;'>Strengths</h4>", unsafe_allow_html=True)
                st.write(row.get('strengths', 'N/A'))
                st.markdown("</div>", unsafe_allow_html=True)
            with col_w:
                st.markdown("<div style='background-color:#1A1A1A; padding:15px; border-radius:4px; border-top: 3px solid #FF5252; height: 100%;'><h4 style='color:#FF5252; margin-bottom:10px;'>Weaknesses</h4>", unsafe_allow_html=True)
                st.write(row.get('weaknesses', 'N/A'))
                st.markdown("</div>", unsafe_allow_html=True)
            with col_o:
                st.markdown("<div style='background-color:#1A1A1A; padding:15px; border-radius:4px; border-top: 3px solid #4CAF50; height: 100%;'><h4 style='color:#4CAF50; margin-bottom:10px;'>Opportunities</h4>", unsafe_allow_html=True)
                st.write(row.get('opportunities', 'N/A'))
                st.markdown("</div>", unsafe_allow_html=True)
            with col_t:
                st.markdown("<div style='background-color:#1A1A1A; padding:15px; border-radius:4px; border-top: 3px solid #FFC107; height: 100%;'><h4 style='color:#FFC107; margin-bottom:10px;'>Threats</h4>", unsafe_allow_html=True)
                st.write(row.get('threats', 'N/A'))
                st.markdown("</div>", unsafe_allow_html=True)
