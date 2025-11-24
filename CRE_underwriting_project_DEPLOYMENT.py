# -*- coding: utf-8 -*-
"""
CRE DCF Valuation Model v5.3 - Fixed Tax Calculations & Layout
@author: danie
"""

import streamlit as st
import hmac

st.set_page_config(
    page_title="CRE DCF Valuation Model",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go
import json
import os
import time
import random

# ==================== PASSWORD PROTECTION ====================
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], "CRE2024Demo"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # Return True if password is correct
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.markdown("## 🏢 CRE DCF Valuation Model")
    st.markdown("### 🔐 Access Required")
    st.info("This tool is password-protected. Please contact the developer for access credentials.")
    
    st.text_input(
        "Enter Password", 
        type="password", 
        on_change=password_entered, 
        key="password",
        placeholder="Enter password here"
    )
    
    if "password_correct" in st.session_state:
        st.error("❌ Incorrect password. Please try again.")
    
    st.markdown("---")
    st.markdown("**Contact:** [Your Email/LinkedIn]")
    
    return False

# Check password before running the app
if not check_password():
    st.stop()

# ==================== APP CONTINUES BELOW ====================

import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go
import json
import os
import time
import random

# PDF Generation imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER
    from datetime import datetime
    import io
    import tempfile
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


DEALS_FILE = "saved_deals.json"

# ==================== PDF THEME CONFIGURATIONS ====================
PDF_THEMES = {
    "professional_blue": {
        "name": "Professional Blue",
        "primary": '#1f77b4',
        "secondary": '#aec7e8',
        "accent": '#ff7f0e'
    },
    "modern_dark": {
        "name": "Modern Dark",
        "primary": '#2c3e50',
        "secondary": '#34495e',
        "accent": '#e74c3c'
    },
    "corporate_green": {
        "name": "Corporate Green",
        "primary": '#27ae60',
        "secondary": '#2ecc71',
        "accent": '#f39c12'
    },
    "finance_burgundy": {
        "name": "Finance Burgundy",
        "primary": '#8e44ad',
        "secondary": '#9b59b6',
        "accent": '#e67e22'
    },
    "minimalist_black": {
        "name": "Minimalist Black",
        "primary": '#000000',
        "secondary": '#333333',
        "accent": '#cccccc'
    },
    "real_estate_gold": {
        "name": "Real Estate Gold",
        "primary": '#d4af37',
        "secondary": '#f4e7c7',
        "accent": '#8b4513'
    }
}





# ==================== CHART CAPTURE HELPER ====================
def save_chart_to_session(chart_name, fig):
    """Save plotly figure to session state for PDF inclusion"""
    try:
        # Try to convert to image bytes using kaleido
        img_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
        st.session_state.charts[chart_name] = img_bytes
    except:
        try:
            # Fallback: use plotly's write_image with orca
            import io as io_module
            img_buffer = io_module.BytesIO()
            fig.write_image(img_buffer, format='png', width=1200, height=700)
            img_buffer.seek(0)
            st.session_state.charts[chart_name] = img_buffer.read()
        except:
            # Final fallback: save figure object and try to convert in PDF
            st.session_state.charts[chart_name] = fig


