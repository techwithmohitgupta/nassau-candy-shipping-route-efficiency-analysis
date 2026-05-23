from pathlib import Path
import pandas as pd


# -------------------------
# PATHS
# -------------------------
data_path = Path("data/processed")

main_path = data_path / "dashboard_main.csv"


# -------------------------
# LOAD
# -------------------------
df_main = pd.read_csv(main_path)


# -------------------------
# DATE FIX
# -------------------------
df_main["Order Date"] = pd.to_datetime(
    df_main["Order Date"],
    dayfirst=True,
    errors="coerce"
)

df_main["Ship Date"] = pd.to_datetime(
    df_main["Ship Date"],
    dayfirst=True,
    errors="coerce"
)


# -------------------------
# TEXT / ROUTE FIX
# -------------------------
def clean_route_text(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("â†’", "→", regex=False)
        .str.replace("->", "→", regex=False)
        .str.replace("  ", " ", regex=False)
        .str.strip()
    )


df_main["Route_State"] = clean_route_text(df_main["Route_State"])
df_main["Route_Region"] = clean_route_text(df_main["Route_Region"])


# Optional: clean other text columns too
text_cols = ["Factory", "State/Province", "Region", "Ship Mode", "Delay Status"]

for col in text_cols:
    if col in df_main.columns:
        df_main[col] = df_main[col].astype(str).str.strip()


# -------------------------
# SAVE BACK PERMANENTLY
# -------------------------
df_main.to_csv(main_path, index=False)


print("dashboard_main.csv fixed and saved successfully.")
print(df_main[["Order Date", "Ship Date", "Route_State", "Route_Region"]].head())
print(df_main.dtypes)
print(df_main.info())















import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from pathlib import Path
import base64
from datetime import date

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Nassau Candy Logistics Dashboard",
    layout="wide"
)

# -------------------------
# FILE PATHS
# -------------------------
nassau_logo_path = Path("assets/images/nassau_candy.png")
mentor_logo_path = Path("assets/images/unified_mentor.png")

# -------------------------
# LOAD FINAL DATASETS
# -------------------------
@st.cache_data
def load_data():
    df_main = pd.read_csv(r"data/processed/dashboard_main.csv")
    df_region = pd.read_csv(r"data/processed/dashboard_region_summary.csv")
    df_routes = pd.read_csv(r"data/processed/dashboard_route_leaderboard.csv")
    df_ship = pd.read_csv(r"data/processed/dashboard_ship_mode.csv")
    df_map = pd.read_csv(r"data/processed/dashboard_state_map.csv")

    df_main["Order Date"] = pd.to_datetime(df_main["Order Date"], dayfirst=True, errors="coerce")
    df_main["Ship Date"] = pd.to_datetime(df_main["Ship Date"], dayfirst=True, errors="coerce")
    df_main["Shipping Lead Time"] = pd.to_numeric(df_main["Shipping Lead Time"], errors="coerce")

    # Route text safeguard
    df_main["Route_State"] = df_main["Route_State"].astype(str).str.replace("â†’", "->", regex=False)
    df_main["Route_Region"] = df_main["Route_Region"].astype(str).str.replace("â†’", "->", regex=False)

    return df_main, df_region, df_routes, df_ship, df_map

df_main, df_region, df_routes, df_ship, df_map = load_data()

# -------------------------
# HELPERS
# -------------------------
def to_base64(path: Path) -> str:
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return ""

nassau_logo_base64 = to_base64(nassau_logo_path)
df_main, df_region, df_routes, df_ship, df_map = load_data()

