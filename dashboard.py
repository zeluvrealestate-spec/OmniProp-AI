import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px
import requests
import io
from fpdf import FPDF

# ==========================================
# CONFIGURATION & PAGE SETUP
# ==========================================
st.set_page_config(page_title="Zeluv io", page_icon="🏢", layout="wide")

REDIS_URL = st.secrets["REDIS_URL"]
LOGO_URL = "https://z-cdn-media.chatglm.cn/files/ddb3a8de-d171-47f6-8d86-5c827f6ca5a5.png?auth_key=1886107572-89f8ef77610746cdb1d35b0f0c9c94b3-0-ae7928019b3f9fc4512fcb26fdee9a29"

# Custom CSS for a Modern, Clean, Enterprise Look
st.markdown("""
<style>
    /* Remove top padding and set pure white background */
    .stApp { background-color: #FFFFFF; padding-top: 2rem; }
    
    /* Clean modern font and spacing */
    .stMarkdown, p, span, div { font-family: 'Inter', 'Helvetica', sans-serif !important; }
    
    /* Remove default Streamlit borders and boxes for a flat look */
    .stMetric { background-color: #F8F9FA; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; }
    
    /* Force the logo to have a transparent/white blend background */
    .logo-img { mix-blend-mode: multiply; }
    
    /* Make buttons look modern */
    .stButton > button {
        border: 1px solid #E9ECEF; background-color: #FFFFFF; color: #333333;
        border-radius: 8px; padding: 10px 15px; font-weight: 500;
        transition: all 0.2s ease-in-out; width: 100%;
    }
    .stButton > button:hover {
        border-color: #333333; background-color: #F8F9FA; transform: translateY(-1px);
    }
    
    /* Hide Streamlit Footer */
    footer { visibility: hidden; }
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
# PDF GENERATOR
# ==========================================
def generate_pdf(report):
    pdf = FPDF()
    pdf.add_page()
    try:
        img_response = requests.get(LOGO_URL)
        img_byte_arr = io.BytesIO(img_response.content)
        # Put logo top right in PDF
        pdf.image(img_byte_arr, x=150, y=8, w=45)
    except: pass
        
    pdf.ln(20)
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "Investment Intelligence Report", ln=True)
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

# Modern Header: Title on left, Single Logo on right
col_header1, col_header2 = st.columns([4, 1])
with col_header1:
    st.markdown("<h1 style='font-size: 2.5rem; font-weight: 800; margin-bottom: 0; color: #1a1a1a;'>Zeluv io</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1rem; color: #6c757d; margin-top: 0;'>Global Real Estate Investment Intelligence</p>", unsafe_allow_html=True)
with col_header2:
    st.markdown(f"<img src='{LOGO_URL}' class='logo-img' width='150' style='float: right;'>", unsafe_allow_html=True)

st.markdown("---")

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
    st.markdown("### 📊 Global Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Markets Tracked", len(df))
    col2.metric("Highest Cap Rate", f"{df['cap_rate'].max()}%")
    col3.metric("Best ROI", f"{df['annual_roi_pct'].max()}%")
    col4.metric("Highest Legal Risk", df['legal_risk_level'].mode()[0])
    
    st.markdown("---")

    # Charts
    st.markdown("### 📈 Market Performance")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig_cap = px.bar(df, x='market_key', y='cap_rate', color='market_key', text='cap_rate')
        fig_cap.update_traces(texttemplate='%{text}%', textposition='outside', marker_line_width=0)
        fig_cap.update_layout(showlegend=False, xaxis_title="", yaxis_title="Cap Rate (%)", font=dict(family="Inter", size=12), plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_cap, use_container_width=True)

    with col_chart2:
        fig_cash = px.bar(df, x='market_key', y='monthly_cashflow', color='market_key', text='monthly_cashflow')
        fig_cash.update_traces(texttemplate='$%{text}', textposition='outside', marker_line_width=0)
        fig_cash.update_layout(showlegend=False, xaxis_title="", yaxis_title="Monthly Cash Flow ($)", font=dict(family="Inter", size=12), plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig_cash, use_container_width=True)

    st.markdown("---")

    # City Icons Grid (Click to view details)
    st.markdown("### 🌍 Select a Market to View Detailed Report")
    
    # Map cities to professional emojis
    city_icons = {
        "Dubai": "🏙️", "Riyadh": "🕌", "Miami": "🌴", "London": "🎡", "Tokyo": "🗼",
        "Singapore": "🦁", "New": "🗽", "Berlin": "🐻", "Sydney": "🌉", "Paris": "🥐"
    }
    
    # Create a grid of buttons (4 columns)
    cols = st.columns(4)
    for index, row in df.iterrows():
        city_name = row['market_key']
        icon = city_icons.get(city_name, "🏢")
        
        # Put button in the correct column
        with cols[index % 4]:
            if st.button(f"{icon}  {city_name}", key=f"btn_{index}"):
                st.session_state['selected_market'] = index

    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed Report Section (Shows when a city is clicked)
    if 'selected_market' in st.session_state:
        selected_index = st.session_state['selected_market']
        row = df.iloc[selected_index]
        
        st.markdown(f"### {city_icons.get(row['market_key'], '🏢')} {row['market_key']} - {row.get('property_address', 'Unknown')}")
        
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
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Zeluv_io_{row['market_key']}_Report.pdf",
                mime="application/pdf"
            )
            
        with c2:
            st.markdown("#### Executive Summary")
            st.info(row.get('executive_summary', 'N/A'))
            st.markdown("#### Recommendation")
            st.warning(row.get('actionable_recommendation', 'N/A'))
    else:
        st.info("👆 Click a city above to load its detailed investment report.")