# ==================== PDF GENERATION FUNCTIONS ====================
def generate_pdf_report(property_data, cash_flow_df, theme_key="professional_blue", charts_dict=None, loan_schedule_df=None):
    """Generate professional PDF investment memo"""
    
    if not PDF_AVAILABLE:
        return None
    
    # Track temp files for cleanup after PDF is built
    temp_files_to_cleanup = []
    
    # Get theme colors
    theme = PDF_THEMES.get(theme_key, PDF_THEMES["professional_blue"])
    primary_color = colors.HexColor(theme["primary"])
    secondary_color = colors.HexColor(theme["secondary"])
    accent_color = colors.HexColor(theme["accent"])
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                fontSize=24, textColor=primary_color,
                                spaceAfter=30, alignment=TA_CENTER)
    
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                  fontSize=16, textColor=primary_color,
                                  spaceAfter=12, spaceBefore=12)
    
    # Title Page
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("COMMERCIAL REAL ESTATE", title_style))
    story.append(Paragraph("INVESTMENT MEMORANDUM", title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"<b>{property_data['property_name']}</b>", title_style))
    story.append(Paragraph(f"{property_data['property_type']}", styles['Normal']))
    story.append(Spacer(1, 1*inch))
    
    # Key metrics
    metrics_data = [
        ['PURCHASE PRICE', f"${property_data['purchase_price']:,.0f}"],
        ['LEVERED IRR', f"{property_data['irr']:.2f}%"],
        ['EQUITY MULTIPLE', f"{property_data['equity_multiple']:.2f}x"],
        ['NPV', f"${property_data['npv']:,.0f}"]
    ]
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2.5*inch])
    metrics_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(f"<i>Generated: {datetime.now().strftime('%B %d, %Y')}</i>", styles['Normal']))
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
    story.append(Spacer(1, 0.2*inch))
    
    summary_text = f"""
    <b>Property:</b> {property_data['property_name']}<br/>
    <b>Type:</b> {property_data['property_type']}<br/>
    <b>Purchase Price:</b> ${property_data['purchase_price']:,.0f}<br/>
    <b>Equity Required:</b> ${property_data['equity_required']:,.0f}<br/>
    <b>Holding Period:</b> {property_data['holding_period']} years<br/>
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Return Metrics Table
    returns_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Levered IRR', f"{property_data['irr']:.2f}%", 
         'Outstanding' if property_data['irr'] >= 20 else 'Excellent' if property_data['irr'] >= 15 else 'Good' if property_data['irr'] >= 12 else 'Solid'],
        ['Equity Multiple', f"{property_data['equity_multiple']:.2f}x", 
         f"${property_data['equity_multiple']:.2f} back per $1 invested"],
        ['NPV', f"${property_data['npv']:,.0f}", 
         'Exceeds required return' if property_data['npv'] > 0 else 'Below required return'],
        ['Avg Cash-on-Cash', f"{property_data.get('avg_coc', 0):.2f}%", 'Annual cash yield']
    ]
    
    returns_table = Table(returns_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    returns_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(returns_table)
    story.append(PageBreak())
    
    # Investment Summary
    story.append(Paragraph("INVESTMENT SUMMARY", heading_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
    story.append(Spacer(1, 0.2*inch))
    
    inv_data = [
        ['ACQUISITION', ''],
        ['Purchase Price', f"${property_data['purchase_price']:,.0f}"],
        ['Closing Costs', f"${property_data['closing_costs']:,.0f}"],
        ['Total Acquisition', f"${property_data['purchase_price'] + property_data['closing_costs']:,.0f}"],
        ['', ''],
        ['CAPITAL STRUCTURE', ''],
        ['Loan Amount', f"${property_data['loan_amount']:,.0f}"],
        ['LTV', f"{property_data['loan_to_value']:.1f}%"],
        ['Equity Required', f"${property_data['equity_required']:,.0f}"],
        ['', ''],
        ['RETURNS', ''],
        ['Going-In Cap Rate', f"{property_data['going_in_cap']:.2f}%"],
        ['Exit Cap Rate', f"{property_data['exit_cap_rate']:.2f}%"],
    ]
    
    inv_table = Table(inv_data, colWidths=[3*inch, 2*inch])
    inv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, 5), (-1, 5), primary_color),
        ('TEXTCOLOR', (0, 5), (-1, 5), colors.whitesmoke),
        ('BACKGROUND', (0, 10), (-1, 10), primary_color),
        ('TEXTCOLOR', (0, 10), (-1, 10), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(inv_table)
    story.append(PageBreak())
    
    # Cash Flow Table
    story.append(Paragraph(f"{property_data['holding_period']}-YEAR CASH FLOW PROJECTION", heading_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
    story.append(Spacer(1, 0.2*inch))
    
    cf_data = [['Year', 'NOI', 'CapEx', 'Debt Service', 'BTCF', 'CoC %']]
    for _, row in cash_flow_df.iterrows():
        cf_data.append([
            str(int(row['Year'])),
            f"${row['NOI']:,.0f}",
            f"${row['CapEx']:,.0f}",
            f"${row['Debt Service']:,.0f}",
            f"${row['BTCF']:,.0f}",
            f"{row['CoC Return %']:.1f}%"
        ])
    
    cf_table = Table(cf_data, colWidths=[0.5*inch, 1.1*inch, 0.9*inch, 1.1*inch, 1.1*inch, 0.8*inch])
    cf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(cf_table)
    story.append(PageBreak())
    

    
    # Add Charts/Visualizations section if charts exist
    if charts_dict and len(charts_dict) > 0:
        story.append(Paragraph("VISUALIZATIONS", heading_style))
        story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
        story.append(Spacer(1, 0.2*inch))
        
        for chart_name, chart_data in charts_dict.items():
            try:
                # Create temp file for image
                import tempfile
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                tmp_path = tmp.name
                
                if isinstance(chart_data, bytes):
                    tmp.write(chart_data)
                    tmp.close()
                    temp_files_to_cleanup.append(tmp_path)
                    
                    # Add to PDF
                    from reportlab.platypus import Image as RLImage
                    img = RLImage(tmp_path, width=6.5*inch, height=3.8*inch)
                    story.append(Paragraph(f"<b>{chart_name}</b>", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                else:
                    # Try multiple methods to convert plotly figure
                    img_bytes = None
                    
                    # Method 1: Try kaleido with explicit engine
                    try:
                        import kaleido
                        img_bytes = chart_data.to_image(format="png", width=1200, height=700, scale=2, engine="kaleido")
                    except Exception as e1:
                        # Method 2: Try without engine specification
                        try:
                            img_bytes = chart_data.to_image(format="png", width=1200, height=700, scale=2)
                        except Exception as e2:
                            # Method 3: Try write_image
                            try:
                                import io as io_module
                                img_buffer = io_module.BytesIO()
                                chart_data.write_image(img_buffer, format='png', width=1200, height=700, engine="kaleido")
                                img_bytes = img_buffer.getvalue()
                            except Exception as e3:
                                # Method 4: Try with orca (legacy)
                                try:
                                    img_bytes = chart_data.to_image(format="png", width=1200, height=700, scale=2, engine="orca")
                                except Exception as e4:
                                    # All methods failed - skip this chart
                                    story.append(Paragraph(f"<i>Chart: {chart_name} (unable to embed - chart rendering not available in this environment)</i>", styles['Normal']))
                                    story.append(Spacer(1, 0.2*inch))
                                    tmp.close()
                                    import os
                                    try:
                                        os.unlink(tmp_path)
                                    except:
                                        pass
                                    continue
                    
                    # If we got image bytes, save and embed
                    if img_bytes:
                        tmp.write(img_bytes)
                        tmp.close()
                        temp_files_to_cleanup.append(tmp_path)
                        
                        from reportlab.platypus import Image as RLImage
                        img = RLImage(tmp_path, width=6.5*inch, height=3.8*inch)
                        story.append(Paragraph(f"<b>{chart_name}</b>", styles['Normal']))
                        story.append(Spacer(1, 0.1*inch))
                        story.append(img)
                        story.append(Spacer(1, 0.3*inch))
                        
            except Exception as e:
                story.append(Paragraph(f"<i>Chart: {chart_name} (unable to embed - {str(e)[:50]})</i>", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())

    # Assumptions
    story.append(Paragraph("ASSUMPTIONS & INPUTS", heading_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
    story.append(Spacer(1, 0.2*inch))
    
    assump_data = [
        ['OPERATING ASSUMPTIONS', ''],
        ['Rent Growth Rate', f"{property_data['rent_growth']:.2f}%"],
        ['Vacancy Rate', f"{property_data['vacancy']:.1f}%"],
        ['OpEx Growth Rate', f"{property_data['opex_growth']:.2f}%"],
        ['Management Fee', f"{property_data['management_fee']:.1f}%"],
        ['', ''],
        ['EXIT ASSUMPTIONS', ''],
        ['Holding Period', f"{property_data['holding_period']} years"],
        ['Exit Cap Rate', f"{property_data['exit_cap_rate']:.2f}%"],
        ['Selling Costs', f"{property_data['selling_costs']:.1f}%"],
    ]
    
    assump_table = Table(assump_data, colWidths=[3.5*inch, 2*inch])
    assump_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, 6), (-1, 6), primary_color),
        ('TEXTCOLOR', (0, 6), (-1, 6), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(assump_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Disclaimer
    disclaimer = """<b>DISCLAIMER:</b> This investment memorandum is for informational purposes only. 
    All investments involve risk and may result in loss. Past performance is not indicative of future results."""
    story.append(Paragraph(disclaimer, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"<i>Generated by CRE DCF Valuation Model v5.3 on {datetime.now().strftime('%B %d, %Y')}</i>", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Clean up all temp files after PDF is successfully built
    import os
    for tmp_path in temp_files_to_cleanup:
        try:
            os.unlink(tmp_path)
        except:
            pass
    
    return buffer


# ==================== DEAL SCORING & RECOMMENDATION SYSTEM ====================

def calculate_deal_score(metrics, property_data):
    """
    Calculate comprehensive deal score (0-100) based on 5 categories
    Returns: (total_score, breakdown_dict, grade, rating)
    """
    try:
        score_breakdown = {}
        total_score = 0
        
        # CATEGORY 1: RETURN METRICS (30 points max)
        irr_score = 0
        irr = metrics.get('irr', 0)
        if irr >= 20:    irr_score = 20
        elif irr >= 17:  irr_score = 18
        elif irr >= 15:  irr_score = 16
        elif irr >= 12:  irr_score = 13
        elif irr >= 10:  irr_score = 10
        elif irr >= 8:   irr_score = 6
        else:            irr_score = 2
        
        em_score = 0
        em = metrics.get('equity_multiple', 1)
        if em >= 3.5:    em_score = 10
        elif em >= 3.0:  em_score = 9
        elif em >= 2.5:  em_score = 8
        elif em >= 2.0:  em_score = 6
        elif em >= 1.5:  em_score = 4
        else:            em_score = 2
        
        returns_score = irr_score + em_score
        score_breakdown['Returns (IRR/EM)'] = {'score': returns_score, 'max': 30}
        total_score += returns_score
        
        # CATEGORY 2: VALUE CREATION (20 points max)
        value_score = 0
        npv = metrics.get('npv', 0)
        equity = property_data.get('equity_required', 1)
        npv_pct = (npv / equity) * 100 if equity > 0 else 0
        
        if npv_pct >= 25:    value_score = 20
        elif npv_pct >= 20:  value_score = 18
        elif npv_pct >= 15:  value_score = 15
        elif npv_pct >= 10:  value_score = 12
        elif npv_pct >= 5:   value_score = 8
        elif npv_pct >= 0:   value_score = 5
        else:                value_score = 0
        
        score_breakdown['Value Creation (NPV)'] = {'score': value_score, 'max': 20}
        total_score += value_score
        
        # CATEGORY 3: CASH FLOW STRENGTH (20 points max)
        year1_coc = metrics.get('year1_coc', 0)
        coc1_score = 0
        if year1_coc >= 10:   coc1_score = 12
        elif year1_coc >= 8:  coc1_score = 10
        elif year1_coc >= 6:  coc1_score = 8
        elif year1_coc >= 4:  coc1_score = 5
        elif year1_coc >= 2:  coc1_score = 3
        else:                 coc1_score = 1
        
        avg_coc = metrics.get('avg_coc', 0)
        coc_avg_score = 0
        if avg_coc >= 12:     coc_avg_score = 8
        elif avg_coc >= 10:   coc_avg_score = 7
        elif avg_coc >= 8:    coc_avg_score = 5
        elif avg_coc >= 6:    coc_avg_score = 3
        else:                 coc_avg_score = 1
        
        cashflow_score = coc1_score + coc_avg_score
        score_breakdown['Cash Flow Strength'] = {'score': cashflow_score, 'max': 20}
        total_score += cashflow_score
        
        # CATEGORY 4: MARKET POSITIONING (15 points max)
        going_in_cap = metrics.get('cap_rate', 0)
        exit_cap = property_data.get('exit_cap_rate', 0)
        cap_spread = exit_cap - going_in_cap
        
        cap_score = 0
        if cap_spread >= 1.5:     cap_score = 10
        elif cap_spread >= 1.0:   cap_score = 8
        elif cap_spread >= 0.5:   cap_score = 6
        elif cap_spread >= 0:     cap_score = 4
        elif cap_spread >= -0.5:  cap_score = 2
        else:                     cap_score = 0
        
        # Entry valuation vs market
        property_type = property_data.get('property_type', '')
        market_caps = {'Multifamily': 5.5, 'Office': 7.0, 'Retail': 6.5, 'Single Family': 6.0}
        market_cap = market_caps.get(property_type, 6.5)
        
        entry_score = 0
        if going_in_cap >= market_cap + 1:    entry_score = 5  # Buying cheap
        elif going_in_cap >= market_cap:      entry_score = 3  # Fair
        else:                                  entry_score = 1  # Premium
        
        market_score = cap_score + entry_score
        score_breakdown['Market Positioning'] = {'score': market_score, 'max': 15}
        total_score += market_score
        
        # CATEGORY 5: RISK FACTORS (15 points max)
        ltv = property_data.get('loan_to_value', 0)
        ltv_score = 0
        if ltv == 0:          ltv_score = 5  # All cash
        elif ltv <= 65:       ltv_score = 5
        elif ltv <= 75:       ltv_score = 4
        elif ltv <= 80:       ltv_score = 3
        else:                 ltv_score = 1
        
        dscr_score = 0
        if ltv == 0:
            dscr_score = 5  # All cash, no debt service
        else:
            dscr = metrics.get('dscr', 0)
            if dscr >= 1.5:    dscr_score = 5
            elif dscr >= 1.3:  dscr_score = 4
            elif dscr >= 1.2:  dscr_score = 3
            elif dscr >= 1.1:  dscr_score = 2
            else:              dscr_score = 0
        
        holding_period = property_data.get('holding_period', 10)
        hold_score = 0
        if holding_period <= 5:      hold_score = 5
        elif holding_period <= 10:   hold_score = 4
        elif holding_period <= 20:   hold_score = 3
        elif holding_period <= 30:   hold_score = 2
        else:                         hold_score = 1
        
        risk_score = ltv_score + dscr_score + hold_score
        score_breakdown['Risk Profile'] = {'score': risk_score, 'max': 15}
        total_score += risk_score
        
        # Calculate grade
        if total_score >= 95:     grade, rating = 'A+', 'Elite'
        elif total_score >= 90:   grade, rating = 'A', 'Outstanding'
        elif total_score >= 85:   grade, rating = 'A-', 'Excellent'
        elif total_score >= 80:   grade, rating = 'B+', 'Very Good'
        elif total_score >= 75:   grade, rating = 'B', 'Good'
        elif total_score >= 70:   grade, rating = 'B-', 'Above Average'
        elif total_score >= 65:   grade, rating = 'C+', 'Average'
        elif total_score >= 60:   grade, rating = 'C', 'Below Average'
        elif total_score >= 55:   grade, rating = 'C-', 'Weak'
        else:                      grade, rating = 'F', 'Poor'
        
        return total_score, score_breakdown, grade, rating
        
    except Exception as e:
        # If anything fails, return neutral score
        return 50, {}, 'C', 'Average'


def generate_recommendation(total_score, score_breakdown, metrics, property_data):
    """
    Generate detailed recommendation based on score and metrics
    Returns: dict with recommendation, strengths, risks, actions
    """
    try:
        recommendation = {}
        
        # Determine overall recommendation
        if total_score >= 85:
            recommendation['action'] = '🟢 STRONG BUY'
            recommendation['summary'] = 'This deal offers exceptional risk-adjusted returns. Proceed with acquisition immediately.'
        elif total_score >= 75:
            recommendation['action'] = '🟢 BUY'
            recommendation['summary'] = 'Solid investment opportunity that meets investment criteria. Proceed if available.'
        elif total_score >= 65:
            recommendation['action'] = '🟡 HOLD'
            recommendation['summary'] = 'Average deal with mixed qualities. Consider waiting for better opportunities.'
        elif total_score >= 55:
            recommendation['action'] = '🟠 PASS'
            recommendation['summary'] = 'Below-average deal with significant concerns. Not recommended.'
        else:
            recommendation['action'] = '🔴 HARD PASS'
            recommendation['summary'] = 'This deal has critical red flags. Do not proceed.'
        
        # Identify strengths (categories scoring above 70%)
        strengths = []
        for category, data in score_breakdown.items():
            pct = (data['score'] / data['max']) * 100
            if pct >= 80:
                strengths.append(f"✓ {category}: {data['score']}/{data['max']} pts ({pct:.0f}%)")
        
        if metrics.get('irr', 0) >= 15:
            strengths.append(f"✓ Superior IRR of {metrics['irr']:.1f}% (well above market)")
        if metrics.get('npv', 0) > 0:
            strengths.append(f"✓ Positive NPV of ${metrics['npv']:,.0f} (creating value)")
        if metrics.get('equity_multiple', 0) >= 2.5:
            strengths.append(f"✓ Strong equity multiple of {metrics['equity_multiple']:.1f}x")
        
        recommendation['strengths'] = strengths[:4]  # Top 4 strengths
        
        # Identify risks (categories scoring below 50%)
        risks = []
        for category, data in score_breakdown.items():
            pct = (data['score'] / data['max']) * 100
            if pct < 50:
                risks.append(f"⚠ {category}: {data['score']}/{data['max']} pts ({pct:.0f}%) - needs attention")
        
        if metrics.get('irr', 0) < 10:
            risks.append(f"⚠ IRR of {metrics['irr']:.1f}% below typical threshold")
        if metrics.get('npv', 0) < 0:
            risks.append(f"⚠ Negative NPV indicates deal doesn't meet required return")
        if property_data.get('holding_period', 0) > 20:
            risks.append(f"⚠ Very long {property_data['holding_period']}-year hold increases uncertainty")
        
        recommendation['risks'] = risks[:4]  # Top 4 risks
        
        # Action items
        actions = []
        if total_score >= 75:
            actions.append("1. Verify rent comps and growth assumptions with local brokers")
            actions.append("2. Confirm property condition and CapEx budget accuracy")
            actions.append("3. Review tenant quality and lease terms in detail")
        else:
            actions.append("1. Reassess assumptions - are they too aggressive?")
            actions.append("2. Explore ways to improve returns (lower price, better financing)")
            actions.append("3. Compare against other available opportunities")
        
        recommendation['actions'] = actions
        
        # Confidence level
        if total_score >= 85:
            recommendation['confidence'] = 'HIGH'
        elif total_score >= 70:
            recommendation['confidence'] = 'MODERATE'
        else:
            recommendation['confidence'] = 'LOW'
        
        return recommendation
        
    except Exception as e:
        return {
            'action': '🟡 REVIEW NEEDED',
            'summary': 'Unable to generate recommendation. Review metrics manually.',
            'strengths': [],
            'risks': [],
            'actions': [],
            'confidence': 'N/A'
        }





# Initialize session state for chart storage
if 'charts' not in st.session_state:
    st.session_state.charts = {}
if 'pdf_theme' not in st.session_state:
    st.session_state.pdf_theme = 'professional_blue'

if 'show_intro' not in st.session_state:
    st.session_state.show_intro = True
if 'show_matrix' not in st.session_state:
    st.session_state.show_matrix = False
if 'matrix_color' not in st.session_state:
    colors = ['#00ff00', '#ff0000', '#0000ff', '#ffff00', '#ff8800', '#aa00ff']
    st.session_state.matrix_color = random.choice(colors)

@st.cache_data(ttl=1)  # Cache for 1 second to allow saves to persist
def load_deals_from_file():
    if os.path.exists(DEALS_FILE):
        try:
            with open(DEALS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_deal_to_file(deal_name, deal_data):
    deals = load_deals_from_file()
    deals[deal_name] = deal_data
    with open(DEALS_FILE, 'w') as f:
        json.dump(deals, f, indent=2)
    # Clear cache so next load gets fresh data
    load_deals_from_file.clear()

def delete_deal_from_file(deal_name):
    deals = load_deals_from_file()
    if deal_name in deals:
        del deals[deal_name]
        with open(DEALS_FILE, 'w') as f:
            json.dump(deals, f, indent=2)
        # Clear cache so next load gets fresh data
        load_deals_from_file.clear()
        return True
    return False

@st.cache_data(ttl=1)  # Cache for 1 second
def get_deals_by_type(property_type):
    deals = load_deals_from_file()
    return {name: data for name, data in deals.items() if data.get('property_type') == property_type}

# ==================== INTRO SCREEN ====================
if st.session_state.show_intro and not st.session_state.show_matrix:
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .intro-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            padding-top: 10vh;
        }
        .hello-text {
            font-size: 6rem;
            font-weight: bold;
            color: white;
            animation: fadeIn 1s ease-in;
            margin-bottom: 2rem;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        
        <div class="intro-wrapper">
            <div class="hello-text">Hello</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨ Click here to get started ✨", key="start_btn", use_container_width=True):
            st.session_state.show_intro = False
            st.session_state.show_matrix = True
            st.rerun()
    
    st.stop()

elif st.session_state.show_matrix:
    matrix_color = st.session_state.matrix_color
    
    st.markdown(f"""
        <style>
        .stApp {{
            background: #000 !important;
        }}
        .matrix-message {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 2.5rem;
            color: {matrix_color};
            font-weight: bold;
            font-family: 'Courier New', monospace;
            text-align: center;
            z-index: 10000;
            animation: glow 1.5s ease-in-out infinite;
            text-shadow: 0 0 20px {matrix_color};
        }}
        @keyframes glow {{
            0%, 100% {{ opacity: 0.7; }}
            50% {{ opacity: 1; text-shadow: 0 0 30px {matrix_color}, 0 0 50px {matrix_color}; }}
        }}
        </style>
        
        <div class="matrix-message">
            ▓▒░ INITIALIZING CRE VALUATION MODEL ░▒▓<br/>
            <span style="font-size: 1.5rem;">█████████████ 100%</span>
        </div>
    """, unsafe_allow_html=True)
    
    time.sleep(3)  # Keep the cool animation
    st.session_state.show_matrix = False
    colors = ['#00ff00', '#ff0000', '#0000ff', '#ffff00', '#ff8800', '#aa00ff']
    st.session_state.matrix_color = random.choice(colors)
    st.rerun()

# ==================== MAIN APP ====================
st.markdown("""<style>.main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4;}</style>""", unsafe_allow_html=True)
st.markdown('<p class="main-header">🏢 CRE DCF Valuation Model</p>', unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    st.header("📂 Past Properties")
    
    all_deals = load_deals_from_file()
    
    if all_deals:
        for prop_type in ["Single Family", "Multifamily", "Office", "Retail"]:
            type_deals = get_deals_by_type(prop_type)
            
            if type_deals:
                with st.expander(f"{prop_type} ({len(type_deals)})", expanded=False):
                    for deal_name, deal_data in type_deals.items():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            if st.button(f"📄 {deal_name}", key=f"load_{deal_name}", use_container_width=True):
                                # Load all regular fields
                                for key, value in deal_data.items():
                                    if key not in ['saved_date', 'irr', 'equity_multiple', 'npv', 'going_in_cap', 'unit_rents']:
                                        st.session_state[f"{key}_input"] = value
                                
                                # Special handling for multifamily unit rents
                                if 'unit_rents' in deal_data and deal_data.get('property_type') == 'Multifamily':
                                    unit_rents_list = deal_data['unit_rents']
                                    for i, rent in enumerate(unit_rents_list):
                                        st.session_state[f'unit_{i}_rent_input'] = rent
                                
                                st.success(f"✅ Loaded: {deal_name}")
                                st.rerun()
                            
                            price = deal_data.get('purchase_price', 0)
                            size = deal_data.get('units', deal_data.get('square_feet', 0))
                            irr_val = deal_data.get('irr', 0)
                            st.caption(f"💰 ${price:,.0f} | 📏 {size} | 📈 {irr_val:.1f}% IRR")
                        
                        with col2:
                            if st.button("🗑️", key=f"del_{deal_name}"):
                                delete_deal_from_file(deal_name)
                                st.rerun()
    else:
        st.info("No saved properties yet!")
    
    st.markdown("---")
    st.header("📄 PDF Settings")
    
    pdf_theme = st.selectbox(
        "PDF Report Theme",
        options=list(PDF_THEMES.keys()),
        format_func=lambda x: PDF_THEMES[x]["name"],
        index=0,
        help="Choose color scheme for PDF reports",
        key='pdf_theme_select'
    )
    st.session_state.pdf_theme = pdf_theme
    
    # Show theme preview
    theme_colors = PDF_THEMES[pdf_theme]
    st.markdown(f"""
    <div style='padding: 10px; background: {theme_colors['primary']}; color: white; border-radius: 5px; text-align: center;'>
        <b>{theme_colors['name']}</b>
    </div>
    """, unsafe_allow_html=True)
    
    
    st.markdown("---")
    st.header("📋 Property Details")
    
    property_name = st.text_input("Property Name", value=st.session_state.get('property_name_input', 'Sample Property'), 
                                  help="Unique identifier for this deal (e.g., 'Sunset Apartments - Phoenix'). Used for saving and organizing multiple properties.",
                                  key='property_name_input')
    
    property_type = st.selectbox("Property Type", ["Single Family", "Multifamily", "Office", "Retail"], 
                                index=["Single Family", "Multifamily", "Office", "Retail"].index(st.session_state.get('property_type_input', 'Multifamily')),
                                help="Asset class determines calculation methods:\n• Single Family: 1 house, monthly rent\n• Multifamily: Multiple units (1-10), individual rents per unit\n• Office: Square footage (RSF), annual rent per SF\n• Retail: Square footage (GLA), annual rent per SF",
                                key='property_type_input')
    
    if property_type == "Single Family":
        st.info("Single Family: 1 House")
        units_or_sf = 1
        size_metric = "house"
    elif property_type == "Multifamily":
        units_or_sf = st.number_input("Number of Units (Max 10)", min_value=1, max_value=10, 
                                     value=min(st.session_state.get('units_input', 5), 10), step=1,
                                     help="Total apartment units in the building (max 10 for detailed analysis). Each unit can have different monthly rent. Used to calculate total rental income and operating expenses.",
                                     key='units_input')
        size_metric = "units"
    elif property_type == "Office":
        units_or_sf = st.number_input("Rentable Square Feet (RSF)", min_value=1, 
                                     value=st.session_state.get('square_feet_input', 10000), step=100,
                                     help="Total leasable office space excluding common areas, hallways, and building core. Used to calculate annual rent ($/SF/year) and operating expenses. Typical office: 10,000-50,000 SF.",
                                     key='square_feet_input')
        size_metric = "sf"
    else:
        units_or_sf = st.number_input("Gross Leasable Area (GLA in SF)", min_value=1, 
                                     value=st.session_state.get('square_feet_input', 8000), step=100,
                                     help="Total retail space available for tenant use, including sales floor and back rooms. Used to calculate annual rent ($/SF/year) and expenses. Excludes parking and common areas.",
                                     key='square_feet_input')
        size_metric = "sf"
    
    purchase_price = st.number_input("Purchase Price ($)", min_value=0, value=st.session_state.get('purchase_price_input', 20000000), 
                                    step=100000, format="%d",
                                    help="Total acquisition price agreed with seller (before closing costs). Used to calculate LTV, going-in cap rate, and price per unit/SF. Does NOT include closing costs.",
                                    key='purchase_price_input')
    
    closing_costs = st.number_input("Closing Costs ($)", min_value=0, value=st.session_state.get('closing_costs_input', 400000), 
                                   step=10000, format="%d",
                                   help="Transaction costs (typically 2-4% of purchase price). Includes: legal fees, title insurance, due diligence, lender fees, escrow fees. Added to purchase price to get Total Acquisition Cost.",
                                   key='closing_costs_input')
    
    st.markdown("---")
    st.header("💰 Operating Assumptions")
    
    unit_rents = []
    
    if property_type == "Single Family":
        st.subheader("Rental Income")
        monthly_rent = st.number_input("Monthly Rent ($)", min_value=0.0, 
                                      value=st.session_state.get('sf_rent_input', 2500.0), step=50.0,
                                      help="Current monthly rental income for the house. Will grow at the Annual Rent Growth rate each year. Market check: Compare to similar homes in area.",
                                      key='sf_rent_input')
        unit_rents = [monthly_rent]
        annual_rent_total = monthly_rent * 12
        
    elif property_type == "Multifamily":
        st.subheader("Rental Income per Unit")
        for i in range(units_or_sf):
            default_rent = st.session_state.get(f'unit_{i}_rent_input', 1500.0)
            rent = st.number_input(f"Unit {i+1} Monthly Rent ($)", min_value=0.0, 
                                 value=default_rent, step=50.0,
                                 help=f"Current monthly rent for Unit {i+1}. Each unit can have different rent based on size, floor level, finishes, and amenities. Rent will grow at Annual Rent Growth rate.",
                                 key=f'unit_{i}_rent_input')
            unit_rents.append(rent)
        total_monthly_rent = sum(unit_rents)
        annual_rent_total = total_monthly_rent * 12
        st.info(f"Total Monthly Rent: ${total_monthly_rent:,.2f}")
        
    elif property_type in ["Office", "Retail"]:
        st.subheader("Rental Income")
        rent_per_sf = st.number_input("Annual Rent per SF ($)", min_value=0.0, 
                                     value=st.session_state.get('rent_per_sf_input', 30.0), step=1.0,
                                     help="Market rent rate per square foot per YEAR (not monthly). Example: $30/SF/year = $2.50/SF/month. Typical: Class A Office $35-50/SF, Class B $25-35/SF, Retail (prime) $40-60/SF.",
                                     key='rent_per_sf_input')
        annual_rent_total = rent_per_sf * units_or_sf
    
    rent_growth = st.slider("Annual Rent Growth (%)", 0.0, 10.0, st.session_state.get('rent_growth_input', 3.0), 0.1,
                           help="Expected yearly percentage increase in rents. Typical: 2-3% matches inflation (conservative), 3-4% historical average, 4-5% strong markets, 5%+ aggressive. Applies to ALL units/space equally.",
                           key='rent_growth_input')
    
    vacancy = st.slider("Vacancy & Credit Loss (%)", 0.0, 20.0, st.session_state.get('vacancy_input', 5.0), 0.5,
                       help="Expected % of rental income lost to vacant units, tenant defaults, and turnover. Typical: Stabilized 3-5%, Value-add 5-10%, New construction 10-20%. Formula: EGI = Gross Rent × (1 - Vacancy%)",
                       key='vacancy_input')
    
    if property_type == "Single Family":
        opex_total = st.number_input("Operating Expenses per Year ($)", min_value=0, 
                                    value=st.session_state.get('opex_total_input', 5000), step=100,
                                    help="Total annual operating expenses for the house. Typical: $3,000-6,000/year. Includes property taxes, insurance, repairs, HOA fees, utilities (if landlord pays). Higher for older homes, pools, large lots.",
                                    key='opex_total_input')
        opex_per_unit_or_sf = opex_total
    elif property_type == "Multifamily":
        opex_per_unit_or_sf = st.number_input("Operating Expenses per Unit per Year ($)", min_value=0, 
                                             value=st.session_state.get('opex_per_unit_input', 6000), step=100,
                                             help="Annual cost to operate per unit. Typical: $5,000-8,000/unit/year. Includes property taxes, insurance, utilities, maintenance, landscaping. Does NOT include debt service, CapEx, or management fees.",
                                             key='opex_per_unit_input')
    else:
        opex_per_unit_or_sf = st.number_input("Operating Expenses per SF per Year ($)", min_value=0.0, 
                                             value=st.session_state.get('opex_per_sf_input', 12.0), step=0.5,
                                             help="Annual operating cost per square foot. Typical: Office $10-15/SF/year, Retail $8-12/SF/year. Full-service lease: Landlord pays all. NNN (triple-net): Tenant pays (recoverable).",
                                             key='opex_per_sf_input')
    
    opex_growth = st.slider("OpEx Growth Rate (%)", 0.0, 10.0, st.session_state.get('opex_growth_input', 3.0), 0.1,
                           help="Annual percentage increase in operating costs. Typically matches inflation: 2-3%/year standard, 3-4%/year high inflation. Property taxes often grow faster (4-5%) due to assessment increases.",
                           key='opex_growth_input')
    
    if property_type == "Single Family":
        capex_total = st.number_input("CapEx Reserve per Year ($)", min_value=0, 
                                     value=st.session_state.get('capex_total_input', 2000), step=100,
                                     help="Annual reserve for major repairs. Typical: $1,500-3,000/year. The '1% rule': Set aside 1% of property value annually. Covers: roof, HVAC, water heater, appliances. Higher for older homes (20+ years), pools.",
                                     key='capex_total_input')
        capex_per_unit_or_sf = capex_total
    elif property_type == "Multifamily":
        capex_per_unit_or_sf = st.number_input("CapEx Reserve per Unit per Year ($)", min_value=0, 
                                              value=st.session_state.get('capex_per_unit_input', 300), step=50,
                                              help="Annual reserve for major repairs & capital improvements per unit. Typical: $250-500/unit/year. Used for: roof (20-30yr), HVAC (15-20yr), appliances (8-12yr), parking lot, painting, renovations. Higher for older buildings.",
                                              key='capex_per_unit_input')
    else:
        capex_per_unit_or_sf = st.number_input("CapEx Reserve per SF per Year ($)", min_value=0.0, 
                                              value=st.session_state.get('capex_per_sf_input', 1.5), step=0.1,
                                              help="Annual reserve for capital improvements per SF. Typical: $1.00-2.50/SF/year. Used for: roof & structural, HVAC & mechanical, parking lot, facade, common area renovations. Tenant improvement (TI) costs handled separately.",
                                              key='capex_per_sf_input')
    
    management_fee = st.slider("Management Fee (% of EGI)", 0.0, 10.0, st.session_state.get('management_fee_input', 4.0), 0.5,
                              help="Property management fee as % of Effective Gross Income. Industry standard: Single Family 8-10%, Small Multifamily 6-8%, Large Multifamily 4-5%, Office/Retail 3-5%. Covers rent collection, maintenance, leasing, reporting. Self-managing? Set to 0%.",
                              key='management_fee_input')
    
    st.markdown("---")
    st.header("🏦 Debt Assumptions")
    
    loan_to_value = st.slider("Loan-to-Value (%)", 0.0, 90.0, st.session_state.get('loan_to_value_input', 70.0), 1.0,
                             help="Loan amount as % of purchase price. Higher LTV = More leverage = Higher returns (and risk). Typical: Aggressive 75-80%, Standard 65-75%, Conservative 50-65%. Set to 0% for all-cash (unlevered) analysis.",
                             key='loan_to_value_input')
    
    interest_rate = st.slider("Interest Rate (%)", 0.0, 15.0, st.session_state.get('interest_rate_input', 6.5), 0.1,
                             help="Annual interest rate on loan. Current rates (late 2024): Multifamily 6.0-7.0%, Office/Retail 6.5-7.5%, Single Family investment 7.0-8.5%. Lower for larger loans, stabilized properties, stronger borrowers.",
                             key='interest_rate_input')
    
    amortization = st.number_input("Amortization Period (Years)", min_value=0, value=st.session_state.get('amortization_input', 30), 
                                  step=1,
                                  help="Number of years to fully pay off loan. Common: 25 years (higher payments, less interest), 30 years (lower payments, more interest - most common), 20 years (aggressive paydown). Longer = Lower monthly payments = Higher cash flow.",
                                  key='amortization_input')
    
    io_period = st.number_input("Interest-Only Period (Years)", min_value=0, value=st.session_state.get('io_period_input', 0), 
                               step=1,
                               help="Years where you ONLY pay interest (no principal). During IO: Lower payments, higher cash flow, loan balance unchanged. After IO: Payments increase (principal+interest), loan begins amortizing. Common: 0 years (standard), 2-3 years (stabilization), 5 years (value-add).",
                               key='io_period_input')
    
    st.markdown("---")
    st.header("📈 Exit Assumptions")
    
    holding_period = st.slider("Holding Period (Years)", 1, 50, st.session_state.get('holding_period_input', 10), 1,
                              help="Years you plan to own before selling. Typical: 3-5 years (value-add/flip), 5-7 years (standard), 7-10 years (long-term), 10+ years (generational wealth). Affects total returns, loan paydown, taxes. IRR typically highest at 5-7 years for value-add.",
                              key='holding_period_input')
    
    exit_cap_rate = st.slider("Exit Cap Rate (%)", 0.0, 15.0, st.session_state.get('exit_cap_rate_input', 5.5), 0.1,
                             help="Projected cap rate when selling (Year N+1 NOI ÷ Sale Price). Typically: Exit cap = Going-in cap + 0.25-0.50%. Why higher? Property is older, conservative assumption, market cycles. Lower exit cap = Higher sale price (aggressive). Higher exit cap = Lower sale price (conservative).",
                             key='exit_cap_rate_input')
    
    selling_costs = st.slider("Selling Costs (%)", 0.0, 10.0, st.session_state.get('selling_costs_input', 2.0), 0.5,
                             help="Transaction costs to sell, as % of sale price. Typical: 1.5-3%. Includes: Broker commission (1-2%), legal fees (0.25-0.5%), title insurance (0.25-0.5%), closing costs (0.25-0.5%). Larger deals ($10M+): ~1.5%. Smaller deals (<$5M): ~2.5-3%.",
                             key='selling_costs_input')
    
    discount_rate = st.slider("Discount Rate for NPV (%)", 0.0, 25.0, st.session_state.get('discount_rate_input', 12.0), 0.5,
                             help="Your required annual return ('hurdle rate') for NPV calculation. Should reflect risk: Core 8-10%, Core-Plus 10-12%, Value-Add 12-15%, Opportunistic 15-18%. What 12% means: 'I need at least 12%/year return to invest'. NPV>0: Exceeds requirement. NPV<0: Doesn't meet requirement.",
                             key='discount_rate_input')
    
    st.markdown("---")
    st.header("💼 Tax Assumptions (Optional)")
    
    tax_rate = st.slider("Combined Tax Rate (%)", 0.0, 50.0, st.session_state.get('tax_rate_input', 0.0), 1.0,
                        help="Combined federal + state income tax rate. 0% = Tax-free entity (IRA, 401k, 1031 exchange). 25% = Moderate tax bracket. 35% = High earner. 40-50% = High earner in high-tax state (CA, NY, NJ). Used to calculate After-Tax Cash Flow.",
                        key='tax_rate_input')
    
    if tax_rate > 0:
        building_value_pct = st.slider("Building Value (% of Purchase Price)", 70.0, 90.0, 
                                      st.session_state.get('building_value_pct_input', 80.0), 1.0,
                                      help="Portion of purchase price that is building (depreciable). Land is NOT depreciable. Typical: 75-85%. Used for depreciation calculation: Residential 27.5 years, Commercial 39 years.",
                                      key='building_value_pct_input')

# ==================== CALCULATIONS ====================
total_acquisition = purchase_price + closing_costs
loan_amount = purchase_price * (loan_to_value / 100)
equity_required = total_acquisition - loan_amount

if size_metric in ["units", "house"]:
    price_per_unit = purchase_price / units_or_sf
else:
    price_per_sf = purchase_price / units_or_sf

# Year 1 NOI
if property_type in ["Single Family", "Multifamily"]:
    year_1_gri = annual_rent_total
else:
    year_1_gri = annual_rent_total

year_1_egi = year_1_gri * (1 - vacancy / 100)

if property_type == "Single Family":
    year_1_opex = opex_per_unit_or_sf
elif property_type == "Multifamily":
    year_1_opex = opex_per_unit_or_sf * units_or_sf
else:
    year_1_opex = opex_per_unit_or_sf * units_or_sf

year_1_mgmt = year_1_egi * (management_fee / 100)
year_1_noi = year_1_egi - year_1_opex - year_1_mgmt
going_in_cap = (year_1_noi / purchase_price) * 100 if purchase_price > 0 else 0

def calculate_debt_service(year, loan_amount, interest_rate, amortization, io_period):
    if year <= io_period or loan_amount == 0:
        return loan_amount * (interest_rate / 100)
    monthly_rate = interest_rate / 100 / 12
    remaining_payments = (amortization - io_period) * 12
    if remaining_payments <= 0:
        return 0
    monthly_pmt = loan_amount * (monthly_rate * (1 + monthly_rate)**remaining_payments) / ((1 + monthly_rate)**remaining_payments - 1)
    return monthly_pmt * 12

# Calculate depreciation if tax rate > 0
if tax_rate > 0:
    building_value = purchase_price * (building_value_pct / 100)
    if property_type in ["Single Family", "Multifamily"]:
        annual_depreciation = building_value / 27.5
    else:
        annual_depreciation = building_value / 39
else:
    annual_depreciation = 0

@st.cache_data(show_spinner=False)
def calculate_cash_flows(
    property_type, holding_period, unit_rents_tuple, annual_rent_total, 
    rent_growth, vacancy, opex_per_unit_or_sf, opex_growth, units_or_sf, management_fee,
    capex_per_unit_or_sf, loan_amount, interest_rate, amortization, io_period,
    equity_required, tax_rate, annual_depreciation
):
    """
    Cached cash flow calculation - only recalculates when inputs change
    Using tuple for unit_rents since lists aren't hashable for caching
    """
    # Convert tuple back to list for calculations
    unit_rents = list(unit_rents_tuple) if unit_rents_tuple else []
    
    # Track loan balance year by year
    current_loan_balance = loan_amount
    monthly_rate = interest_rate / 100 / 12 if interest_rate > 0 else 0
    
    cash_flow_data = []
    
    for year in range(1, holding_period + 1):
        if property_type in ["Single Family", "Multifamily"]:
            year_rents = [rent * (1 + rent_growth / 100) ** (year - 1) for rent in unit_rents]
            year_total_rent = sum(year_rents)
            gri = year_total_rent * 12
        else:
            gri = annual_rent_total * (1 + rent_growth / 100) ** (year - 1)
        
        egi = gri * (1 - vacancy / 100)
        
        if property_type == "Single Family":
            opex = opex_per_unit_or_sf * (1 + opex_growth / 100) ** (year - 1)
        elif property_type == "Multifamily":
            opex = opex_per_unit_or_sf * units_or_sf * (1 + opex_growth / 100) ** (year - 1)
        else:
            opex = opex_per_unit_or_sf * units_or_sf * (1 + opex_growth / 100) ** (year - 1)
        
        mgmt = egi * (management_fee / 100)
        
        if property_type == "Single Family":
            capex = capex_per_unit_or_sf
        elif property_type == "Multifamily":
            capex = capex_per_unit_or_sf * units_or_sf
        else:
            capex = capex_per_unit_or_sf * units_or_sf
        
        noi = egi - opex - mgmt
        ncf = noi - capex
        ds = calculate_debt_service(year, loan_amount, interest_rate, amortization, io_period)
        
        # Calculate interest expense
        if loan_amount == 0:
            interest_expense = 0
            principal_paid_this_year = 0
        elif year <= io_period:
            interest_expense = current_loan_balance * (interest_rate / 100)
            principal_paid_this_year = 0
        else:
            interest_expense = 0
            principal_paid_this_year = 0
            
            if amortization > io_period:
                remaining_payments = (amortization - io_period) * 12
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**remaining_payments) / ((1 + monthly_rate)**remaining_payments - 1)
                
                temp_balance = current_loan_balance
                for month in range(12):
                    monthly_interest = temp_balance * monthly_rate
                    monthly_principal = monthly_payment - monthly_interest
                    interest_expense += monthly_interest
                    principal_paid_this_year += monthly_principal
                    temp_balance -= monthly_principal
                
                current_loan_balance = temp_balance
        
        btcf = ncf - ds
        
        if tax_rate > 0:
            taxable_income = noi - interest_expense - annual_depreciation
            taxes = max(0, taxable_income * (tax_rate / 100))
            atcf = btcf - taxes
        else:
            atcf = btcf
            taxes = 0
        
        coc = (btcf / equity_required) * 100 if equity_required > 0 else 0
        
        cash_flow_data.append({
            'Year': year,
            'Gross Income': gri,
            'EGI': egi,
            'OpEx': opex,
            'Mgmt Fees': mgmt,
            'CapEx': capex,
            'NOI': noi,
            'Debt Service': ds,
            'BTCF': btcf,
            'Taxes': taxes if tax_rate > 0 else 0,
            'ATCF': atcf if tax_rate > 0 else btcf,
            'CoC Return %': coc
        })
    
    return pd.DataFrame(cash_flow_data)

# Call cached function - converts to tuple for hashability
cf_df = calculate_cash_flows(
    property_type, holding_period, tuple(unit_rents), annual_rent_total,
    rent_growth, vacancy, opex_per_unit_or_sf, opex_growth, units_or_sf, management_fee,
    capex_per_unit_or_sf, loan_amount, interest_rate, amortization, io_period,
    equity_required, tax_rate, annual_depreciation
)

# Track loan balance year by year for proper interest calculation
current_loan_balance = loan_amount
monthly_rate = interest_rate / 100 / 12 if interest_rate > 0 else 0

# Cash flow projection - NOW USING CACHED RESULTS
cash_flow_data = cf_df.to_dict('records')

cf_df = pd.DataFrame(cash_flow_data)

# Terminal analysis
final_noi = cf_df.iloc[-1]['NOI']
terminal_noi = final_noi * (1 + rent_growth / 100)
sale_price = terminal_noi / (exit_cap_rate / 100) if exit_cap_rate > 0 else 0
sale_costs = sale_price * (selling_costs / 100)

def calc_remaining_balance(loan_amount, interest_rate, amortization, io_period, holding_period):
    if holding_period <= io_period or loan_amount == 0:
        return loan_amount
    monthly_rate = interest_rate / 100 / 12
    total_pmts = (amortization - io_period) * 12
    remaining_pmts = (amortization - holding_period) * 12
    if remaining_pmts <= 0:
        return 0
    monthly_pmt = loan_amount * (monthly_rate * (1 + monthly_rate)**total_pmts) / ((1 + monthly_rate)**total_pmts - 1)
    return monthly_pmt * ((1 + monthly_rate)**remaining_pmts - 1) / (monthly_rate * (1 + monthly_rate)**remaining_pmts)

remaining_balance = calc_remaining_balance(loan_amount, interest_rate, amortization, io_period, holding_period)
net_sale_proceeds = sale_price - sale_costs - remaining_balance

# Returns
cash_flows = [-equity_required] + list(cf_df['ATCF'] if tax_rate > 0 else cf_df['BTCF'])
cash_flows[-1] += net_sale_proceeds

try:
    irr = npf.irr(cash_flows) * 100
except:
    irr = 0

npv = npf.npv(discount_rate / 100, cash_flows)
equity_multiple = (sum(cf_df['ATCF' if tax_rate > 0 else 'BTCF']) + net_sale_proceeds) / equity_required if equity_required > 0 else 0
avg_coc = cf_df['CoC Return %'].mean()

# ==================== METRICS (STAYS AT TOP) ====================
st.markdown("---")

# ==================== SAVE/EXPORT (PARALLEL BUTTONS) ====================
st.markdown("**Property Name:**")
save_col1, save_col2, save_col3, save_col4 = st.columns([2, 1, 1, 1.2])

with save_col1:
    save_name = st.text_input("", property_name, key="save_name", placeholder="Enter property name")

with save_col2:
    st.write("")
    st.write("")
    if st.button("💾 SAVE DEAL", use_container_width=True):
        deal_data = {
            'property_name': property_name,
            'property_type': property_type,
            'units': units_or_sf if size_metric in ["units", "house"] else None,
            'square_feet': units_or_sf if size_metric == "sf" else None,
            'purchase_price': purchase_price,
            'closing_costs': closing_costs,
            'rent_growth': rent_growth,
            'vacancy': vacancy,
            'opex_growth': opex_growth,
            'management_fee': management_fee,
            'loan_to_value': loan_to_value,
            'interest_rate': interest_rate,
            'amortization': amortization,
            'io_period': io_period,
            'holding_period': holding_period,
            'exit_cap_rate': exit_cap_rate,
            'selling_costs': selling_costs,
            'discount_rate': discount_rate,
            'irr': irr,
            'equity_multiple': equity_multiple,
            'npv': npv,
            'going_in_cap': going_in_cap
        }
        
        if property_type == "Single Family":
            deal_data['sf_rent'] = unit_rents[0]
            deal_data['opex_total'] = opex_per_unit_or_sf
            deal_data['capex_total'] = capex_per_unit_or_sf
        elif property_type == "Multifamily":
            deal_data['unit_rents'] = unit_rents
            deal_data['opex_per_unit'] = opex_per_unit_or_sf
            deal_data['capex_per_unit'] = capex_per_unit_or_sf
        else:
            deal_data['rent_per_sf'] = rent_per_sf if property_type in ["Office", "Retail"] else None
            deal_data['opex_per_sf'] = opex_per_unit_or_sf
            deal_data['capex_per_sf'] = capex_per_unit_or_sf
        
        save_deal_to_file(save_name, deal_data)
        st.success(f"✅ Saved: {save_name}")
        st.rerun()

with save_col3:
    st.write("")
    st.write("")
    csv = cf_df.to_csv(index=False)
    st.download_button("📥 Export CSV", csv, f"{property_name.replace(' ', '_')}_cashflow.csv", 
                      "text/csv", use_container_width=True)

with save_col4:
    st.write("")
    st.write("")
    if PDF_AVAILABLE:
        if st.button("📄 Generate PDF", use_container_width=True, help="Create professional PDF investment memo"):
            with st.spinner("Generating PDF report..."):
                # Prepare property data
                property_data = {
                    'property_name': property_name,
                    'property_type': property_type,
                    'purchase_price': purchase_price,
                    'closing_costs': closing_costs,
                    'equity_required': equity_required,
                    'loan_amount': loan_amount,
                    'loan_to_value': loan_to_value,
                    'interest_rate': interest_rate,
                    'amortization': amortization,
                    'io_period': io_period,
                    'holding_period': holding_period,
                    'exit_cap_rate': exit_cap_rate,
                    'selling_costs': selling_costs,
                    'discount_rate': discount_rate,
                    'rent_growth': rent_growth,
                    'vacancy': vacancy,
                    'opex_growth': opex_growth,
                    'management_fee': management_fee,
                    'irr': irr,
                    'equity_multiple': equity_multiple,
                    'npv': npv,
                    'going_in_cap': going_in_cap,
                    'avg_coc': avg_coc
                }
                
                # Generate PDF with theme and charts
                pdf_buffer = generate_pdf_report(
                    property_data, 
                    cf_df,
                    theme_key=st.session_state.get('pdf_theme', 'professional_blue'),
                    charts_dict=st.session_state.get('charts', {}),
                    loan_schedule_df=None
                )
                
                if pdf_buffer:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_buffer,
                        file_name=f"{property_name.replace(' ', '_')}_Investment_Memo.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF Generated Successfully!")
    else:
        st.button("📄 PDF Unavailable", disabled=True, use_container_width=True,
                 help="Install reportlab: pip install reportlab")

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

irr_help = f"""Levered IRR (Internal Rate of Return) using debt financing.

