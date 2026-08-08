# ==========================================
# PDF GENERATOR (Bulletproofed)
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
    pdf.cell(0, 8, "FINANCIAL METRICS", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Price: ${report.get('purchase_price', 0):,.0f}", ln=True)
    pdf.cell(0, 8, f"Cap Rate: {report.get('cap_rate', 0)}%", ln=True)
    pdf.cell(0, 8, f"Cash-on-Cash ROI: {report.get('annual_roi_pct', 0)}%", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "SWOT ANALYSIS", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(0, 0, 0)
    
    # Use wrapmode="CHAR" to prevent crashes on long words
    pdf.multi_cell(0, 8, f"Strengths: {clean_text(report.get('strengths', 'N/A'))}", wrapmode="CHAR")
    pdf.multi_cell(0, 8, f"Weaknesses: {clean_text(report.get('weaknesses', 'N/A'))}", wrapmode="CHAR")
    pdf.multi_cell(0, 8, f"Opportunities: {clean_text(report.get('opportunities', 'N/A'))}", wrapmode="CHAR")
    pdf.multi_cell(0, 8, f"Threats: {clean_text(report.get('threats', 'N/A'))}", wrapmode="CHAR")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "EXECUTIVE SUMMARY", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.multi_cell(0, 8, clean_text(report.get('executive_summary', 'N/A')), wrapmode="CHAR")
    
    return bytes(pdf.output())
