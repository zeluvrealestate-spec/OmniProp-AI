import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px
import io
from fpdf import FPDF

# ==========================================
# CONFIGURATION & PAGE SETUP
# ==========================================
st.set_page_config(page_title="Zeluv io", page_icon="🏢", layout="wide")

REDIS_URL = st.secrets["REDIS_URL"]

# Custom CSS for a Modern, Sleek Black Enterprise Look
st.markdown("""
<style>
    /* Set pure black background */
    .stApp { background-color: #000000; padding-top: 2rem; }
    
    /* Clean modern font and ensure text is white/light gray */
    .stMarkdown, p, span, div, h1, h2, h3 { font-family: 'Helvetica', 'Arial', sans-serif !important; color: #FFFFFF !important; }
    
    /* KPI Metric boxes - Dark Gray with subtle border */
    .stMetric { background-color: #1A1A1A; padding: 15px; border-radius: 4px; border: 1px solid #333333; }
    .stMetric label { color: #AAAAAA !important; }
    .stMetric value { color: #FFFFFF !important; }
    
    /* Remove Streamlit Footer */
    footer { visibility: hidden; }
    
    /* Sidebar styling - True Black */
    [data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #333333; }
    
    /* Make buttons look modern */
    .stButton > button {
        border: 1px solid #333333; background-color: #1A1A1A; color: #FFFFFF;
        border-radius: 4px; padding: 10px 15px; font-weight: 500;
        transition: all 0.2s ease-in-out; width: 100%;
    }
    .stButton > button:hover {
        border-color: #FFFFFF; background-color: #333333; 
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div { background-color: #1A1A1A; color: #FFFFFF; border: 1px solid #333333; }
    
    /* Horizontal rule color */
    hr { border-color: #333333 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING
# ==========================================
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
            except: pass 
    return pd.DataFrame(all_reports)

# ==========================================
# PDF GENERATOR (Keeps white background for printing)
# ==========================================
def generate_pdf(report):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "Zeluv io", ln=True)
    
    pdf.set_font("Helvetica", '', 12)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 10, "Investment Intelligence Report", ln=True)
    pdf.ln(10)
    
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, 35, 200, 35)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "PROPERTY DETAILS", ln=True)
    
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Market: {report.get('market_key', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Address: {report.get('property_address', 'N/A')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "FINANCIAL METRICS", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 8, f"Purchase Price: ${report.get('purchase_price', 0):,.0f}", ln=True)
    pdf.cell(0, 8, f"Monthly Cash Flow: ${report.get('monthly_cashflow', 0):,.2f}", ln=True)
    pdf.cell(0, 8, f"Cap Rate: {report.get('cap_rate', 0)}%", ln=True)
    pdf.cell(0, 8, f"1% Rule: {report.get('one_percent_rule', 'N/A')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "EXECUTIVE SUMMARY", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.multi_cell(0, 8, report.get('executive_summary', 'N/A'))
    
    return bytes(pdf.output())

# ==========================================
# DASHBOARD UI
# ==========================================

# Clean Header
st.markdown("<h1 style='font-size: 2.2rem; font-weight: 800; margin-bottom: 0; color: #FFFFFF;'>Zeluv io</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.05rem; color: #AAAAAA; margin-top: 0;'>Global Real Estate Investment Intelligence</p>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px; border-color: #333333;'>", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("No reports found in the database yet. Make sure the GitHub Action has successfully finished running!")
else:
    # Clean Data
    if 'purchase_price' in df:
        df['purchase_price'] = df['purchase_price'].astype(float)
        df['annual_roi_pct'] = df['annual_roi_pct'].astype(float)
        df['cap_rate'] = df['cap_rate'].astype(float)
        df['monthly_cashflow'] = df['monthly_cashflow'].astype(float)

    # Top KPI Metrics
    st.markdown("### Global Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Markets Tracked", len(df))
    col2.metric("Highest Cap Rate", f"{df['cap_rate'].max()}%")
    col3.metric("Best ROI", f"{df['annual_roi_pct'].max()}%")
    col4.metric("Highest Legal Risk", df['legal_risk_level'].mode()[0])
    
    st.markdown("---")

    # Professional Charts (Neon Pop on Black)
    st.markdown("### Market Performance")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_cap = px.bar(df, x='market_key', y='cap_rate', text='cap_rate')
        fig_cap.update_traces(marker_color='#4A90E2', marker_line_width=0, texttemplate='%{text}%', textposition='outside', textfont_color='#FFFFFF')
        fig_cap.update_layout(showlegend=False, xaxis_title="", yaxis_title="Cap Rate (%)", font=dict(size=12, color='#AAAAAA'), plot_bgcolor='#000000', paper_bgcolor='#000000', margin=dict(t=10, b=10))
        fig_cap.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='#333333', color='#AAAAAA')
        fig_cap.update_xaxes(showline=True, linewidth=1, linecolor='#333333', color='#AAAAAA')
        st.plotly_chart(fig_cap, use_container_width=True)

    with col_chart2:
        # Cash flow: Bright Red for negative, Bright Blue for positive
        cash_colors = ['#FF5252' if x < 0 else '#4A90E2' for x in df['monthly_cashflow']]
        fig_cash = px.bar(df, x='market_key', y='monthly_cashflow', text='monthly_cashflow')
        fig_cash.update_traces(marker_color=cash_colors, marker_line_width=0, texttemplate='$%{text}', textposition='outside', textfont_color='#FFFFFF')
        fig_cash.update_layout(showlegend=False, xaxis_title="", yaxis_title="Monthly Cash Flow ($)", font=dict(size=12, color='#AAAAAA'), plot_bgcolor='#000000', paper_bgcolor='#000000', margin=dict(t=10, b=10))
        fig_cash.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='#333333', color='#AAAAAA')
        fig_cash.update_xaxes(showline=True, linewidth=1, linecolor='#333333', color='#AAAAAA')
        st.plotly_chart(fig_cash, use_container_width=True)

    st.markdown("---")

    # Professional Sidebar Selection
    st.sidebar.markdown("### Navigation")
    st.sidebar.markdown("Select a market to view its detailed investment report and download the PDF.")
    selected_market_name = st.sidebar.selectbox("Markets", df['market_key'].unique())

    # Detailed Report Section
    if selected_market_name:
        # Get the data for the selected market
        row = df[df['market_key'] == selected_market_name].iloc[0]
        
        st.markdown(f"### {selected_market_name} - {row.get('property_address', 'Unknown')}")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### Financials")
            st.markdown(f"**Purchase Price:** ${row['purchase_price']:,.0f}")
            st.markdown(f"**Monthly Rent:** ${row.get('monthly_rent', 0):,.0f}")
            st.markdown(f"**Monthly Cashflow:** ${row['monthly_cashflow']:,.2f}")
            st.markdown(f"**Cap Rate:** {row['cap_rate']}%")
            st.markdown(f"**1% Rule:** {row.get('one_percent_rule', 'N/A')}")
            st.markdown(f"**Legal Risk:** {row.get('legal_risk_level', 'N/A')}")
            
            st.markdown("---")
            pdf_bytes = generate_pdf(row)
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"Zeluv_io_{row['market_key']}_Report.pdf",
                mime="application/pdf"
            )
            
        with c2:
            st.markdown("#### Executive Summary")
            st.info(row.get('executive_summary', 'N/A'))
            st.markdown("#### Recommendation")
            st.warning(row.get('actionable_recommendation', 'N/A'))