What's included:
• Initial equity: -${equity_required:,.0f}
• Annual cash flows (Years 1-{holding_period}): After debt service
• Sale proceeds (Year {holding_period}): After paying off loan

Interpretation:
• 8-12%: Solid (core properties)
• 12-15%: Good (stabilized with upside)
• 15-18%: Great (value-add deals)
• 18-20%: Excellent (heavy value-add)
• 20%+: Outstanding (opportunistic)

Compare to your discount rate ({discount_rate}%). If IRR > Discount Rate → Good deal!

To see UNLEVERED IRR: Set LTV to 0% (all cash)"""

col1.metric("💹 Levered IRR", f"{irr:.2f}%", "Internal Rate of Return", help=irr_help)

em_help = f"""Total cash returned ÷ Equity invested = For every $1 invested, how many dollars back?

Current deal:
• Invested: ${equity_required:,.0f}
• Total returned: ${sum(cf_df['ATCF' if tax_rate > 0 else 'BTCF']) + net_sale_proceeds:,.0f}
• Multiple: {equity_multiple:.2f}x

Interpretation:
• 1.0x = Break even
• 1.5x = Made 50% profit
• 2.0x = Doubled money
• 2.5x = Great return
• 3.0x+ = Excellent

Note: Doesn't account for time (use IRR for that)"""