# -------------------------
# GLOBAL CSS
# -------------------------
st.markdown(f"""
<style>
/* Hide Streamlit chrome */
[data-testid="stDecoration"] {{
    display: none !important;
}}

header[data-testid="stHeader"] {{
    display: none !important;
}}

[data-testid="stToolbar"] {{
    display: none !important;
}}

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

/* App background */
.stApp {{
    background: linear-gradient(135deg, #dce9f3 0%, #edf4f9 40%, #dce9f3 100%);
}}

/* Main layout spacing */
.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #f8edd4 0%, #eed8a7 55%, #e7cb8a 100%);
    border-right: 1px solid rgba(91, 70, 48, 0.14);
}}

section[data-testid="stSidebar"] .block-container {{
    padding-top: 0rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-bottom: 1.5rem !important;
}}

section[data-testid="stSidebar"] [data-testid="stImage"] img {{
    display: block;
    margin-left: auto;
    margin-right: auto;
}}
            
section[data-testid="stSidebar"] [data-testid="stImage"] {{ 
    margin-top: -20px !important;
    padding-top: 0 !important;
    margin-bottom: 0.25rem !important;
}}

/* Sidebar text */
.sidebar-heading {{
    color: #3b2f1b;
    font-size: 24px;
    font-weight: 800;
    text-align: center;
    margin-top: 0.4rem;
    margin-bottom: 0.4rem;
}}

.sidebar-subtext {{
    color: #6b563d;
    font-size: 13px;
    text-align: center;
    line-height: 1.6;
    margin-bottom: 1rem;
}}

.sidebar-divider {{
    height: 1px;
    background: rgba(91, 70, 48, 0.16);
    margin: 0.8rem 0 1rem 0;
    border-radius: 10px;
}}

.filter-card {{
    background: rgba(255,255,255,0.28);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 18px;
    padding: 14px 14px 8px 14px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 14px;
}}

.filter-card-title {{
    color: #3b2f1b;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 0.6rem;
}}

/* Main header wrapper */
.header-shell {{
    margin-left: 80px;
    margin-bottom: 1.4rem;
}}

/* Hero card */
.hero-card {{
    width: 100%;
    max-width: 1120px;
    background: linear-gradient(135deg, #f6e7c4 0%, #e7c57a 100%);
    border-radius: 26px;
    padding: 26px 30px 30px 30px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.10);
    border: 1px solid rgba(91, 70, 48, 0.08);
    text-align: center;
}}

.hero-logo {{
    width: 260px;
    height: 105px;
    margin: 0 auto 18px auto;
    background-image: url("data:image/png;base64,{nassau_logo_base64}");
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
    background-color: rgba(255,255,255,0.32);
    border-radius: 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}

.hero-title {{
    color: #3b2f1b;
    font-size: 33px;
    font-weight: 900;
    line-height: 1.28;
    margin: 0;
    padding: 0 20px;
}}

.hero-subtitle {{
    color: #5b4630;
    font-size: 16px;
    font-weight: 500;
    line-height: 1.6;
    margin: 14px auto 0 auto;
    text-align: center;
    width: 100%;
}}

.hero-badges {{
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 18px;
}}

.hero-badge {{
    background: rgba(255, 255, 255, 0.32);
    color: #4a3725;
    padding: 10px 16px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.38);
    box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    white-space: nowrap;
}}

/* KPI cards */
.kpi-shell {{
    margin-left: 80px;
    margin-top: 0.4rem;
    margin-bottom: 1rem;
}}

.kpi-card {{
    background: linear-gradient(180deg, #fffaf0 0%, #f6ebcf 100%);
    border: 1px solid rgba(91,70,48,0.08);
    border-radius: 20px;
    padding: 18px 18px 16px 18px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.06);
}}

.kpi-label {{
    color: #6b563d;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 8px;
}}

.kpi-value {{
    color: #3b2f1b;
    font-size: 28px;
    font-weight: 900;
    line-height: 1;
}}

.kpi-note {{
    color: #8a7458;
    font-size: 12px;
    margin-top: 8px;
}}

/* Section cards */
.section-shell {{
    margin-left: 80px;
}}

.section-card {{
    background: linear-gradient(180deg, #fffaf1 0%, #f5ebd2 100%);
    border: 1px solid rgba(91,70,48,0.08);
    border-radius: 22px;
    padding: 18px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    min-height: 320px;
}}

.section-title {{
    color: #3b2f1b;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 6px;
}}

.section-subtitle {{
    color: #6b563d;
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 16px;
}}

.placeholder-box {{
    background: rgba(255,255,255,0.55);
    border: 1px dashed rgba(91,70,48,0.18);
    border-radius: 18px;
    min-height: 210px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #7b6548;
    font-size: 15px;
    font-weight: 600;
    text-align: center;
    padding: 20px;
}}

.small-card-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}}

.small-info-card {{
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(91,70,48,0.08);
    border-radius: 16px;
    padding: 14px;
}}

.small-info-title {{
    color: #4a3725;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 6px;
}}

.small-info-text {{
    color: #6b563d;
    font-size: 12px;
    line-height: 1.5;
}}

/* Utility strip */
.utility-shell {{ 
    margin-left: 80px;
    margin-top: -0.3rem;
    margin-bottom: 1rem;
}}

.utility-strip {{ 
    width: 100%;
    max-width: 1120px;
    background: rgba(255, 250, 240, 0.72);
    border: 1px solid rgba(91,70,48,0.08);
    border-radius: 18px;
    padding: 12px 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}}

.utility-grid {{ 
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}}

.utility-item {{ 
    background: rgba(255,255,255,0.55);
    border-radius: 14px;
    padding: 10px 12px;
    border: 1px solid rgba(91,70,48,0.06);
}}

.utility-label {{ 
    color: #7b6548;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 4px;
}}

.utility-value {{ 
    color: #3b2f1b;
    font-size: 14px;
    font-weight: 700;
}}

/* KPI stronger polish */
.kpi-card {{ 
    position: relative;
    overflow: hidden;
}}

.kpi-card::before {{ 
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #d9b76c, #f5e6c4);
}}

.kpi-card:hover {{ 
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.08);
}}

/* Section chips */
.section-chip-shell {{ 
    margin-left: 80px;
    margin-bottom: 0.8rem;
}}

.section-chip-row {{ 
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}}

.section-chip {{ 
    background: rgba(255,255,255,0.65);
    color: #4a3725;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    border: 1px solid rgba(91,70,48,0.08);
    box-shadow: 0 3px 8px rgba(0,0,0,0.04);
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
}}

.stTabs [data-baseweb="tab"] {{
    background: #f6ebcf;
    border-radius: 14px;
    padding: 10px 16px;
    color: #4a3725;
    font-weight: 700;
}}

.stTabs [aria-selected="true"] {{
    background: #e7c57a !important;
    color: #3b2f1b !important;
}}

.kpi-card {{ 
    background: linear-gradient(180deg, #fffaf0 0%, #f6ebcf 100%);
    border: 1px solid rgba(91,70,48,0.08);
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 6px 14px rgba(0,0,0,0.05);
    transition: all 0.25s ease;
}}

.kpi-card:hover {{ 
    transform: translateY(-3px);
    box-shadow: 0 10px 22px rgba(0,0,0,0.08);
}}

/* Inputs */
.stDateInput, .stSelectbox, .stMultiSelect, .stSlider {{
    margin-bottom: 0.5rem;
}}

@media (max-width: 1200px) {{
    .header-shell, .kpi-shell, .section-shell {{
        margin-left: 20px;
    }}
}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# SIDEBAR UI
# -------------------------
with st.sidebar:
    if mentor_logo_path.exists():
        st.image(str(mentor_logo_path), use_container_width=True)
    else:
        st.warning("Unified Mentor logo not found.")

    st.markdown("""
    <div class="sidebar-heading">Supply Chain Analytics Project</div>
    <div class="sidebar-subtext">
        Premium logistics dashboard controls panel
    </div>
    <div class="sidebar-divider"></div>
    """, unsafe_allow_html=True)

    min_date = df_main["Order Date"].min().date()
    max_date = df_main["Order Date"].max().date()

    st.markdown('<div class="filter-card"><div class="filter-card-title">📅 Date Range</div></div>', unsafe_allow_html=True)
    st.date_input(
        "Select period",
        value=(date(2024, 1, 1), date(2024, 12, 31)),
        label_visibility="collapsed"
    )

    st.markdown('<div class="filter-card"><div class="filter-card-title">🌍 Region / State</div></div>', unsafe_allow_html=True)
    st.selectbox("Region", ["All Regions", "East", "West", "Central", "South"], label_visibility="collapsed")
    st.selectbox("State", ["All States"], label_visibility="collapsed")

    st.markdown('<div class="filter-card"><div class="filter-card-title">🚚 Ship Mode</div></div>', unsafe_allow_html=True)
    st.multiselect(
        "Ship Mode",
        ["Standard Class", "Second Class", "First Class", "Same Day"],
        default=["Standard Class", "Second Class"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="filter-card"><div class="filter-card-title">⏱ Lead-Time Threshold</div></div>', unsafe_allow_html=True)
    st.slider("Lead Time Threshold", min_value=1, max_value=30, value=7, label_visibility="collapsed")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-subtext">
        UI scaffold only • analytics visuals will be connected next
    </div>
    """, unsafe_allow_html=True)

