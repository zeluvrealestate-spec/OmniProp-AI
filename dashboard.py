import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(page_title="Zeluv io", page_icon="🏢", layout="wide")

# Read the URL securely from Streamlit Cloud
REDIS_URL = st.secrets["REDIS_URL"]

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
            except:
                pass 
                
    return pd.DataFrame(all_reports)

# ==========================================
# DASHBOARD UI
# ==========================================
st.title("🏢 Zeluv io Dashboard")
st.markdown("Global Real Estate Investment Intelligence & Analytics")

df = load_data()

if df.empty:
    st.warning("No reports found in the database yet. Make sure the GitHub Action has successfully finished running!")
else:
    if 'purchase_price' in df:
        df['purchase_price'] = df['purchase_price'].astype(float)
        df['annual_roi_pct'] = df['annual_roi_pct'].astype(float)
        df['cap_rate'] = df['cap_rate'].astype(float)
        df['monthly_cashflow'] = df['monthly_cashflow'].astype(float)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Global Markets Tracked", len(df))
    col2.metric("Highest Cap Rate", "{}%".format(df['cap_rate'].max()) if not df.empty else "N/A")
    col3.metric("Best Cash-on-Cash ROI", "{}%".format(df['annual_roi_pct'].max()) if not df.empty else "N/A")
    col4.metric("Highest Legal Risk", df['legal_risk_level'].mode()[0] if not df.empty else "N/A")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Cap Rate by Market")
        fig_cap = px.bar(df, x='market_key', y='cap_rate', color='market_key', text='cap_rate')
        fig_cap.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_cap.update_layout(showlegend=False, xaxis_title="", yaxis_title="Cap Rate (%)")
        st.plotly_chart(fig_cap, use_container_width=True)

    with col_chart2:
        st.subheader("Monthly Cash Flow by Market")
        fig_cash = px.bar(df, x='market_key', y='monthly_cashflow', color='market_key', text='monthly_cashflow')
        fig_cash.update_traces(texttemplate='$%{text}', textposition='outside')
        fig_cash.update_layout(showlegend=False, xaxis_title="", yaxis_title="Monthly Cash Flow ($)")
        st.plotly_chart(fig_cash, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 Latest Executive Reports")
    for index, row in df.iterrows():
        title = "🌍 {} - {}".format(row['market_key'], row.get('property_address', 'Unknown'))
        with st.expander(title):
            c1, c2 = st.columns([1, 2])
            with c1:
                price_str = "${:,.0f}".format(row['purchase_price'])
                rent_str = "${:,.0f}".format(row.get('monthly_rent', 0))
                cashflow_str = "${:,.2f}".format(row['monthly_cashflow'])
                cap_str = "{}%".format(row['cap_rate'])
                
                st.markdown("**Purchase Price:** " + price_str)
                st.markdown("**Monthly Rent:** " + rent_str)
                st.markdown("**Monthly Cashflow:** " + cashflow_str)
                st.markdown("**Cap Rate:** " + cap_str)
                st.markdown("**1% Rule:** " + str(row.get('one_percent_rule', 'N/A')))
                st.markdown("**Legal Risk:** " + str(row.get('legal_risk_level', 'N/A')))
            with c2:
                st.markdown("**Executive Summary:**")
                st.info(row.get('executive_summary', 'N/A'))
                st.markdown("**Recommendation:**")
                st.warning(row.get('actionable_recommendation', 'N/A'))