col2.metric("📊 Equity Multiple", f"{equity_multiple:.2f}x", "Total Return Multiple", help=em_help)

npv_help = f"""How much the investment is worth TODAY after discounting future cash flows at {discount_rate}%.

At {discount_rate}% discount rate:
• NPV > 0: Worth MORE than you're paying ✓
• NPV = 0: Fair deal, meets return target
• NPV < 0: Doesn't meet requirements

This deal: ${npv:,.0f}
Meaning: Worth ${abs(npv):,.0f} {'more' if npv > 0 else 'less'} than your required {discount_rate}% return"""

col3.metric("💵 NPV", f"${npv:,.0f}", f"@ {discount_rate}% Discount", help=npv_help)

coc_help = f"""Average Cash-on-Cash return = Annual Cash Flow ÷ Equity Invested

Measures annual cash yield (like a dividend), ignoring appreciation.

Good CoC returns:
• 4-6%: Core/stable (bond-like)
• 6-8%: Core-plus
• 8-12%: Value-add
• 12%+: High risk/return

This deal: Averaging {avg_coc:.2f}% cash yield per year"""

col4.metric("📈 Avg CoC", f"{avg_coc:.2f}%", "Cash-on-Cash", help=coc_help)

st.markdown("---")

# ==================== DEAL SCORE & ANALYSIS ====================
st.header("🎯 Deal Score & Recommendation")