# -------------------------
# HERO HEADER
# -------------------------
st.markdown("""
<div class="header-shell">
    <div class="hero-card">
        <div class="hero-logo"></div>
        <h1 class="hero-title">
            Factory-to-Customer Shipping Route Efficiency Analysis for Nassau Candy Distributor
        </h1>
        <div class="hero-subtitle">
            Analyze shipping lead time, route performance, regional bottlenecks, and ship mode efficiency across factory-to-customer delivery routes.
        </div>
        <div class="hero-badges">
            <span class="hero-badge">⏱ Shipping Lead Time</span>
            <span class="hero-badge">📍 Route Performance</span>
            <span class="hero-badge">⚠ Regional Bottlenecks</span>
            <span class="hero-badge">🚚 Ship Mode Efficiency</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="utility-shell">
    <div class="utility-strip">
        <div class="utility-grid">
            <div class="utility-item">
                <div class="utility-label">Last Updated</div>
                <div class="utility-value">UI Prototype Mode</div>
            </div>
            <div class="utility-item">
                <div class="utility-label">Dashboard Status</div>
                <div class="utility-value">Layout Active</div>
            </div>
            <div class="utility-item">
                <div class="utility-label">Active Filters</div>
                <div class="utility-value">4 Controls Ready</div>
            </div>
            <div class="utility-item">
                <div class="utility-label">View Type</div>
                <div class="utility-value">Executive Overview</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# KPI SECTION (FINAL - PROJECT BASED)
# -------------------------
st.markdown('<div class="kpi-shell">', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)

# 1️⃣ Shipping Lead Time
with k1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">⏱ Shipping Lead Time</div>
        <div class="kpi-value">5.6 Days</div>
        <div class="kpi-note">Overall average delivery duration</div>
    </div>
    """, unsafe_allow_html=True)