# Prepare metrics dict for scoring
metrics_for_score = {
    'irr': irr,
    'equity_multiple': equity_multiple,
    'npv': npv,
    'cap_rate': going_in_cap,
    'year1_coc': cf_df.iloc[0]['CoC Return %'] if len(cf_df) > 0 else 0,
    'avg_coc': avg_coc,
    'dscr': (cf_df.iloc[0]['NOI'] / (cf_df.iloc[0]['Debt Service'] if cf_df.iloc[0]['Debt Service'] > 0 else 1)) if len(cf_df) > 0 else 0
}

property_for_score = {
    'property_type': property_type,
    'equity_required': equity_required,
    'exit_cap_rate': exit_cap_rate,
    'loan_to_value': loan_to_value,
    'holding_period': holding_period
}

# Calculate score
total_score, score_breakdown, grade, rating = calculate_deal_score(metrics_for_score, property_for_score)

# Generate recommendation
recommendation = generate_recommendation(total_score, score_breakdown, metrics_for_score, property_for_score)

# Display Score Card
score_col1, score_col2, score_col3 = st.columns([2, 1, 1])

with score_col1:
    # Main score display
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; text-align: center;'>
        <h1 style='color: white; margin: 0; font-size: 3.5rem;'>{total_score:.1f}/100</h1>
        <p style='color: white; margin: 5px 0 0 0; font-size: 1.8rem;'>Grade: {grade}</p>
        <p style='color: white; margin: 5px 0 0 0; font-size: 1.2rem;'>{rating}</p>
    </div>
    """, unsafe_allow_html=True)

with score_col2:
    st.metric("Confidence", recommendation['confidence'], 
             help="How confident the algorithm is in this recommendation based on data quality and score consistency")

with score_col3:
    # Color code based on score
    if total_score >= 85:
        color = "🟢"
    elif total_score >= 70:
        color = "🟡"
    else:
        color = "🔴"
    st.markdown(f"### {color}")
    st.caption("Investment Signal")

st.markdown("---")

# Component Breakdown
st.subheader("📊 Score Breakdown by Category")

breakdown_cols = st.columns(5)
for idx, (category, data) in enumerate(score_breakdown.items()):
    with breakdown_cols[idx % 5]:
        score_pct = (data['score'] / data['max']) * 100
        
        # Progress bar color
        if score_pct >= 80:
            bar_color = "#10b981"  # Green
        elif score_pct >= 60:
            bar_color = "#f59e0b"  # Yellow
        else:
            bar_color = "#ef4444"  # Red
        
        st.markdown(f"""
        <div style='text-align: center; padding: 10px; background: #f8f9fa; border-radius: 10px; margin-bottom: 10px;'>
            <p style='margin: 0; font-size: 0.9rem; font-weight: bold; color: #1f2937;'>{category}</p>
            <h3 style='margin: 5px 0; color: {bar_color};'>{data['score']}/{data['max']}</h3>
            <div style='background: #e5e7eb; border-radius: 10px; overflow: hidden; height: 10px;'>
                <div style='background: {bar_color}; width: {score_pct}%; height: 100%;'></div>
            </div>
            <p style='margin: 5px 0 0 0; font-size: 0.8rem; color: #374151;'>{score_pct:.0f}%</p>
        </div>
        """, unsafe_allow_html=True)

# Scoring Logic Explanation
with st.expander("ℹ️ How is the Investment Score Calculated?"):
    st.markdown("""
    ### 📊 Scoring Methodology
    
    The **Investment Score** is an algorithmic assessment based on 5 key categories, each weighted differently based on importance to real estate investment performance:
    
    #### **1. Cash Flow Quality (30 points max)**
    - **What it measures:** Stability and strength of property cash flows
    - **Calculation:**
        - **Debt Service Coverage Ratio (DSCR):** 15 pts
            - 1.3+ = Full points (strong coverage)
            - 1.1-1.3 = Moderate points (acceptable)
            - <1.1 = Low points (weak coverage)
        - **Cash-on-Cash Return:** 15 pts
            - 10%+ = Full points (strong yield)
            - 7-10% = Moderate points (market rate)
            - <7% = Low points (below market)
    
    #### **2. Returns Profile (25 points max)**
    - **What it measures:** Total return potential and growth
    - **Calculation:**
        - **IRR (Internal Rate of Return):** 15 pts
            - 15%+ = Full points (excellent)
            - 10-15% = Moderate points (good)
            - <10% = Low points (below target)
        - **Equity Multiple:** 10 pts
            - 2.0x+ = Full points (strong appreciation)
            - 1.5-2.0x = Moderate points (decent growth)
            - <1.5x = Low points (minimal growth)
    
    #### **3. Risk Metrics (20 points max)**
    - **What it measures:** Downside protection and safety margins
    - **Calculation:**
        - **Loan-to-Value (LTV):** 10 pts
            - <70% = Full points (conservative)
            - 70-80% = Moderate points (standard)
            - >80% = Low points (aggressive)
        - **Break-Even Occupancy:** 10 pts
            - <70% = Full points (safe buffer)
            - 70-85% = Moderate points (thin margin)
            - >85% = Low points (risky)
    
    #### **4. Market Position (15 points max)**
    - **What it measures:** Pricing relative to market and cap rate spread
    - **Calculation:**
        - **Entry Cap Rate vs Exit Cap Rate:** 10 pts
            - Entry > Exit = Full points (buying below market)
            - Entry ≈ Exit = Moderate points (market rate)
            - Entry < Exit = Low points (premium pricing)
        - **Rent Growth Assumptions:** 5 pts
            - 2-4% = Full points (realistic)
            - 4-6% = Moderate points (optimistic)
            - >6% or <2% = Low points (extreme)
    
    #### **5. Structure Quality (10 points max)**
    - **What it measures:** Deal structure and financing efficiency
    - **Calculation:**
        - **Amortization Period:** 5 pts
            - 25-30 years = Full points (optimal)
            - 20-25 or interest-only = Moderate points
            - <20 years = Low points (accelerated paydown)
        - **Interest Rate:** 5 pts
            - <5% = Full points (low cost of debt)
            - 5-7% = Moderate points (market rate)
            - >7% = Low points (expensive debt)
    
    ---
    
    ### 🎯 Investment Grades
    
    Based on the **Total Score (0-100)**:
    
    | Score Range | Grade | Rating | Action |
    |------------|-------|--------|---------|
    | 85-100 | A+ | Excellent Deal | **Strong Buy** - Exceptional opportunity |
    | 70-84 | A/B+ | Good Deal | **Buy** - Solid fundamentals |
    | 60-69 | B/C+ | Fair Deal | **Consider** - Acceptable with caveats |
    | 50-59 | C | Below Average | **Pass** - Weak metrics |
    | 0-49 | D/F | Poor Deal | **Avoid** - High risk |
    
    ---
    
    ### 💡 How to Use This Score
    
    - **85+:** This is a home run deal with strong returns, low risk, and favorable structure
    - **70-84:** Solid investment that checks most boxes - proceed with standard due diligence
    - **60-69:** Marginal deal that may work in specific situations - requires deeper analysis
    - **<60:** Red flags present - likely not worth pursuing unless something changes
    
    **Remember:** This is a starting point for analysis, not a final decision. Always conduct thorough due diligence!
    """)

st.markdown("---")

# Recommendation Section
rec_col1, rec_col2 = st.columns([1, 1])

with rec_col1:
    st.subheader("💡 Algorithmic Recommendation")
    st.markdown(f"### {recommendation['action']}")
    st.write(recommendation['summary'])
    
    if recommendation['strengths']:
        st.markdown("**Key Strengths:**")
        for strength in recommendation['strengths']:
            st.markdown(f"- {strength}")

with rec_col2:
    if recommendation['risks']:
        st.markdown("**Potential Risks:**")
        for risk in recommendation['risks']:
            st.markdown(f"- {risk}")
    
    if recommendation['actions']:
        st.markdown("**Recommended Next Steps:**")
        for action in recommendation['actions']:
            st.markdown(f"- {action}")


# ==================== INVESTMENT SUMMARY ====================
st.subheader("📊 Investment Summary")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Acquisition**")
    st.write(f"Purchase Price: ${purchase_price:,.0f}")
    if property_type != "Single Family":
        if size_metric in ["units"]:
            st.write(f"Price per Unit: ${price_per_unit:,.0f}")
        else:
            st.write(f"Price per SF: ${price_per_sf:,.2f}")
    st.write(f"Closing Costs: ${closing_costs:,.0f}")
    st.write(f"**Total Acquisition: ${total_acquisition:,.0f}**")

with c2:
    st.markdown("**Capital Structure**")
    st.write(f"Loan Amount: ${loan_amount:,.0f}")
    st.write(f"LTV: {loan_to_value:.1f}%")
    st.write(f"Interest Rate: {interest_rate:.2f}%")
    st.write(f"**Equity Required: ${equity_required:,.0f}**")

with c3:
    st.markdown("**Returns**")
    st.write(f"Going-In Cap Rate: {going_in_cap:.2f}%")
    st.write(f"Exit Cap Rate: {exit_cap_rate:.2f}%")
    st.write(f"Exit Sale Price: ${sale_price:,.0f}")
    
    st.markdown(f"**Net Sale Proceeds: ${net_sale_proceeds:,.0f}**")
    
    with st.expander("ℹ️ How is Net Sale Proceeds calculated?"):
        st.markdown(f"""
**Net Sale Proceeds Calculation:**

**[1] Sale Price:** ${sale_price:,.0f}  
(Year {holding_period+1} NOI ÷ Exit Cap Rate)

**[2] - Selling Costs ({selling_costs}%):** -${sale_costs:,.0f}

**[3] - Remaining Loan Balance:** -${remaining_balance:,.0f}

**[4] = Net Proceeds to YOU:** ${net_sale_proceeds:,.0f}

This is the cash you walk away with at closing. Added to Year {holding_period} cash flow for IRR calculation.
        """)

st.markdown("---")

# ==================== LOAN PAYMENT SUMMARY ====================
if loan_amount > 0:
    st.subheader("📊 Loan Payment Summary")
    
    # Calculate monthly payments
    monthly_rate = interest_rate / 100 / 12
    
    if io_period > 0:
        monthly_payment_io = loan_amount * monthly_rate
    else:
        monthly_payment_io = 0
    
    if amortization > io_period:
        remaining_payments = (amortization - io_period) * 12
        monthly_payment_amort = loan_amount * (monthly_rate * (1 + monthly_rate)**remaining_payments) / ((1 + monthly_rate)**remaining_payments - 1) if monthly_rate > 0 else 0
    else:
        monthly_payment_amort = 0
    
    # Calculate total paid and principal paid
    balance = loan_amount
    total_paid_at_holding = 0
    principal_paid_at_holding = 0
    total_paid_full_term = 0
    
    for year in range(1, amortization + 1):
        if year <= io_period:
            annual_payment = loan_amount * (interest_rate / 100)
            principal_this_year = 0
        else:
            annual_interest = 0
            annual_principal = 0
            for month in range(12):
                interest = balance * monthly_rate
                principal = monthly_payment_amort - interest
                balance -= principal
                annual_interest += interest
                annual_principal += principal
            annual_payment = annual_interest + annual_principal
            principal_this_year = annual_principal
        
        total_paid_full_term += annual_payment
        
        if year <= holding_period:
            total_paid_at_holding += annual_payment
            principal_paid_at_holding += principal_this_year
    
    sum_col1, sum_col2, sum_col3 = st.columns(3)
    
    with sum_col1:
        if io_period > 0:
            st.metric("Monthly Payment (IO Period)", f"${monthly_payment_io:,.2f}")
            st.metric("Monthly Payment (Amortizing)", f"${monthly_payment_amort:,.2f}")
        else:
            st.metric("Monthly Payment", f"${monthly_payment_amort:,.2f}")
    
    # Calculate interest paid at holding period
    interest_paid_at_holding = total_paid_at_holding - principal_paid_at_holding
    
    with sum_col2:
        st.metric(f"Total Paid (Year {holding_period})", f"${total_paid_at_holding:,.0f}")
        st.metric(f"Principal Paid (Year {holding_period})", f"${principal_paid_at_holding:,.0f}")
        st.metric(f"Interest Paid (Year {holding_period})", f"${interest_paid_at_holding:,.0f}")
    
    with sum_col3:
        st.metric(f"Total if Held {amortization} Years", f"${total_paid_full_term:,.0f}")
        st.metric(f"Total Interest Paid ({amortization} Years)", f"${total_paid_full_term - loan_amount:,.0f}")

    st.markdown("---")

# ==================== LOAN PAYOFF VISUALIZATION ====================
if loan_amount > 0:
    st.subheader("🏦 Loan Payoff Schedule")
    
    # Generate amortization schedule
    amort_schedule = []
    balance = loan_amount
    monthly_rate = interest_rate / 100 / 12
    
    if io_period > 0:
        monthly_payment_io = loan_amount * monthly_rate
    else:
        monthly_payment_io = 0
    
    if amortization > io_period:
        remaining_payments = (amortization - io_period) * 12
        monthly_payment_amort = loan_amount * (monthly_rate * (1 + monthly_rate)**remaining_payments) / ((1 + monthly_rate)**remaining_payments - 1) if monthly_rate > 0 else 0
    else:
        monthly_payment_amort = 0
    
    for year in range(1, amortization + 1):
        if year <= io_period:
            interest_paid = loan_amount * (interest_rate / 100)
            principal_paid = 0
            annual_payment = interest_paid
        else:
            year_interest = 0
            year_principal = 0
            for month in range(12):
                interest = balance * monthly_rate
                principal = monthly_payment_amort - interest
                balance = max(0, balance - principal)
                year_interest += interest
                year_principal += principal
            annual_payment = year_interest + year_principal
            interest_paid = year_interest
            principal_paid = year_principal
        
        amort_schedule.append({
            'Year': year,
            'Annual Payment': annual_payment,
            'Principal': principal_paid,
            'Interest': interest_paid,
            'Remaining Balance': max(0, balance)
        })
    
    amort_df = pd.DataFrame(amort_schedule)
    
    # Line graph
    fig_loan = go.Figure()
    
    fig_loan.add_trace(go.Scatter(
        x=amort_df['Year'],
        y=amort_df['Remaining Balance'],
        mode='lines',
        name='Loan Balance',
        line=dict(color='#1f77b4', width=3),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)'
    ))
    
    # Add vertical line at holding period
    fig_loan.add_vline(
        x=holding_period,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"Holding Period: {holding_period} years",
        annotation_position="top"
    )
    
    fig_loan.update_layout(
        title='Loan Balance Over Time',
        xaxis_title='Year',
        yaxis_title='Remaining Balance ($)',
        height=400,
        showlegend=False,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_loan, use_container_width=True)
    save_chart_to_session("Loan Balance Over Time", fig_loan)

st.markdown("---")

# ==================== CASH FLOW TABLE ====================
st.subheader(f"📋 {holding_period}-Year Cash Flow Projection")

display_df = cf_df.copy()
for col in ['Gross Income', 'EGI', 'OpEx', 'Mgmt Fees', 'CapEx', 'NOI', 'Debt Service', 'BTCF', 'Taxes', 'ATCF']:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
display_df['CoC Return %'] = display_df['CoC Return %'].apply(lambda x: f"{x:.2f}%")

if tax_rate == 0:
    display_df = display_df.drop(columns=['Taxes', 'ATCF'], errors='ignore')

st.dataframe(display_df, use_container_width=True, height=400)

st.markdown("---")

# ==================== VISUALIZATIONS ====================
st.subheader("📈 Visualizations")
chart1, chart2 = st.columns(2)

with chart1:
    fig_noi = go.Figure(go.Bar(x=cf_df['Year'], y=cf_df['NOI'], marker_color='#1f77b4'))
    fig_noi.update_layout(title='NOI Growth Over Time', xaxis_title='Year', yaxis_title='NOI ($)', height=400, showlegend=False)
    st.plotly_chart(fig_noi, use_container_width=True)
    save_chart_to_session("NOI Growth Over Time", fig_noi)

with chart2:
    cash_flow_col = 'ATCF' if tax_rate > 0 else 'BTCF'
    title_text = 'After-Tax Cash Flow' if tax_rate > 0 else 'Before-Tax Cash Flow'
    fig_cf = go.Figure(go.Scatter(x=cf_df['Year'], y=cf_df[cash_flow_col], mode='lines+markers', 
                                  line=dict(color='#2ca02c', width=3), marker=dict(size=8)))
    fig_cf.update_layout(title=title_text, xaxis_title='Year', yaxis_title='Cash Flow ($)', height=400, showlegend=False)
    st.plotly_chart(fig_cf, use_container_width=True)
    save_chart_to_session(f"{title_text}", fig_cf)

st.markdown("---")

st.markdown("---")

# ==================== SENSITIVITY ANALYSIS ====================
st.header("📊 Sensitivity Analysis")

st.info("""
**What is Sensitivity Analysis?** Test how changes in key assumptions affect your returns. 
This helps you understand deal risk and identify which variables matter most for due diligence.
""")

# Create tabs
tab1, tab2, tab3 = st.tabs(["🔥 Two-Way Analysis", "📈 One-Way Analysis", "🌪️ Tornado Chart"])

# Variable options (ordered by importance)
sensitivity_vars = [
    "Exit Cap Rate",
    "Rent Growth Rate", 
    "Interest Rate",
    "Vacancy Rate",
    "OpEx Growth Rate"
]

# ==================== TAB 1: TWO-WAY SENSITIVITY ====================
with tab1:
    st.subheader("🔥 Two-Way Sensitivity Heat Map")
    
    with st.expander("📖 What is Two-Way Sensitivity Analysis?"):
        st.markdown("""