# 2️⃣ Average Lead Time
with k2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">📊 Avg Lead Time (Route)</div>
        <div class="kpi-value">6.2 Days</div>
        <div class="kpi-note">Route-level performance average</div>
    </div>
    """, unsafe_allow_html=True)

# 3️⃣ Route Volume
with k3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">📦 Route Volume</div>
        <div class="kpi-value">4,130</div>
        <div class="kpi-note">Total shipments processed</div>
    </div>
    """, unsafe_allow_html=True)

# 4️⃣ Delay Frequency
with k4:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">⚠ Delay Frequency</div>
        <div class="kpi-value">66.4%</div>
        <div class="kpi-note">Above threshold delays</div>
    </div>
    """, unsafe_allow_html=True)

# 5️⃣ Efficiency Score
with k5:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-label">🚀 Efficiency Score</div>
        <div class="kpi-value">72.3</div>
        <div class="kpi-note">Normalized route performance</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="section-chip-shell">
    <div class="section-chip-row">
        <span class="section-chip">Logistics Monitoring</span>
        <span class="section-chip">Route Benchmarking</span>
        <span class="section-chip">Geographic Intelligence</span>
        <span class="section-chip">Shipment Insights</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# MAIN CONTENT UI
# -------------------------
st.markdown('<div class="section-shell">', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Route Overview",
    "Geographic View",
    "Ship Mode Analysis",
    "Route Drill-Down"
])

with tab1:
    left, right = st.columns([1.55, 1])
    with left:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Route Efficiency Overview</div>
            <div class="section-subtitle">
                This area will display route leaderboard visuals, average lead time comparisons,
                and performance benchmarking views.
            </div>
            <div class="placeholder-box">
                Route efficiency chart placeholder
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Quick Insights</div>
            <div class="section-subtitle">
                Insight summaries, route alerts, and high-level recommendations will appear here.
            </div>
            <div class="small-card-grid">
                <div class="small-info-card">
                    <div class="small-info-title">Fastest Routes</div>
                    <div class="small-info-text">Top-performing route summary placeholder.</div>
                </div>
                <div class="small-info-card">
                    <div class="small-info-title">Slowest Routes</div>
                    <div class="small-info-text">Bottom-performing route summary placeholder.</div>
                </div>
                <div class="small-info-card">
                    <div class="small-info-title">High Volume</div>
                    <div class="small-info-text">High-order route signal placeholder.</div>
                </div>
                <div class="small-info-card">
                    <div class="small-info-title">Delay Risk</div>
                    <div class="small-info-text">Delay hotspot insight placeholder.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Geographic Shipping Map</div>
            <div class="section-subtitle">
                Map-based regional bottleneck visualization and state-level efficiency patterns will be shown here.
            </div>
            <div class="placeholder-box">
                U.S. shipping map placeholder
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Bottleneck Summary</div>
            <div class="section-subtitle">
                State and region summaries, delay concentration, and route congestion notes.
            </div>
            <div class="placeholder-box">
                Regional bottleneck summary placeholder
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    c1, c2 = st.columns([1.2, 1.2])
    with c1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Ship Mode Comparison</div>
            <div class="section-subtitle">
                Comparative views for Standard, Second, First Class, and Same Day shipment performance.
            </div>
            <div class="placeholder-box">
                Ship mode comparison chart placeholder
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Mode Trade-Off View</div>
            <div class="section-subtitle">
                Cost-time trade-off commentary, lead-time variance, and shipment distribution placeholders.
            </div>
            <div class="placeholder-box">
                Trade-off analysis placeholder
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab4:
    c1, c2 = st.columns([1.45, 1])
    with c1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Route Drill-Down Panel</div>
            <div class="section-subtitle">
                State-level route inspection, order-level timeline tracking, and detailed drill-down UI.
            </div>
            <div class="placeholder-box">
                Route drill-down table / timeline placeholder
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Selected Route Details</div>
            <div class="section-subtitle">
                Route metadata, delay signals, lead-time notes, and shipment profile placeholder card.
            </div>
            <div class="placeholder-box">
                Selected route detail placeholder
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)