**How it works:** Tests TWO variables at once to see how they interact and affect returns.

**When to use:**
- Understanding how multiple risks compound together
- Identifying "safe zones" where your deal still works
- Presenting risk scenarios to investors

**How to read the heat map:**
- 🟢 Green = Strong returns (deal works well)
- 🟡 Yellow = Acceptable returns  
- 🔴 Red = Weak returns (deal at risk)

**Pro tip:** Pick the two variables you're MOST uncertain about!
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        var1 = st.selectbox(
            "Variable 1 (Y-Axis)",
            sensitivity_vars,
            help="Variable shown on rows",
            key="two_var1"
        )
    
    with col2:
        var2_options = [v for v in sensitivity_vars if v != var1]
        var2 = st.selectbox(
            "Variable 2 (X-Axis)",
            var2_options,
            help="Variable shown on columns",
            key="two_var2"
        )
    
    metric_choice = st.selectbox(
        "Metric to Display",
        ["IRR (%)", "NPV ($)", "Equity Multiple (x)"],
        help="Which return metric to analyze",
        key="two_metric"
    )
    
    if st.button("🔥 Generate Heat Map", use_container_width=True):
        with st.spinner("Calculating all scenarios..."):
            
            # Define ranges for each variable
            var_ranges = {
                "Exit Cap Rate": np.linspace(max(3.0, exit_cap_rate - 1.5), min(9.0, exit_cap_rate + 1.5), 7),
                "Rent Growth Rate": np.linspace(max(0, rent_growth - 2.0), min(6.0, rent_growth + 2.0), 7),
                "Interest Rate": np.linspace(max(2.0, interest_rate - 2.0), min(10.0, interest_rate + 2.0), 7),
                "Vacancy Rate": np.linspace(max(0, vacancy - 3.0), min(15.0, vacancy + 3.0), 7),
                "OpEx Growth Rate": np.linspace(max(0, opex_growth - 2.0), min(6.0, opex_growth + 2.0), 7)
            }
            
            var1_range = var_ranges[var1]
            var2_range = var_ranges[var2]
            
            # Create results matrix
            heat_results = np.zeros((len(var1_range), len(var2_range)))
            
            # Precompute base values that don't change
            monthly_rate = interest_rate / 100 / 12
            
            # Calculate for each combination (optimized)
            for i, val1 in enumerate(var1_range):
                for j, val2 in enumerate(var2_range):
                    # Set up modified parameters
                    test_rent_gr = rent_growth if var1 != "Rent Growth Rate" and var2 != "Rent Growth Rate" else (val1 if var1 == "Rent Growth Rate" else val2)
                    test_vac = vacancy if var1 != "Vacancy Rate" and var2 != "Vacancy Rate" else (val1 if var1 == "Vacancy Rate" else val2)
                    test_opex_gr = opex_growth if var1 != "OpEx Growth Rate" and var2 != "OpEx Growth Rate" else (val1 if var1 == "OpEx Growth Rate" else val2)
                    test_exit = exit_cap_rate if var1 != "Exit Cap Rate" and var2 != "Exit Cap Rate" else (val1 if var1 == "Exit Cap Rate" else val2)
                    test_int = interest_rate if var1 != "Interest Rate" and var2 != "Interest Rate" else (val1 if var1 == "Interest Rate" else val2)
                    
                    # Vectorized cash flow calculation
                    years = np.arange(1, holding_period + 1)
                    noi_values = year_1_noi * ((1 + test_rent_gr / 100) ** (years - 1))
                    
                    # Calculate CapEx for each year (doesn't change with tested variables)
                    if property_type == "Single Family":
                        capex_annual = capex_per_unit_or_sf
                    elif property_type == "Multifamily":
                        capex_annual = capex_per_unit_or_sf * units_or_sf
                    else:
                        capex_annual = capex_per_unit_or_sf * units_or_sf
                    
                    # Calculate debt service (simplified for speed)
                    if test_int != interest_rate:
                        test_monthly_rate = test_int / 100 / 12
                        remaining_payments = (amortization - io_period) * 12
                        temp_annual_ds = 12 * loan_amount * (test_monthly_rate * (1 + test_monthly_rate)**remaining_payments) / ((1 + test_monthly_rate)**remaining_payments - 1) if amortization > io_period else loan_amount * test_int / 100
                    else:
                        temp_annual_ds = calculate_debt_service(1, loan_amount, test_int, amortization, io_period)
                    
                    # Cash flows: NCF = NOI - CapEx, then BTCF = NCF - Debt Service
                    ncf_values = noi_values - capex_annual
                    temp_cf_list = ncf_values - temp_annual_ds
                    
                    # Sale calculation
                    final_noi = year_1_noi * ((1 + test_rent_gr / 100) ** holding_period)
                    temp_sale = final_noi / (test_exit / 100)
                    temp_proceeds = temp_sale * 0.94 - remaining_balance
                    
                    # Calculate metric
                    flows = np.concatenate([[-equity_required], temp_cf_list])
                    flows[-1] += temp_proceeds
                    
                    try:
                        if "IRR" in metric_choice:
                            result = npf.irr(flows) * 100
                        elif "NPV" in metric_choice:
                            result = npf.npv(discount_rate / 100, flows)
                        else:  # Equity Multiple
                            result = (np.sum(temp_cf_list) + temp_proceeds) / equity_required
                    except:
                        result = 0
                    
                    heat_results[i, j] = result
            
            # Create heat map
            fig_heat = go.Figure(data=go.Heatmap(
                z=heat_results,
                x=[f"{v:.2f}" for v in var2_range],
                y=[f"{v:.2f}" for v in var1_range],
                colorscale=[
                    [0, "#d73027"],
                    [0.35, "#fee08b"],
                    [0.65, "#d9ef8b"],
                    [1, "#1a9850"]
                ],
                text=np.round(heat_results, 1),
                texttemplate='%{text}',
                textfont={"size": 9},
                colorbar=dict(title=metric_choice.split("(")[0])
            ))
            
            fig_heat.update_layout(
                title=f'{metric_choice}: {var1} vs {var2}',
                xaxis_title=f'{var2} (%)',
                yaxis_title=f'{var1} (%)',
                height=550
            )
            
            st.plotly_chart(fig_heat, use_container_width=True)
            save_chart_to_session(f"Two-Way Sensitivity: {var1} vs {var2}", fig_heat)
            
            # Key stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Best Case", f"{heat_results.max():.2f}")
            col2.metric("Your Base", f"{heat_results[len(var1_range)//2, len(var2_range)//2]:.2f}")
            col3.metric("Worst Case", f"{heat_results.min():.2f}")
            
            with st.expander("💡 How to Read This"):
                st.markdown(f"""
**Key Insights:**
- Each cell shows {metric_choice} for that combination of {var1} and {var2}
- Your base case is near the center of the map
- Green zones = Deal works well even if assumptions change
- Red zones = Deal breaks down - avoid these scenarios!

**Action:** Focus due diligence on the top 2 variables tested here.
                """)

# ==================== TAB 2: ONE-WAY SENSITIVITY ====================
with tab2:
    st.subheader("📈 One-Way Sensitivity Analysis")
    
    with st.expander("📖 What is One-Way Sensitivity Analysis?"):
        st.markdown("""
**How it works:** Changes ONE variable at a time while keeping everything else constant.

**When to use:**
- Finding which single variable matters MOST
- Testing specific "what if" scenarios
- Prioritizing due diligence efforts

**How to read:**
- Steep line = Highly sensitive (big impact!)
- Flat line = Not sensitive (doesn't matter much)

**Pro tip:** Test all your key variables to see which ones actually matter!
        """)
    
    test_var = st.selectbox(
        "Select Variable to Test",
        sensitivity_vars,
        help="Pick ONE variable to analyze",
        key="one_var"
    )
    
    one_metric = st.selectbox(
        "Metric to Analyze",
        ["IRR (%)", "NPV ($)", "Equity Multiple (x)"],
        key="one_metric"
    )
    
    if st.button("📈 Run Analysis", use_container_width=True):
        with st.spinner("Analyzing..."):
            
            # Define test range
            if test_var == "Exit Cap Rate":
                test_range = np.linspace(max(3.0, exit_cap_rate - 2.0), min(9.0, exit_cap_rate + 2.0), 13)
                base_val = exit_cap_rate
            elif test_var == "Rent Growth Rate":
                test_range = np.linspace(max(0, rent_growth - 2.5), min(6.0, rent_growth + 2.5), 13)
                base_val = rent_growth
            elif test_var == "Interest Rate":
                test_range = np.linspace(max(2.0, interest_rate - 2.5), min(10.0, interest_rate + 2.5), 13)
                base_val = interest_rate
            elif test_var == "Vacancy Rate":
                test_range = np.linspace(max(0, vacancy - 4.0), min(15.0, vacancy + 4.0), 13)
                base_val = vacancy
            else:  # OpEx Growth
                test_range = np.linspace(max(0, opex_growth - 2.5), min(6.0, opex_growth + 2.5), 13)
                base_val = opex_growth
            
            one_results = []
            
            for test_val in test_range:
                # Quick calculation with modified variable
                temp_noi = year_1_noi
                temp_cf_list = []
                
                test_rent_gr = rent_growth if test_var != "Rent Growth Rate" else test_val
                test_vac = vacancy if test_var != "Vacancy Rate" else test_val
                test_opex_gr = opex_growth if test_var != "OpEx Growth Rate" else test_val
                test_exit = exit_cap_rate if test_var != "Exit Cap Rate" else test_val
                test_int = interest_rate if test_var != "Interest Rate" else test_val
                
                # Vectorized NOI calculation
                years = np.arange(1, holding_period + 1)
                noi_values = year_1_noi * ((1 + test_rent_gr / 100) ** (years - 1))
                
                # Calculate CapEx
                if property_type == "Single Family":
                    capex_annual = capex_per_unit_or_sf
                elif property_type == "Multifamily":
                    capex_annual = capex_per_unit_or_sf * units_or_sf
                else:
                    capex_annual = capex_per_unit_or_sf * units_or_sf
                
                # Calculate debt service once
                temp_annual_ds = calculate_debt_service(1, loan_amount, test_int, amortization, io_period)
                
                # Cash flows: NCF = NOI - CapEx, then BTCF = NCF - Debt Service
                ncf_values = noi_values - capex_annual
                temp_cf_list = ncf_values - temp_annual_ds
                
                final_noi = year_1_noi * ((1 + test_rent_gr / 100) ** holding_period)
                temp_sale = final_noi / (test_exit / 100)
                temp_proceeds = temp_sale * 0.94 - remaining_balance
                
                flows = np.concatenate([[-equity_required], temp_cf_list])
                flows[-1] += temp_proceeds
                
                try:
                    if "IRR" in one_metric:
                        result = npf.irr(flows) * 100
                    elif "NPV" in one_metric:
                        result = npf.npv(discount_rate / 100, flows)
                    else:
                        result = (np.sum(temp_cf_list) + temp_proceeds) / equity_required
                except:
                    result = 0
                
                one_results.append(result)
            
            # Create line chart
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=test_range,
                y=one_results,
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig_line.add_vline(x=base_val, line_dash="dash", line_color="red", annotation_text="Base Case")
            
            fig_line.update_layout(
                title=f'{one_metric} Sensitivity to {test_var}',
                xaxis_title=f'{test_var} (%)',
                yaxis_title=one_metric,
                height=450
            )
            
            st.plotly_chart(fig_line, use_container_width=True)
            save_chart_to_session(f"One-Way Sensitivity: {test_var}", fig_line)
            
            # Stats
            base_idx = np.argmin(np.abs(test_range - base_val))
            col1, col2, col3 = st.columns(3)
            col1.metric("Base Case", f"{one_results[base_idx]:.2f}")
            col2.metric("Best Case", f"{max(one_results):.2f}")
            col3.metric("Worst Case", f"{min(one_results):.2f}")
            
            # Calculate sensitivity
            slope = (one_results[-1] - one_results[0]) / (test_range[-1] - test_range[0])
            sensitivity_level = "HIGH" if abs(slope) > 1.5 else "MODERATE" if abs(slope) > 0.5 else "LOW"
            
            st.info(f"**Sensitivity Level: {sensitivity_level}** - " + 
                   ("Focus heavy due diligence here!" if sensitivity_level == "HIGH" else 
                    "Standard diligence recommended" if sensitivity_level == "MODERATE" else
                    "Low priority - use industry averages"))

# ==================== TAB 3: TORNADO CHART ====================
with tab3:
    st.subheader("🌪️ Tornado Chart - Variable Ranking")
    
    with st.expander("📖 What is a Tornado Chart?"):
        st.markdown("""
**How it works:** Tests ALL variables automatically and ranks them by impact.

**When to use:**
- Prioritizing what to focus on in due diligence
- Understanding overall deal risk
- Comparing multiple deals

**How to read:**
- Widest bar = Most important variable (focus here!)
- Narrowest bar = Least important (use defaults)
- Shows ±20% change impact for each variable

**Pro tip:** Spend 80% of your time on the top 3 variables!
        """)
    
    tornado_metric = st.selectbox(
        "Metric to Test",
        ["IRR (%)", "NPV ($)", "Equity Multiple (x)"],
        key="tornado_metric"
    )
    
    if st.button("🌪️ Generate Tornado Chart", use_container_width=True):
        with st.spinner("Testing all variables..."):
            
            tornado_data = []
            
            # Test each variable at ±20%
            for var_name in sensitivity_vars:
                if var_name == "Exit Cap Rate": base_val = exit_cap_rate
                elif var_name == "Rent Growth Rate": base_val = rent_growth
                elif var_name == "Interest Rate": base_val = interest_rate
                elif var_name == "Vacancy Rate": base_val = vacancy
                else: base_val = opex_growth
                
                low_val = base_val * 0.8
                high_val = base_val * 1.2
                
                var_results = []
                
                for test_val in [low_val, high_val]:
                    # Quick calc
                    temp_noi = year_1_noi
                    
                    test_params = {
                        "rent_gr": rent_growth,
                        "vac": vacancy,
                        "opex_gr": opex_growth,
                        "exit_cap": exit_cap_rate
                    }
                    
                    if var_name == "Rent Growth Rate": test_params["rent_gr"] = test_val
                    elif var_name == "Vacancy Rate": test_params["vac"] = test_val
                    elif var_name == "OpEx Growth Rate": test_params["opex_gr"] = test_val
                    elif var_name == "Exit Cap Rate": test_params["exit_cap"] = test_val
                    
                    for yr in range(holding_period):
                        temp_noi *= (1 + test_params["rent_gr"] / 100)
                    
                    temp_sale = temp_noi / (test_params["exit_cap"] / 100)
                    simple_return = (temp_sale * 0.94 - equity_required) / equity_required
                    
                    var_results.append(simple_return * 100)
                
                tornado_data.append({
                    "variable": var_name,
                    "low": var_results[0],
                    "high": var_results[1],
                    "range": abs(var_results[1] - var_results[0])
                })
            
            # Sort by range
            tornado_data.sort(key=lambda x: x["range"], reverse=True)
            
            # Create chart
            fig_tornado = go.Figure()
            
            for item in tornado_data:
                # Low bar
                fig_tornado.add_trace(go.Bar(
                    y=[item["variable"]],
                    x=[item["low"]],
                    orientation='h',
                    marker=dict(color='#d73027'),
                    name='Pessimistic',
                    showlegend=False
                ))
                # High bar
                fig_tornado.add_trace(go.Bar(
                    y=[item["variable"]],
                    x=[item["high"]],
                    orientation='h',
                    marker=dict(color='#1a9850'),
                    name='Optimistic',
                    showlegend=False
                ))
            
            fig_tornado.update_layout(
                title='Variable Impact on Returns (±20% Test)',
                xaxis_title='Return Impact',
                barmode='overlay',
                height=400
            )
            
            st.plotly_chart(fig_tornado, use_container_width=True)
            save_chart_to_session("Tornado Chart - Variable Importance", fig_tornado)
            
            # Key insights
            st.success("✅ Analysis Complete!")
            
            col1, col2 = st.columns(2)
            col1.metric("Most Critical", tornado_data[0]["variable"], f"±{tornado_data[0]['range']/2:.1f}%")
            col2.metric("Least Critical", tornado_data[-1]["variable"], f"±{tornado_data[-1]['range']/2:.1f}%")
            
            st.info(f"""
**Action Plan:**
1. **{tornado_data[0]["variable"]}** - Highest priority! Get multiple expert opinions.
2. **{tornado_data[1]["variable"]}** - Important. Do thorough market research.
3. **{tornado_data[2]["variable"]}** - Standard diligence.
4. **{tornado_data[-1]["variable"]}** - Low priority. Use industry averages.
            """)

# ==================== DEAL COMPARISON ====================
st.markdown("---")
st.header("📊 Deal Comparison Dashboard")
st.markdown("Compare up to 3 saved deals side-by-side to identify the best investment opportunity")

all_deals_for_comparison = load_deals_from_file()

if len(all_deals_for_comparison) < 2:
    st.info("💡 Save at least 2 deals to use the comparison feature!")
else:
    # Deal selection
    st.subheader("Select Deals to Compare")
    
    compare_col1, compare_col2, compare_col3 = st.columns(3)
    
    deal_names = list(all_deals_for_comparison.keys())
    
    with compare_col1:
        deal1_name = st.selectbox("Deal 1", ["None"] + deal_names, key="compare_deal1")
    
    with compare_col2:
        deal2_name = st.selectbox("Deal 2", ["None"] + deal_names, key="compare_deal2")
    
    with compare_col3:
        deal3_name = st.selectbox("Deal 3 (Optional)", ["None"] + deal_names, key="compare_deal3")
    
    selected_deals = []
    selected_names = []
    
    if deal1_name != "None":
        selected_deals.append(all_deals_for_comparison[deal1_name])
        selected_names.append(deal1_name)
    if deal2_name != "None":
        selected_deals.append(all_deals_for_comparison[deal2_name])
        selected_names.append(deal2_name)
    if deal3_name != "None":
        selected_deals.append(all_deals_for_comparison[deal3_name])
        selected_names.append(deal3_name)
    
    if len(selected_deals) >= 2:
        if st.button("🔍 Compare Selected Deals", use_container_width=True, type="primary"):
            st.markdown("---")
            st.subheader("📊 Comparison Results")
            
            # Create comparison table
            comparison_data = {
                'Metric': [
                    'Property Type',
                    'Purchase Price',
                    'Equity Required',
                    'Levered IRR (%)',
                    'Equity Multiple (x)',
                    'NPV ($)',
                    'Going-In Cap (%)',
                    'Exit Cap (%)',
                    'Holding Period (yrs)',
                    'LTV (%)'
                ]
            }
            
            # Calculate scores for each deal
            deal_scores = []
            
            for deal_name, deal_data in zip(selected_names, selected_deals):
                # Prepare metrics for scoring
                equity_calc = deal_data.get('purchase_price', 0) - (deal_data.get('purchase_price', 0) * (deal_data.get('loan_to_value', 0) / 100))
                
                deal_metrics = {
                    'irr': deal_data.get('irr', 0),
                    'equity_multiple': deal_data.get('equity_multiple', 1),
                    'npv': deal_data.get('npv', 0),
                    'cap_rate': deal_data.get('going_in_cap', 0),
                    'year1_coc': deal_data.get('irr', 0) / 2,
                    'avg_coc': deal_data.get('irr', 0) / 1.5,
                    'dscr': 1.3
                }
                
                deal_property_data = {
                    'property_type': deal_data.get('property_type', 'Unknown'),
                    'equity_required': equity_calc,
                    'exit_cap_rate': deal_data.get('exit_cap_rate', 0),
                    'loan_to_value': deal_data.get('loan_to_value', 0),
                    'holding_period': deal_data.get('holding_period', 10)
                }
                
                score, breakdown, grade, rating = calculate_deal_score(deal_metrics, deal_property_data)
                deal_scores.append({'score': score, 'grade': grade, 'rating': rating})
                
                # Add column for this deal
                comparison_data[deal_name] = [
                    deal_data.get('property_type', 'N/A'),
                    f"${deal_data.get('purchase_price', 0):,.0f}",
                    f"${equity_calc:,.0f}",
                    f"{deal_data.get('irr', 0):.2f}%",
                    f"{deal_data.get('equity_multiple', 0):.2f}x",
                    f"${deal_data.get('npv', 0):,.0f}",
                    f"{deal_data.get('going_in_cap', 0):.2f}%",
                    f"{deal_data.get('exit_cap_rate', 0):.2f}%",
                    deal_data.get('holding_period', 'N/A'),
                    f"{deal_data.get('loan_to_value', 0):.1f}%"
                ]
            
            # Display comparison table
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, height=420)
            
            st.markdown("---")
            
            # Display deal scores
            st.subheader("🎯 Deal Scores & Rankings")
            
            score_cols = st.columns(len(selected_deals))
            
            # Find best deal
            best_idx = max(range(len(deal_scores)), key=lambda i: deal_scores[i]['score'])
            
            for idx, (deal_name, score_data) in enumerate(zip(selected_names, deal_scores)):
                with score_cols[idx]:
                    is_best = idx == best_idx
                    border_color = "#10b981" if is_best else "#6b7280"
                    
                    st.markdown(f"""
                    <div style='border: 3px solid {border_color}; padding: 20px; border-radius: 15px; text-align: center;
                                background: {"#f0fdf4" if is_best else "#f9fafb"}'>
                        {f'<p style="margin: 0; color: #10b981; font-size: 1.2rem; font-weight: bold;">🏆 BEST DEAL</p>' if is_best else ''}
                        <h3 style='margin: 10px 0 5px 0; color: #1f2937;'>{deal_name}</h3>
                        <h1 style='margin: 5px 0; color: {border_color}; font-size: 2.5rem;'>{score_data['score']:.1f}</h1>
                        <p style='margin: 0; font-size: 1.2rem; color: #4b5563;'>Grade: {score_data['grade']}</p>
                        <p style='margin: 5px 0 0 0; color: #6b7280;'>{score_data['rating']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Visualization comparisons
            st.subheader("📈 Visual Comparisons")
            
            # IRR Comparison Bar Chart
            fig_irr_compare = go.Figure()
            
            irrs = [deal.get('irr', 0) for deal in selected_deals]
            colors_list = ['#10b981' if i == best_idx else '#6b7280' for i in range(len(selected_deals))]
            
            fig_irr_compare.add_trace(go.Bar(
                x=selected_names,
                y=irrs,
                marker=dict(color=colors_list),
                text=[f"{irr:.2f}%" for irr in irrs],
                textposition='outside'
            ))
            
            fig_irr_compare.update_layout(
                title="Levered IRR Comparison",
                yaxis_title="IRR (%)",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_irr_compare, use_container_width=True)
            
            # Risk vs Return Scatter
            fig_risk_return = go.Figure()
            
            for idx, (deal_name, deal_data) in enumerate(zip(selected_names, selected_deals)):
                is_best = idx == best_idx
                fig_risk_return.add_trace(go.Scatter(
                    x=[deal_data.get('loan_to_value', 0)],
                    y=[deal_data.get('irr', 0)],
                    mode='markers+text',
                    name=deal_name,
                    marker=dict(
                        size=20,
                        color='#10b981' if is_best else '#6b7280',
                        symbol='star' if is_best else 'circle'
                    ),
                    text=[deal_name],
                    textposition='top center'
                ))
            
            fig_risk_return.update_layout(
                title="Risk vs Return Analysis",
                xaxis_title="Leverage (LTV %)",
                yaxis_title="IRR (%)",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_risk_return, use_container_width=True)
            
            # Winner Analysis
            st.markdown("---")
            st.subheader("🏆 Winner Analysis")
            
            best_deal_name = selected_names[best_idx]
            best_deal_data = selected_deals[best_idx]
            best_score = deal_scores[best_idx]
            
            st.success(f"""
**🏆 RECOMMENDED DEAL: {best_deal_name}**

**Overall Score:** {best_score['score']:.1f}/100 (Grade {best_score['grade']} - {best_score['rating']})

**Why This Deal Wins:**
- Highest algorithmic score based on risk-adjusted returns
- IRR: {best_deal_data.get('irr', 0):.2f}%
- Equity Multiple: {best_deal_data.get('equity_multiple', 0):.2f}x
- NPV: ${best_deal_data.get('npv', 0):,.0f}

**Next Steps:**
1. Review detailed underwriting for {best_deal_name}
2. Verify all assumptions with fresh market data
3. Proceed with acquisition if scoring confirms value
            """)
            
            st.info("💡 **Tip:** The 'best' deal isn't always the highest IRR. Consider your risk tolerance, capital availability, and investment strategy.")
    else:
        st.warning("⚠️ Please select at least 2 deals to compare")


st.markdown(f"**CRE DCF Valuation Model** | Property: {property_type}")