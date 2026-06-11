from pathlib import Path
from datetime import date

import base64
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Nassau Candy Logistics Dashboard",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="auto"
)

# -------------------------
# FILE PATHS
# -------------------------
nassau_logo_path = Path("app/assets/images/nassau_candy.png")
mentor_logo_path = Path("app/assets/images/unified_mentor.png")
css_file_path = Path("app/assets/nassau_shippingrouteanalysis.css")

# -------------------------
# FACTORY COORDINATES
# -------------------------
FACTORY_COORDS = {
    "Lot's O' Nuts": {"lat": 32.881893, "lon": -111.768036},
    "Wicked Choccy's": {"lat": 32.076176, "lon": -81.088371},
    "Sugar Shack": {"lat": 48.11914, "lon": -96.18115},
    "Secret Factory": {"lat": 41.446333, "lon": -90.565487},
    "The Other Factory": {"lat": 35.1175, "lon": -89.971107},
}

# -------------------------
# STATE NAME TO ABBREVIATION
# -------------------------
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT",
    "Delaware": "DE", "District Of Columbia": "DC", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

# -------------------------
# HELPERS
# -------------------------
def to_base64(path: Path) -> str:
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return ""

def clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("â†’", "→", regex=False)
        .str.replace("->", "→", regex=False)
        .str.replace("â€™", "'", regex=False)
        .str.replace("â€˜", "'", regex=False)
        .str.replace("â€“", "-", regex=False)
        .str.replace("  ", " ", regex=False)
        .str.strip()
    )

def format_number(x: float, decimals: int = 1) -> str:
    if pd.isna(x):
        return "0"
    return f"{x:,.{decimals}f}"

def performance_category(score: float) -> str:
    if pd.isna(score):
        return "N/A"
    if score >= 70:
        return "High"
    if score >= 45:
        return "Average"
    return "Poor"

def safe_mode(series: pd.Series, fallback: str = "N/A") -> str:
    if series.empty:
        return fallback
    mode_vals = series.mode()
    if mode_vals.empty:
        return fallback
    return str(mode_vals.iloc[0])


def render_primary_kpi(label: str, value: str, note: str = ""):
    st.markdown(f"""
    <div class="kpi-card primary-kpi">
        <div class="kpi-topline"></div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-note">{note}</div>
    </div>
    """, unsafe_allow_html=True)


def render_secondary_kpi(label: str, value: str):
    st.markdown(f"""
    <div class="secondary-metric">
        <div class="secondary-metric-label">{label}</div>
        <div class="secondary-metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_panel_item(title: str, text: str, kind: str = "insight"):
    box_class = "insight-box" if kind == "insight" else "reco-box"
    title_class = "insight-title" if kind == "insight" else "reco-title"
    text_class = "insight-text" if kind == "insight" else "reco-text"
    st.markdown(f"""
    <div class="{box_class}"> 
        <div class="{title_class}">{title}</div>
        <div class="{text_class}">{text}</div>
    </div>
    """, unsafe_allow_html=True)
    
# -------------------------
# PLOTLY MOBILE-SAFE CONFIG
# -------------------------
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False
}

def apply_mobile_chart_style(fig, height=380):
    """Apply consistent mobile-friendly Plotly styling without changing chart logic."""
    fig.update_layout(
        height=height,
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#2f281c"
        ),
        margin=dict(l=10, r=10, t=28, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.58)",
        hoverlabel=dict(
            bgcolor="#fffdf8",
            bordercolor="rgba(184,149,91,0.28)",
            font=dict(color="#2f281c", size=12)
        ),
        legend=dict(
            font=dict(size=11, color="#2f281c"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    fig.update_xaxes(
        tickfont=dict(size=10, color="#3b2f1b"),
        title_font=dict(size=11, color="#3b2f1b"),
        gridcolor="rgba(91,70,48,0.08)",
        zerolinecolor="rgba(91,70,48,0.12)"
    )

    fig.update_yaxes(
        tickfont=dict(size=10, color="#3b2f1b"),
        title_font=dict(size=11, color="#3b2f1b"),
        gridcolor="rgba(91,70,48,0.08)",
        zerolinecolor="rgba(91,70,48,0.12)"
    )

    return fig


def show_chart(fig, height=380):
    """Render Plotly chart with mobile-safe config."""
    fig = apply_mobile_chart_style(fig, height=height)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def load_css(css_path: Path):
    """Load external CSS file safely into Streamlit."""
    possible_paths = [
        css_path,
        Path("nassau_shippingrouteanalysis.css"),
        Path(__file__).parent / "assets" / "nassau_shippingrouteanalysis.css",
        Path(__file__).parent / "nassau_shippingrouteanalysis.css",
    ]

    selected_path = None
    for path in possible_paths:
        if path.exists():
            selected_path = path
            break

    if selected_path is None:
        st.warning("CSS file not found: nassau_shippingrouteanalysis.css")
        return

    css = selected_path.read_text(encoding="utf-8")
    css = css.replace("{nassau_logo_base64}", nassau_logo_base64)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# -------------------------
# LOAD FINAL DATASETS
# -------------------------
@st.cache_data
def load_data():
    df_main = pd.read_csv("data/processed/dashboard_main.csv")
    df_region = pd.read_csv("data/processed/dashboard_region_summary.csv")
    df_routes = pd.read_csv("data/processed/dashboard_route_leaderboard.csv")
    df_ship = pd.read_csv("data/processed/dashboard_ship_mode.csv")
    df_map = pd.read_csv("data/processed/dashboard_state_map.csv")

    # Main dataset
    df_main["Order Date"] = pd.to_datetime(df_main["Order Date"], dayfirst=True, errors="coerce")
    df_main["Ship Date"] = pd.to_datetime(df_main["Ship Date"], dayfirst=True, errors="coerce")
    df_main["Shipping Lead Time"] = pd.to_numeric(df_main["Shipping Lead Time"], errors="coerce")

    text_cols_main = [
        "Order ID", "Ship Mode", "Factory", "State/Province", "Region",
        "Route_State", "Route_Region", "Delay Status", "Shipping Speed Category"
    ]
    for col in text_cols_main:
        if col in df_main.columns:
            df_main[col] = clean_text_series(df_main[col])

    if "Route_State" not in df_main.columns and {"Factory", "State/Province"}.issubset(df_main.columns):
        df_main["Route_State"] = df_main["Factory"] + " → " + df_main["State/Province"]

    if "Route_Region" not in df_main.columns and {"Factory", "Region"}.issubset(df_main.columns):
        df_main["Route_Region"] = df_main["Factory"] + " → " + df_main["Region"]

    # Route leaderboard
    if "Route_State" in df_routes.columns:
        df_routes["Route_State"] = clean_text_series(df_routes["Route_State"])

    for col in [
        "Total_Shipments", "Avg_Lead_Time", "Lead_Time_Std",
        "Min_Lead_Time", "Max_Lead_Time", "Efficiency_Rank", "Efficiency_Score"
    ]:
        if col in df_routes.columns:
            df_routes[col] = pd.to_numeric(df_routes[col], errors="coerce")

    # Region summary
    if "Route_Region" in df_region.columns:
        df_region["Route_Region"] = clean_text_series(df_region["Route_Region"])

    for col in [
        "Total_Shipments", "Avg_Lead_Time", "Lead_Time_Std",
        "Min_Lead_Time", "Max_Lead_Time"
    ]:
        if col in df_region.columns:
            df_region[col] = pd.to_numeric(df_region[col], errors="coerce")

    # Ship mode
    if "Ship Mode" in df_ship.columns:
        df_ship["Ship Mode"] = clean_text_series(df_ship["Ship Mode"])

    for col in [
        "Total_Shipments", "Avg_Lead_Time", "Lead_Time_Std",
        "Delayed", "On-Time", "Efficiency_Rank"
    ]:
        if col in df_ship.columns:
            df_ship[col] = pd.to_numeric(df_ship[col], errors="coerce")

    # State map
    if "State/Province" in df_map.columns:
        df_map["State/Province"] = clean_text_series(df_map["State/Province"])

    for col in ["Total_Shipments", "Avg_Lead_Time", "Lead_Time_Std"]:
        if col in df_map.columns:
            df_map[col] = pd.to_numeric(df_map[col], errors="coerce")

    return df_main, df_region, df_routes, df_ship, df_map

df_main, df_region, df_routes, df_ship, df_map = load_data()
nassau_logo_base64 = to_base64(nassau_logo_path)
load_css(css_file_path)

# -------------------------
# FILTER PREP
# -------------------------
df_main = df_main.dropna(subset=["Order Date", "Ship Date", "Shipping Lead Time"]).copy()

min_date = df_main["Order Date"].min().date()
max_date = df_main["Order Date"].max().date()

region_options = ["All Regions"] + sorted(df_main["Region"].dropna().unique().tolist())
ship_mode_options = sorted(df_main["Ship Mode"].dropna().unique().tolist())

# -------------------------
# CENTRAL FILTER STATE SYSTEM
# Initialize single source of truth for desktop + mobile filters
# -------------------------

def get_state_options_for_region(region_value: str) -> list[str]:
    """Return valid state options based on selected region."""
    if region_value == "All Regions":
        state_source = df_main.copy()
    else:
        state_source = df_main[df_main["Region"] == region_value].copy()

    return ["All States"] + sorted(
        state_source["State/Province"].dropna().unique().tolist()
    )


def clamp_date_range(start_value, end_value):
    """Keep selected dates inside dataset date range."""
    if start_value is None or end_value is None:
        return min_date, max_date

    if start_value < min_date:
        start_value = min_date

    if end_value > max_date:
        end_value = max_date

    if start_value > end_value:
        return min_date, max_date

    return start_value, end_value


# Default final filter state
default_filter_state = {
    "active_filter_source": "desktop",
    "final_start_date": min_date,
    "final_end_date": max_date,
    "final_region": "All Regions",
    "final_state": "All States",
    "final_ship_modes": ship_mode_options.copy(),
    "final_lead_time_threshold": 5,
}

# Initialize missing session state values only once
for state_key, default_value in default_filter_state.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


# -------------------------
# Validate existing session state after reruns / code changes
# -------------------------

# Validate date range
final_start_date, final_end_date = clamp_date_range(
    st.session_state.get("final_start_date", min_date),
    st.session_state.get("final_end_date", max_date),
)

st.session_state["final_start_date"] = final_start_date
st.session_state["final_end_date"] = final_end_date

# Validate region
if st.session_state.get("final_region") not in region_options:
    st.session_state["final_region"] = "All Regions"

# Validate state based on final region
final_state_options = get_state_options_for_region(st.session_state["final_region"])

if st.session_state.get("final_state") not in final_state_options:
    st.session_state["final_state"] = "All States"

# Validate ship modes
current_ship_modes = st.session_state.get("final_ship_modes", ship_mode_options.copy())

if not isinstance(current_ship_modes, list):
    current_ship_modes = ship_mode_options.copy()

st.session_state["final_ship_modes"] = [
    mode for mode in current_ship_modes if mode in ship_mode_options
]

# Validate threshold
try:
    threshold_value = int(st.session_state.get("final_lead_time_threshold", 5))
except Exception:
    threshold_value = 5

threshold_value = max(1, min(15, threshold_value))
st.session_state["final_lead_time_threshold"] = threshold_value

# -------------------------
# SIDEBAR FILTERS — DESKTOP SOURCE
# Updates central filter state for desktop sidebar
# -------------------------
with st.sidebar:
    if mentor_logo_path.exists():
        st.image(str(mentor_logo_path), use_container_width=True)
    else:
        st.warning("Unified Mentor logo not found.")

    st.markdown("""
    <div class="sidebar-hero-card">
        <div class="sidebar-heading">Logistics & Supply Chain Analytics</div>
        <div class="sidebar-subtext">
            Nassau Candy Logistics Dashboard
        </div>
    </div>
    <div class="sidebar-divider"></div>
    """, unsafe_allow_html=True)

    # -------------------------
    # Desktop Date Range
    # -------------------------
    st.markdown(
        '<div class="filter-card"><div class="filter-card-title">📅 Date Range</div></div>',
        unsafe_allow_html=True,
    )

    desktop_default_dates = (
        st.session_state["final_start_date"],
        st.session_state["final_end_date"],
    )

    desktop_selected_dates = st.date_input(
        "Select period",
        value=desktop_default_dates,
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
        key="desktop_date_range_filter",
    )

    if isinstance(desktop_selected_dates, tuple) and len(desktop_selected_dates) == 2:
        desktop_start_date, desktop_end_date = desktop_selected_dates
    else:
        desktop_start_date, desktop_end_date = min_date, max_date

    # -------------------------
    # Desktop Region + State
    # -------------------------
    st.markdown(
        '<div class="filter-card"><div class="filter-card-title">🌍 Region / State</div></div>',
        unsafe_allow_html=True,
    )

    desktop_region_index = (
        region_options.index(st.session_state["final_region"])
        if st.session_state["final_region"] in region_options
        else 0
    )

    desktop_selected_region = st.selectbox(
        "Region",
        options=region_options,
        index=desktop_region_index,
        label_visibility="collapsed",
        key="desktop_region_filter",
    )

    desktop_state_options = get_state_options_for_region(desktop_selected_region)

    current_final_state = st.session_state.get("final_state", "All States")
    if current_final_state not in desktop_state_options:
        current_final_state = "All States"

    desktop_state_index = (
        desktop_state_options.index(current_final_state)
        if current_final_state in desktop_state_options
        else 0
    )

    desktop_selected_state = st.selectbox(
        "State",
        options=desktop_state_options,
        index=desktop_state_index,
        label_visibility="collapsed",
        key="desktop_state_filter",
    )

    # -------------------------
    # Desktop Ship Mode
    # -------------------------
    st.markdown(
        '<div class="filter-card"><div class="filter-card-title">🚚 Ship Mode</div></div>',
        unsafe_allow_html=True,
    )

    desktop_default_ship_modes = [
        mode
        for mode in st.session_state.get("final_ship_modes", ship_mode_options.copy())
        if mode in ship_mode_options
    ]

    desktop_selected_ship_modes = st.multiselect(
        "Ship Mode",
        options=ship_mode_options,
        default=desktop_default_ship_modes,
        label_visibility="collapsed",
        key="desktop_ship_mode_filter",
    )

    # -------------------------
    # Desktop Lead-Time Threshold
    # -------------------------
    st.markdown(
        '<div class="filter-card"><div class="filter-card-title">⏱ Lead-Time Threshold</div></div>',
        unsafe_allow_html=True,
    )

    desktop_lead_time_threshold = st.slider(
        "Lead Time Threshold",
        min_value=1,
        max_value=15,
        value=int(st.session_state["final_lead_time_threshold"]),
        label_visibility="collapsed",
        key="desktop_lead_time_threshold_filter",
    )

    # -------------------------
    # Update central state from desktop filters ONLY when desktop changes
    # This prevents hidden mobile widgets from fighting with desktop state.
    # -------------------------
    desktop_filter_payload = {
        "start_date": desktop_start_date,
        "end_date": desktop_end_date,
        "region": desktop_selected_region,
        "state": desktop_selected_state,
        "ship_modes": desktop_selected_ship_modes,
        "lead_time_threshold": int(desktop_lead_time_threshold),
    }

    desktop_previous_payload = st.session_state.get("_desktop_filter_payload")

    if desktop_previous_payload is None or desktop_filter_payload != desktop_previous_payload:
        st.session_state["active_filter_source"] = "desktop"
        st.session_state["final_start_date"] = desktop_filter_payload["start_date"]
        st.session_state["final_end_date"] = desktop_filter_payload["end_date"]
        st.session_state["final_region"] = desktop_filter_payload["region"]
        st.session_state["final_state"] = desktop_filter_payload["state"]
        st.session_state["final_ship_modes"] = desktop_filter_payload["ship_modes"]
        st.session_state["final_lead_time_threshold"] = desktop_filter_payload["lead_time_threshold"]

    st.session_state["_desktop_filter_payload"] = desktop_filter_payload
    
# -------------------------
# MOBILE FILTER PANEL — MOBILE SOURCE
# Updates central filter state only when mobile filters change
# -------------------------

st.markdown('<div class="mobile-filter-panel-wrapper">', unsafe_allow_html=True)

with st.expander("📱 Dashboard Filters", expanded=False):

    st.markdown(
        """
        <div class="mobile-filter-intro">
            Quickly adjust the dashboard filters to explore shipping performance, route efficiency,
            regional bottlenecks, and ship mode insights.
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------
    # Mobile Date Range
    # -------------------------
    mobile_default_dates = (
        st.session_state["final_start_date"],
        st.session_state["final_end_date"],
    )

    mobile_selected_dates = st.date_input(
        "📅 Date Range",
        value=mobile_default_dates,
        min_value=min_date,
        max_value=max_date,
        key="mobile_date_range_filter",
    )

    if isinstance(mobile_selected_dates, tuple) and len(mobile_selected_dates) == 2:
        mobile_start_date, mobile_end_date = mobile_selected_dates
    else:
        mobile_start_date, mobile_end_date = min_date, max_date

    # -------------------------
    # Mobile Region
    # -------------------------
    mobile_region_default = st.session_state.get("final_region", "All Regions")

    mobile_region_index = (
        region_options.index(mobile_region_default)
        if mobile_region_default in region_options
        else 0
    )

    mobile_selected_region = st.selectbox(
        "🌍 Region",
        options=region_options,
        index=mobile_region_index,
        key="mobile_region_filter",
    )

    # -------------------------
    # Mobile State based on selected mobile region
    # -------------------------
    mobile_state_options = get_state_options_for_region(mobile_selected_region)

    current_mobile_state = st.session_state.get("mobile_state_filter", st.session_state.get("final_state", "All States"))

    if current_mobile_state not in mobile_state_options:
        current_mobile_state = "All States"

    mobile_state_index = (
        mobile_state_options.index(current_mobile_state)
        if current_mobile_state in mobile_state_options
        else 0
    )

    mobile_selected_state = st.selectbox(
        "📍 State",
        options=mobile_state_options,
        index=mobile_state_index,
        key="mobile_state_filter",
    )

    # -------------------------
    # Mobile Ship Mode
    # -------------------------
    mobile_default_ship_modes = [
        mode
        for mode in st.session_state.get("final_ship_modes", ship_mode_options.copy())
        if mode in ship_mode_options
    ]

    mobile_selected_ship_modes = st.multiselect(
        "🚚 Ship Mode",
        options=ship_mode_options,
        default=mobile_default_ship_modes,
        key="mobile_ship_mode_filter",
    )

    # -------------------------
    # Mobile Lead-Time Threshold
    # -------------------------
    mobile_lead_time_threshold = st.slider(
        "⏱ Lead-Time Threshold",
        min_value=1,
        max_value=15,
        value=int(st.session_state["final_lead_time_threshold"]),
        key="mobile_lead_time_threshold_filter",
    )

    # -------------------------
    # Update central state from mobile filters ONLY when mobile changes
    # This prevents hidden mobile panel from overwriting desktop filters.
    # -------------------------
    mobile_filter_payload = {
        "start_date": mobile_start_date,
        "end_date": mobile_end_date,
        "region": mobile_selected_region,
        "state": mobile_selected_state,
        "ship_modes": mobile_selected_ship_modes,
        "lead_time_threshold": int(mobile_lead_time_threshold),
    }

    mobile_previous_payload = st.session_state.get("_mobile_filter_payload")

    if mobile_previous_payload is None:
        # First render only: store payload, do not overwrite desktop state.
        st.session_state["_mobile_filter_payload"] = mobile_filter_payload

    elif mobile_filter_payload != mobile_previous_payload:
        st.session_state["active_filter_source"] = "mobile"
        st.session_state["final_start_date"] = mobile_filter_payload["start_date"]
        st.session_state["final_end_date"] = mobile_filter_payload["end_date"]
        st.session_state["final_region"] = mobile_filter_payload["region"]
        st.session_state["final_state"] = mobile_filter_payload["state"]
        st.session_state["final_ship_modes"] = mobile_filter_payload["ship_modes"]
        st.session_state["final_lead_time_threshold"] = mobile_filter_payload["lead_time_threshold"]

        st.session_state["_mobile_filter_payload"] = mobile_filter_payload

    else:
        st.session_state["_mobile_filter_payload"] = mobile_filter_payload

st.markdown('</div>', unsafe_allow_html=True)


# -------------------------
# FINAL FILTER VARIABLES
# Single source of truth for KPI, charts, tables, and insights
# -------------------------
start_date = st.session_state["final_start_date"]
end_date = st.session_state["final_end_date"]
selected_region = st.session_state["final_region"]
selected_state = st.session_state["final_state"]
selected_ship_modes = st.session_state["final_ship_modes"]
lead_time_threshold = st.session_state["final_lead_time_threshold"]

# -------------------------
# STEP 5 — FINAL FILTER STATE STABILITY GUARD
# Prevents invalid final filter values after desktop/mobile switching
# -------------------------

# Date safety
start_date, end_date = clamp_date_range(start_date, end_date)
st.session_state["final_start_date"] = start_date
st.session_state["final_end_date"] = end_date

# Region safety
if selected_region not in region_options:
    selected_region = "All Regions"
    st.session_state["final_region"] = selected_region

# State safety based on selected region
valid_state_options = get_state_options_for_region(selected_region)

if selected_state not in valid_state_options:
    selected_state = "All States"
    st.session_state["final_state"] = selected_state

# Ship mode safety
selected_ship_modes = [
    mode for mode in selected_ship_modes if mode in ship_mode_options
]

st.session_state["final_ship_modes"] = selected_ship_modes

# Threshold safety
lead_time_threshold = int(lead_time_threshold)
lead_time_threshold = max(1, min(15, lead_time_threshold))
st.session_state["final_lead_time_threshold"] = lead_time_threshold

# -------------------------
# FILTERED DATA
# -------------------------
filtered_df = df_main.copy()

filtered_df = filtered_df[
    (filtered_df["Order Date"].dt.date >= start_date) &
    (filtered_df["Order Date"].dt.date <= end_date)
]

if selected_region != "All Regions":
    filtered_df = filtered_df[filtered_df["Region"] == selected_region]

if selected_state != "All States":
    filtered_df = filtered_df[filtered_df["State/Province"] == selected_state]

if selected_ship_modes:
    filtered_df = filtered_df[filtered_df["Ship Mode"].isin(selected_ship_modes)]
else:
    filtered_df = filtered_df.iloc[0:0].copy()

filtered_df["Dynamic Delay Status"] = np.where(
    filtered_df["Shipping Lead Time"] > lead_time_threshold,
    "Delayed",
    "On-Time"
)

# -------------------------
# DERIVED STATS FROM FILTERED DATA
# -------------------------
route_stats = (
    filtered_df.groupby("Route_State", as_index=False)
    .agg(
        Total_Shipments=("Order ID", "count"),
        Avg_Lead_Time=("Shipping Lead Time", "mean"),
        Lead_Time_Std=("Shipping Lead Time", "std"),
        Min_Lead_Time=("Shipping Lead Time", "min"),
        Max_Lead_Time=("Shipping Lead Time", "max"),
        Delayed_Count=("Dynamic Delay Status", lambda x: (x == "Delayed").sum())
    )
)

if not route_stats.empty:
    min_avg = route_stats["Avg_Lead_Time"].min()
    max_avg = route_stats["Avg_Lead_Time"].max()

    if max_avg != min_avg:
        route_stats["Efficiency_Score"] = 100 - (
            (route_stats["Avg_Lead_Time"] - min_avg) / (max_avg - min_avg) * 100
        )
    else:
        route_stats["Efficiency_Score"] = 100.0

    route_stats["Efficiency_Rank"] = route_stats["Efficiency_Score"].rank(
        ascending=False,
        method="dense"
    ).astype(int)

    route_stats["Performance_Category"] = route_stats["Efficiency_Score"].apply(performance_category)
    route_stats["Delay_Frequency"] = (route_stats["Delayed_Count"] / route_stats["Total_Shipments"]) * 100
else:
    route_stats["Efficiency_Score"] = pd.Series(dtype=float)
    route_stats["Efficiency_Rank"] = pd.Series(dtype=int)
    route_stats["Performance_Category"] = pd.Series(dtype=str)
    route_stats["Delay_Frequency"] = pd.Series(dtype=float)

region_stats = (
    filtered_df.groupby("Route_Region", as_index=False)
    .agg(
        Total_Shipments=("Order ID", "count"),
        Avg_Lead_Time=("Shipping Lead Time", "mean"),
        Lead_Time_Std=("Shipping Lead Time", "std"),
        Min_Lead_Time=("Shipping Lead Time", "min"),
        Max_Lead_Time=("Shipping Lead Time", "max")
    )
)

state_stats = (
    filtered_df.groupby("State/Province", as_index=False)
    .agg(
        Total_Shipments=("Order ID", "count"),
        Avg_Lead_Time=("Shipping Lead Time", "mean"),
        Lead_Time_Std=("Shipping Lead Time", "std"),
        Delayed_Count=("Dynamic Delay Status", lambda x: (x == "Delayed").sum())
    )
)

if not state_stats.empty:
    state_stats["Delay_Frequency"] = (state_stats["Delayed_Count"] / state_stats["Total_Shipments"]) * 100

    volume_cutoff = state_stats["Total_Shipments"].quantile(0.75)
    lead_cutoff = state_stats["Avg_Lead_Time"].quantile(0.75)

    state_stats["Bottleneck_Flag"] = np.where(
        (state_stats["Total_Shipments"] >= volume_cutoff) &
        (state_stats["Avg_Lead_Time"] >= lead_cutoff),
        "Bottleneck",
        "Normal"
    )
else:
    state_stats["Delay_Frequency"] = pd.Series(dtype=float)
    state_stats["Bottleneck_Flag"] = pd.Series(dtype=str)

ship_stats = (
    filtered_df.groupby("Ship Mode", as_index=False)
    .agg(
        Total_Shipments=("Order ID", "count"),
        Avg_Lead_Time=("Shipping Lead Time", "mean"),
        Lead_Time_Std=("Shipping Lead Time", "std"),
        Delayed=("Dynamic Delay Status", lambda x: (x == "Delayed").mean() * 100),
        On_Time=("Dynamic Delay Status", lambda x: (x == "On-Time").mean() * 100)
    )
)

if not ship_stats.empty:
    ship_stats["Efficiency_Rank"] = ship_stats["Avg_Lead_Time"].rank(
        ascending=True,
        method="dense"
    ).astype(int)

    # -------------------------
# TREND DATA (NEW)
# -------------------------
trend_df = filtered_df.copy()

if not trend_df.empty:
    trend_df["Month"] = trend_df["Order Date"].dt.to_period("M").astype(str)

    monthly_trend = trend_df.groupby("Month").agg(
        Avg_Lead_Time=("Shipping Lead Time", "mean"),
        Orders=("Order ID", "count")
    ).reset_index()
else:
    monthly_trend = pd.DataFrame()

# -------------------------
# KPI CALCULATIONS
# -------------------------
shipping_lead_time_kpi = filtered_df["Shipping Lead Time"].median() if not filtered_df.empty else 0
average_lead_time_kpi = filtered_df["Shipping Lead Time"].mean() if not filtered_df.empty else 0
total_shipments_kpi = len(filtered_df) if not filtered_df.empty else 0
unique_orders_kpi = filtered_df["Order ID"].nunique() if not filtered_df.empty else 0
avg_shipments_per_order_kpi = (
    total_shipments_kpi / unique_orders_kpi
    if unique_orders_kpi else 0
)
route_volume_kpi = route_stats["Total_Shipments"].mean() if not route_stats.empty else 0
delay_frequency_kpi = (
    (filtered_df["Dynamic Delay Status"] == "Delayed").mean() * 100
    if not filtered_df.empty else 0
)
route_efficiency_score_kpi = route_stats["Efficiency_Score"].mean() if not route_stats.empty else 0

active_filters_count = 0
if selected_region != "All Regions":
    active_filters_count += 1
if selected_state != "All States":
    active_filters_count += 1
if len(selected_ship_modes) != len(ship_mode_options):
    active_filters_count += 1
if (start_date, end_date) != (min_date, max_date):
    active_filters_count += 1

# -------------------------
# COMPARISON LOGIC (NEW)
# -------------------------
overall_avg = df_main["Shipping Lead Time"].mean() if not df_main.empty else 0
current_avg = filtered_df["Shipping Lead Time"].mean() if not filtered_df.empty else 0

difference = current_avg - overall_avg

# -------------------------
# INSIGHT ENGINE
# -------------------------
insights = []
recommendations = []

if not filtered_df.empty:
    if not region_stats.empty:
        worst_region_row = region_stats.sort_values("Avg_Lead_Time", ascending=False).iloc[0]
        insights.append((
            "🚨 Highest Delay Region",
            f"{worst_region_row['Route_Region']} is the slowest regional route group with {worst_region_row['Avg_Lead_Time']:.2f} days average lead time."
        ))

    if not ship_stats.empty:
        best_mode_row = ship_stats.sort_values("Avg_Lead_Time", ascending=True).iloc[0]
        insights.append((
            "🚚 Best Shipping Mode",
            f"{best_mode_row['Ship Mode']} is the fastest shipping method with {best_mode_row['Avg_Lead_Time']:.2f} days average lead time."
        ))

    if not state_stats.empty:
        worst_state_row = state_stats.sort_values("Avg_Lead_Time", ascending=False).iloc[0]
        insights.append((
            "⚠ Geographic Bottleneck",
            f"{worst_state_row['State/Province']} shows the highest average lead time at {worst_state_row['Avg_Lead_Time']:.2f} days."
        ))

    if not route_stats.empty:
        highest_volume_row = route_stats.sort_values("Total_Shipments", ascending=False).iloc[0]
        insights.append((
            "📦 Highest Volume Route",
            f"{highest_volume_row['Route_State']} carries the highest shipment load with {int(highest_volume_row['Total_Shipments'])} orders."
        ))

    if delay_frequency_kpi > 40:
        recommendations.append((
            "Priority Action",
            "Delay % is high for the selected filters. Review slow routes and consider switching to faster ship modes for bottleneck areas."
        ))

    if average_lead_time_kpi > 5:
        recommendations.append((
            "Route Optimization",
            "Average route lead time is elevated. Focus on bottom 10 routes and investigate factory-to-destination route efficiency."
        ))

    if not ship_stats.empty:
        slowest_mode = ship_stats.sort_values("Avg_Lead_Time", ascending=False).iloc[0]
        recommendations.append((
            "Ship Mode Strategy",
            f"{slowest_mode['Ship Mode']} is currently the slowest mode. Use it selectively for low-priority shipments only."
        ))

    if not state_stats.empty and (state_stats["Bottleneck_Flag"] == "Bottleneck").any():
        bottleneck_count = int((state_stats["Bottleneck_Flag"] == "Bottleneck").sum())
        recommendations.append((
            "Bottleneck Watch",
            f"{bottleneck_count} state(s) are flagged as bottlenecks based on high volume and high lead time. Prioritize these locations for operational review."
        ))

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

# -------------------------
# KEY PERFORMANCE INDICATORS
# -------------------------
st.markdown('<div class="dashboard-section-heading">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
st.markdown('<div class="kpi-zone-shell">', unsafe_allow_html=True)

st.markdown('<div class="kpi-primary-row">', unsafe_allow_html=True)
primary_cols = st.columns(5)
primary_kpis = [
    ("⏱ Shipping Lead Time", f"{format_number(shipping_lead_time_kpi, 1)} Days", "Median shipment duration"),
    ("📊 Average Lead Time", f"{format_number(average_lead_time_kpi, 1)} Days", "Mean shipment duration"),
    ("📦 Route Volume", f"{format_number(route_volume_kpi, 0)}", "Average shipments handled per route"),
    ("⚠ Delay Frequency", f"{format_number(delay_frequency_kpi, 1)}%", f"Above threshold ({lead_time_threshold} days)"),
    ("🚀 Route Efficiency Score", f"{format_number(route_efficiency_score_kpi, 1)}", "Average normalized route efficiency"),
]

for col, (label, value, note) in zip(primary_cols, primary_kpis):
    with col:
        render_primary_kpi(label, value, note)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="secondary-metric-shell">
    <div class="secondary-metric-heading">Supporting Metrics</div>
    <div class="secondary-analyst-strip">
        <div class="secondary-analyst-item">
            <div class="secondary-metric-label">Total Shipments</div>
            <div class="secondary-metric-value">{format_number(total_shipments_kpi, 0)}</div>
        </div>
        <div class="secondary-analyst-item">
            <div class="secondary-metric-label">Unique Orders</div>
            <div class="secondary-metric-value">{format_number(unique_orders_kpi, 0)}</div>
        </div>
        <div class="secondary-analyst-item">
            <div class="secondary-metric-label">Avg Shipments/Order</div>
            <div class="secondary-metric-value">{format_number(avg_shipments_per_order_kpi, 2)}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if delay_frequency_kpi > 40:
    kpi_msg = "⚠ High operational risk detected for the current selection."
elif delay_frequency_kpi > 20:
    kpi_msg = "⚠ Moderate delivery delays are visible in the current selection."
else:
    kpi_msg = "✅ Current logistics performance looks healthy for the selected filters."

st.markdown(
    f"""
    <div class="summary-card">
        <div class="summary-card-label">Performance Summary</div>
        <div class="summary-card-text">{kpi_msg}</div>
        <div class="summary-card-note">
            <strong>Route Efficiency Score:</strong> Calculated from normalized average lead time. 
            Faster routes get higher scores, while slower routes get lower scores.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------
# SECTION CHIPS
# -------------------------
st.markdown("""
<div class="section-chip-shell">
    <div class="section-chip-row">
        <span class="section-chip">Logistics Monitoring</span>
        <span class="section-chip">Route Benchmarking</span>
        <span class="section-chip">Geographic Bottlenecks</span>
        <span class="section-chip">Shipment Insights</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# MAIN CONTENT
# -------------------------
st.markdown('<div class="section-shell">', unsafe_allow_html=True)

# Global empty state
if filtered_df.empty:
    st.warning("No data available for the selected filters. Please adjust the sidebar filters.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

    # -------------------------
# TOP INSIGHT BANNER (NEW)
# -------------------------
if not route_stats.empty:
    top_insight = route_stats.sort_values("Avg_Lead_Time", ascending=False).iloc[0]

st.markdown(f"""
<div class="critical-card">
    <div class="critical-card-label">Critical Insight</div>
    <div class="critical-card-text">
        {top_insight['Route_State']} is the slowest route in the current selection with {top_insight['Avg_Lead_Time']:.2f} days average lead time.
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Route Overview",
    "Geographic View",
    "Ship Mode Analysis",
    "Route Drill-Down",
    "Trends 📈"
])

# -------------------------
# TAB 1 - ROUTE OVERVIEW
# -------------------------
with tab1:
    left, right = st.columns([1.55, 1])

    with left:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📊 Route Efficiency Overview (Lead Time Analysis)</div>
            <div class="section-subtitle">
                Average lead time, route ranking, and volume-performance relationship.
            </div>
        """, unsafe_allow_html=True)

        if route_stats.empty:
            st.warning("No route data available for the selected filters.")
        else:
            route_chart_df = route_stats.sort_values("Avg_Lead_Time", ascending=False).head(15).copy()

            fig_route = px.bar(
                route_chart_df,
                x="Avg_Lead_Time",
                y="Route_State",
                orientation="h",
                text="Avg_Lead_Time",
                color="Efficiency_Score",
                color_continuous_scale="YlOrBr"
            )
            fig_route.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_route.update_layout(
                height=420,
                xaxis_title="Average Lead Time (Days)",
                yaxis_title="Factory → Route",
                yaxis=dict(categoryorder="total ascending"),
                margin=dict(l=10, r=10, t=20, b=10),
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_route, use_container_width=True, config=PLOTLY_CONFIG)

            scatter_df = route_stats.copy()
            fig_scatter = px.scatter(
                scatter_df,
                x="Total_Shipments",
                y="Avg_Lead_Time",
                size="Total_Shipments",
                color="Performance_Category",
                hover_name="Route_State",
                color_discrete_map={
                    "High": "#9C7B37",
                    "Average": "#D0A95A",
                    "Poor": "#E49C3D"
                }
            )
            fig_scatter.update_layout(
                height=330,
                xaxis_title="Route Volume",
                yaxis_title="Average Lead Time (Days)",
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True, config=PLOTLY_CONFIG)

            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">📌 Route Interpretation</div>
                <div class="insight-text">
                    Routes appearing in the high-volume and high-lead-time zone represent the biggest operational risk because they combine shipment scale with slower delivery performance.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">⚡ Insights & Recommendations</div>
            <div class="section-subtitle">
                Clean analyst summary for the selected filters, focused on the most important findings and actions.
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="panel-subheading">Key Insights</div>', unsafe_allow_html=True)
        if insights:
            for title, text in insights[:4]:
                render_panel_item(title, text, kind="insight")
        else:
            st.info("No insight summary available for the selected filters.")

        st.markdown('<div class="spacer-8"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-subheading">Recommended Actions</div>', unsafe_allow_html=True)
        if recommendations:
            for title, text in recommendations[:4]:
                render_panel_item(f"💡 {title}", text, kind="recommendation")
        else:
            st.info("No recommendation summary available for the selected filters.")

        st.markdown("</div>", unsafe_allow_html=True)

    if not route_stats.empty:
        route_rank_display = route_stats.copy()

        for col in ["Avg_Lead_Time", "Efficiency_Score"]:
            if col in route_rank_display.columns:
                route_rank_display[col] = route_rank_display[col].round(1)

        # Safe leaderboard source: minimum 3 shipments
        leaderboard_source = route_rank_display[
            route_rank_display["Total_Shipments"] >= 3
        ].copy()

        # Agar filter ke baad data empty ho jaye, to original use karo
        if leaderboard_source.empty:
            leaderboard_source = route_rank_display.copy()

        top_10_routes = leaderboard_source.sort_values(
            "Efficiency_Score", ascending=False
        )[["Route_State", "Total_Shipments", "Avg_Lead_Time", "Efficiency_Score"]].head(10).copy()

        bottom_10_routes = leaderboard_source.sort_values(
            "Efficiency_Score", ascending=True
        )[["Route_State", "Total_Shipments", "Avg_Lead_Time", "Efficiency_Score"]].head(10).copy()

        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.markdown("**🏆 Top 10 Efficient Routes**")
            fig_top_routes = px.bar(
                top_10_routes.sort_values("Efficiency_Score", ascending=True),
                x="Efficiency_Score",
                y="Route_State",
                orientation="h",
                text="Efficiency_Score",
                color="Efficiency_Score",
                color_continuous_scale="Greens"
            )
            fig_top_routes.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig_top_routes.update_layout(
                height=380,
                xaxis_title="Efficiency Score",
                yaxis_title="Factory → Route",
                margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_top_routes, use_container_width=True, config=PLOTLY_CONFIG)

        with chart_right:
            st.markdown("**⚠️ Bottom 10 Least Efficient Routes**")
            fig_bottom_routes = px.bar(
                bottom_10_routes.sort_values("Efficiency_Score", ascending=False),
                x="Efficiency_Score",
                y="Route_State",
                orientation="h",
                text="Efficiency_Score",
                color="Efficiency_Score",
                color_continuous_scale="OrRd"
            )
            fig_bottom_routes.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig_bottom_routes.update_layout(
                height=380,
                xaxis_title="Efficiency Score",
                yaxis_title="Factory → Route",
                margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_bottom_routes, use_container_width=True, config=PLOTLY_CONFIG)

        with st.expander("View detailed route tables"):
            st.markdown("**Top 10 Efficient Routes — Table**")
            st.dataframe(
                top_10_routes,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("**Bottom 10 Least Efficient Routes — Table**")
            st.dataframe(
                bottom_10_routes,
                use_container_width=True,
                hide_index=True
            )

        st.info("ℹ️ Efficiency Score is calculated based on normalized lead time performance across routes. Higher score indicates better (faster) delivery efficiency.")
        
        st.markdown("### Route Performance Leaderboard (Top Routes by Efficiency Score)")
        route_display = route_stats.copy()
        for col in ["Avg_Lead_Time", "Delay_Frequency", "Efficiency_Score"]:
            if col in route_display.columns:
                route_display[col] = route_display[col].round(1)

        leaderboard_cols = [
            col for col in [
                "Route_State", "Total_Shipments", "Avg_Lead_Time",
                "Efficiency_Score"
            ] if col in route_display.columns
        ]
        
        st.dataframe(
            route_display.sort_values("Efficiency_Score", ascending=False)[leaderboard_cols].head(15),
            use_container_width=True,
            hide_index=True
        )

# -------------------------
# TAB 2 - GEOGRAPHIC VIEW
# -------------------------
with tab2:
    c1, c2 = st.columns([1.6, 1])

    with c1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">🗺 Geographic Shipping Map</div>
            <div class="section-subtitle">
                U.S. heatmap of state-level shipping lead time (efficiency indicator).
            </div>
        """, unsafe_allow_html=True)

        if state_stats.empty:
            st.warning("No state-level data available for the selected filters.")
        else:
            us_map_df = state_stats[state_stats["State/Province"].isin(STATE_ABBR.keys())].copy()
            us_map_df["State_Code"] = us_map_df["State/Province"].map(STATE_ABBR)

            if us_map_df.empty:
                st.info("No U.S. states available in the current filtered selection.")
            else:
                fig_map = px.choropleth(
                    us_map_df,
                    locations="State_Code",
                    locationmode="USA-states",
                    color="Avg_Lead_Time",
                    scope="usa",
                    hover_name="State/Province",
                    hover_data={
                        "State_Code": False,
                        "Avg_Lead_Time": ':.2f',
                        "Total_Shipments": True,
                        "Delay_Frequency": ':.1f'
                    },
                    color_continuous_scale="YlOrBr"
                )
                fig_map.update_layout(
                    height=450,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_map, use_container_width=True, config=PLOTLY_CONFIG)

        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📍 Bottleneck Summary</div>
            <div class="section-subtitle">
                Regional bottlenecks and state-level risk signals.
            </div>
        """, unsafe_allow_html=True)

        if region_stats.empty:
            st.info("No regional summary available.")
        else:
            fig_region = px.bar(
                region_stats.sort_values("Avg_Lead_Time", ascending=False),
                x="Route_Region",
                y="Avg_Lead_Time",
                text="Avg_Lead_Time",
                color="Avg_Lead_Time",
                color_continuous_scale="YlOrBr"
            )
            fig_region.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_region.update_layout(
                height=250,
                xaxis_tickangle=-45,
                xaxis_title="Factory → Region",
                yaxis_title="Avg Lead Time",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_region, use_container_width=True, config=PLOTLY_CONFIG)

            st.info("⚠ Bottlenecks are identified based on high shipment volume and high average lead time (top 25% threshold).")

        if not state_stats.empty:
            bottlenecks = state_stats[state_stats["Bottleneck_Flag"] == "Bottleneck"].copy()
            st.markdown("### Geographic Bottlenecks")
            if bottlenecks.empty:
                st.success("No bottleneck states detected for the selected filters.")
            else:
                st.dataframe(
                    bottlenecks.sort_values(["Avg_Lead_Time", "Total_Shipments"], ascending=False),
                    use_container_width=True,
                    hide_index=True
                )

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# TAB 3 - SHIP MODE ANALYSIS
# -------------------------
with tab3:
    c1, c2 = st.columns([1.2, 1.2])

    with c1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">🚚 Ship Mode Lead Time Comparison</div>
            <div class="section-subtitle">
                Lead-time comparison and ship-mode performance ranking.
            </div>
        """, unsafe_allow_html=True)

        if ship_stats.empty:
            st.warning("No ship mode data available.")
        else:
            fig_ship = px.bar(
                ship_stats.sort_values("Avg_Lead_Time", ascending=True),
                x="Ship Mode",
                y="Avg_Lead_Time",
                text="Avg_Lead_Time",
                color="Avg_Lead_Time",
                color_continuous_scale="YlOrBr"
            )
            fig_ship.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_ship.update_layout(
                height=360,
                xaxis_title="Ship Mode",
                yaxis_title="Average Lead Time (Days)",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_ship, use_container_width=True, config=PLOTLY_CONFIG)

            st.info("ℹ Delay % is calculated based on lead-time threshold. Ship modes with average lead time below threshold may show 0% delay.")

            st.markdown("### Ship Mode Summary")
            ship_display = ship_stats.copy()
            for col in ["Avg_Lead_Time", "Lead_Time_Std", "Delayed", "On_Time"]:
                if col in ship_display.columns:
                    ship_display[col] = ship_display[col].round(1)

            ship_summary_cols = [
                col for col in [
                    "Ship Mode", "Total_Shipments", "Avg_Lead_Time",
                    "Delayed", "On_Time", "Efficiency_Rank"
                ] if col in ship_display.columns
            ]
            st.dataframe(ship_display[ship_summary_cols], use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📉 Delay vs On-Time</div>
            <div class="section-subtitle">
                Delay frequency and on-time performance by ship mode.
            </div>
        """, unsafe_allow_html=True)

        if ship_stats.empty:
            st.info("No ship mode performance available.")
        else:
            ship_long = ship_stats.melt(
                id_vars="Ship Mode",
                value_vars=["Delayed", "On_Time"],
                var_name="Status",
                value_name="Percentage"
            )

            ship_long["Status"] = ship_long["Status"].map({
                "Delayed": "Delayed %",
                "On_Time": "On-Time %"
            })

            fig_delay = px.bar(
                ship_long,
                x="Ship Mode",
                y="Percentage",
                color="Status",
                barmode="group",
                text="Percentage"
            )
            fig_delay.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig_delay.update_layout(
                height=360,
                xaxis_title="Ship Mode",
                yaxis_title="Percentage",
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_delay, use_container_width=True, config=PLOTLY_CONFIG)

            best_mode = ship_stats.sort_values("Avg_Lead_Time", ascending=True).iloc[0]
            worst_mode = ship_stats.sort_values("Avg_Lead_Time", ascending=False).iloc[0]

            st.markdown(f"""
            <div class="small-card-grid">
                <div class="small-info-card">
                    <div class="small-info-title">🥇 Best Mode</div>
                    <div class="small-info-text">{best_mode['Ship Mode']}<br>{best_mode['Avg_Lead_Time']:.2f} days avg lead time</div>
                </div>
                <div class="small-info-card">
                    <div class="small-info-title">⚠ Slowest Mode</div>
                    <div class="small-info-text">{worst_mode['Ship Mode']}<br>{worst_mode['Avg_Lead_Time']:.2f} days avg lead time</div>
                </div>
                <div class="small-info-card">
                    <div class="small-info-title">📌 Best Rank</div>
                    <div class="small-info-text">{best_mode['Ship Mode']}<br>Rank #{int(best_mode['Efficiency_Rank'])}</div>
                </div>
                <div class="small-info-card">
                    <div class="small-info-title">⏱ Threshold Context</div>
                    <div class="small-info-text">{lead_time_threshold} days<br>Used for delay calculation</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# TAB 4 - ROUTE DRILL-DOWN
# -------------------------
with tab4:
    route_options = sorted(filtered_df["Route_State"].dropna().unique().tolist()) if not filtered_df.empty else []

    selected_route = st.selectbox(
        "Select Route for Drill-Down",
        options=route_options if route_options else ["No Routes Available"]
    )

    c1, c2 = st.columns([1.45, 1])

    with c1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">🔎 Route Drill-Down Panel (Order Timeline Analysis)</div>
            <div class="section-subtitle">
                Route performance insights and shipment timeline.
            </div>
        """, unsafe_allow_html=True)

        if filtered_df.empty or selected_route == "No Routes Available":
            st.warning("No route details available for the selected filters.")
        else:
            drill_df = filtered_df[filtered_df["Route_State"] == selected_route].copy()
            drill_df = drill_df.sort_values("Order Date")

            if drill_df.empty:
                st.info("No records available for the selected route.")
            else:

                st.info("Green = On-Time shipments | Red = Delayed shipments based on lead-time threshold.")


                fig_timeline = px.line(
                    drill_df,
                    x="Order Date",
                    y="Shipping Lead Time",
                    color="Dynamic Delay Status",
                    markers=True,
                    color_discrete_map={
                        "On-Time": "green",
                        "Delayed": "red"
                    },
                    hover_data={
                        "Ship Mode": True,
                        "Factory": True,
                        "State/Province": True,
                        "Region": True,
                        "Dynamic Delay Status": True
                    }
                )

                fig_timeline.update_layout(
                    height=350,
                    xaxis_title="Order Date",
                    yaxis_title="Shipping Lead Time (Days)",
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(255,255,255,0.3)",
                    legend_title_text="Shipment Status"
                )

                st.plotly_chart(fig_timeline, use_container_width=True, config=PLOTLY_CONFIG)

                st.markdown("### Order-Level Shipment Records")
                display_cols = [
                    col for col in [
                        "Order ID", "Order Date", "Ship Date", "Ship Mode",
                        "Factory", "State/Province", "Region",
                        "Shipping Lead Time", "Dynamic Delay Status"
                    ] if col in drill_df.columns
                ]
                st.dataframe(drill_df[display_cols], use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📌 Selected Route Details</div>
            <div class="section-subtitle">
                Route details, delay signals, and analyst recommendation.
            </div>
        """, unsafe_allow_html=True)

        if filtered_df.empty or selected_route == "No Routes Available":
            st.info("No selected route details available.")
        else:
            detail_df = filtered_df[filtered_df["Route_State"] == selected_route].copy()

            if not detail_df.empty:
                route_orders = len(detail_df)
                route_avg = detail_df["Shipping Lead Time"].mean()
                route_delay = (detail_df["Dynamic Delay Status"] == "Delayed").mean() * 100
                route_factory = safe_mode(detail_df["Factory"]) if "Factory" in detail_df.columns else "N/A"
                route_state = safe_mode(detail_df["State/Province"]) if "State/Province" in detail_df.columns else "N/A"
                route_region = safe_mode(detail_df["Region"]) if "Region" in detail_df.columns else "N/A"

                coord_text = "Coordinates unavailable"
                if route_factory in FACTORY_COORDS:
                    coord_text = f"{FACTORY_COORDS[route_factory]['lat']}, {FACTORY_COORDS[route_factory]['lon']}"

                st.markdown(f"""
                <div class="small-card-grid">
                    <div class="small-info-card">
                        <div class="small-info-title">Factory</div>
                        <div class="small-info-text">{route_factory}</div>
                    </div>
                    <div class="small-info-card">
                        <div class="small-info-title">State</div>
                        <div class="small-info-text">{route_state}</div>
                    </div>
                    <div class="small-info-card">
                        <div class="small-info-title">Region</div>
                        <div class="small-info-text">{route_region}</div>
                    </div>
                    <div class="small-info-card">
                        <div class="small-info-title">Factory Coordinates</div>
                        <div class="small-info-text">{coord_text}</div>
                    </div>
                    <div class="small-info-card">
                        <div class="small-info-title">Route Orders</div>
                        <div class="small-info-text">{route_orders}</div>
                    </div>
                    <div class="small-info-card">
                        <div class="small-info-title">Avg Lead Time</div>
                        <div class="small-info-text">{route_avg:.2f} days</div>
                    </div>
                    <div class="small-info-card">
                        <div class="small-info-title">Delay Frequency</div>
                        <div class="small-info-text">{route_delay:.1f}%</div>
                    </div>
                    <div class="small-info-card">
                        <div class="small-info-title">Current Threshold</div>
                        <div class="small-info-text">{lead_time_threshold} days</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                route_reco = "Route performance is stable."
                if route_delay > 50:
                    route_reco = "High delay risk. Review this route for faster shipping mode allocation or operational bottlenecks."
                elif route_avg > average_lead_time_kpi:
                    route_reco = "This route is slower than the overall route average. Consider route-specific optimization."
                elif route_avg <= average_lead_time_kpi:
                    route_reco = "This route is performing better than or close to the overall route average."

                st.markdown(f"""
                <div class="reco-box" style="margin-top:12px;">
                    <div class="reco-title">🧠 Analyst Note</div>
                    <div class="reco-text">{route_reco}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# TAB 5 - TRENDS
# -------------------------
with tab5:
    st.markdown("""
    <div class="section-card">
        <div class="section-title">📈 Shipping Trends, Insights & Recommendations</div>
        <div class="section-subtitle">
            Monthly lead-time trend, shipment volume trend, trend interpretation, and analyst recommendations.
        </div>
    """, unsafe_allow_html=True)

    if monthly_trend.empty:
        st.warning("No trend data available for the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        trend_df_display = monthly_trend.copy()

        # -------------------------
        # TREND CALCULATIONS
        # -------------------------
        
        trend_df_display["Month"] = pd.to_datetime(trend_df_display["Month"])
        trend_df_display["Month"] = trend_df_display["Month"].dt.strftime("%b %Y")
        
        latest_month = trend_df_display.iloc[-1]["Month"] if "Month" in trend_df_display.columns else "Latest Month"
        latest_lead = trend_df_display.iloc[-1]["Avg_Lead_Time"]
        latest_orders = trend_df_display.iloc[-1]["Orders"]

        max_lead = trend_df_display["Avg_Lead_Time"].max()
        min_lead = trend_df_display["Avg_Lead_Time"].min()
        avg_lead_overall = trend_df_display["Avg_Lead_Time"].mean()

        max_orders = trend_df_display["Orders"].max()
        min_orders = trend_df_display["Orders"].min()
        avg_orders_overall = trend_df_display["Orders"].mean()

        peak_order_month = trend_df_display.loc[trend_df_display["Orders"].idxmax(), "Month"]
        lowest_order_month = trend_df_display.loc[trend_df_display["Orders"].idxmin(), "Month"]

        highest_lead_month = trend_df_display.loc[trend_df_display["Avg_Lead_Time"].idxmax(), "Month"]
        lowest_lead_month = trend_df_display.loc[trend_df_display["Avg_Lead_Time"].idxmin(), "Month"]

        if len(trend_df_display) >= 2:
            previous_lead = trend_df_display.iloc[-2]["Avg_Lead_Time"]
            previous_orders = trend_df_display.iloc[-2]["Orders"]

            lead_change = latest_lead - previous_lead
            order_change = latest_orders - previous_orders

            if lead_change > 0:
                lead_trend_message = (
                    f"⚠ Shipping lead time increased in {latest_month} from "
                    f"{previous_lead:.2f} to {latest_lead:.2f} days."
                )
            elif lead_change < 0:
                lead_trend_message = (
                    f"✅ Shipping lead time improved in {latest_month} from "
                    f"{previous_lead:.2f} to {latest_lead:.2f} days."
                )
            else:
                lead_trend_message = (
                    f"ℹ Shipping lead time remained stable at {latest_lead:.2f} days in {latest_month}."
                )

            if order_change > 0:
                order_trend_message = (
                    f"📦 Order volume increased in {latest_month} from "
                    f"{int(previous_orders)} to {int(latest_orders)} shipments."
                )
            elif order_change < 0:
                order_trend_message = (
                    f"📦 Order volume declined in {latest_month} from "
                    f"{int(previous_orders)} to {int(latest_orders)} shipments."
                )
            else:
                order_trend_message = (
                    f"📦 Order volume remained stable at {int(latest_orders)} shipments in {latest_month}."
                )
        else:
            lead_trend_message = "ℹ Not enough monthly data available to identify the latest lead-time trend."
            order_trend_message = "ℹ Not enough monthly data available to identify the latest order-volume trend."

        # -------------------------
        # TOP KPI SNAPSHOT
        # -------------------------
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">📅 Latest Month</div>
                <div class="kpi-value" style="font-size:22px;">{latest_month}</div>
                <div class="kpi-note">Most recent month in trend view</div>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">⏱ Latest Avg Lead Time</div>
                <div class="kpi-value">{latest_lead:.2f}</div>
                <div class="kpi-note">Days in latest month</div>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">📦 Latest Monthly Orders</div>
                <div class="kpi-value">{int(latest_orders)}</div>
                <div class="kpi-note">Orders in latest month</div>
            </div>
            """, unsafe_allow_html=True)

        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">📊 Avg Monthly Lead Time</div>
                <div class="kpi-value">{avg_lead_overall:.2f}</div>
                <div class="kpi-note">Overall monthly average</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------
        # INSIGHTS & RECOMMENDATIONS
        # -------------------------
        insight_col, reco_col = st.columns([1.2, 1])

        with insight_col:
            st.markdown("""
            <div class="section-card">
                <div class="section-title">📌 Trend Insights</div>
                <div class="section-subtitle">
                    Key patterns identified from monthly lead time and shipment volume.
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">📈 Latest Lead-Time Movement</div>
                <div class="insight-text">{lead_trend_message}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">📦 Latest Volume Movement</div>
                <div class="insight-text">{order_trend_message}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">🚨 Highest Lead-Time Month</div>
                <div class="insight-text">
                    {highest_lead_month} recorded the highest monthly average lead time at {max_lead:.2f} days.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">✅ Best Lead-Time Month</div>
                <div class="insight-text">
                    {lowest_lead_month} recorded the lowest monthly average lead time at {min_lead:.2f} days.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">📦 Peak Volume Month</div>
                <div class="insight-text">
                    {peak_order_month} had the highest shipment volume with {int(max_orders)} orders, indicating peak operational load.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">📉 Lowest Volume Month</div>
                <div class="insight-text">
                    {lowest_order_month} had the lowest shipment volume with {int(min_orders)} orders.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with reco_col:
            st.markdown("""
            <div class="section-card">
                <div class="section-title">💡 Analyst Recommendations</div>
                <div class="section-subtitle">
                    Suggested actions based on trend behavior and shipment patterns.
                </div>
            """, unsafe_allow_html=True)

            if max_lead > avg_lead_overall + 0.3:
                st.markdown(f"""
                <div class="reco-box">
                    <div class="reco-title">Lead-Time Stabilization</div>
                    <div class="reco-text">
                        Investigate drivers behind the spike in {highest_lead_month}, as monthly lead time reached {max_lead:.2f} days and exceeded the overall trend average.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if max_orders > avg_orders_overall * 1.20:
                st.markdown(f"""
                <div class="reco-box">
                    <div class="reco-title">Peak Volume Planning</div>
                    <div class="reco-text">
                        {peak_order_month} shows a major shipment spike. Prepare additional operational capacity and route monitoring during peak-demand months.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if len(trend_df_display) >= 2 and latest_lead <= previous_lead:
                st.markdown(f"""
                <div class="reco-box">
                    <div class="reco-title">Maintain Current Performance</div>
                    <div class="reco-text">
                        Lead time is stable or improving in the latest month. Preserve the current fulfillment and shipping practices that are supporting better delivery consistency.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if len(trend_df_display) >= 2 and latest_orders > avg_orders_overall and latest_lead <= avg_lead_overall:
                st.markdown(f"""
                <div class="reco-box">
                    <div class="reco-title">Positive Capacity Signal</div>
                    <div class="reco-text">
                        The latest month handled above-average shipment volume while keeping lead time near or below the long-run average. This indicates relatively healthy logistics capacity under load.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="reco-box">
                <div class="reco-title">Monitoring Priority</div>
                <div class="reco-text">
                    Continue monthly tracking of both lead time and order volume together, because shipment spikes can directly impact delivery performance and route efficiency.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------
        # CHART SECTION
        # -------------------------
        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.markdown("""
            <div class="section-card">
                <div class="section-title">📉 Monthly Average Lead Time Trend</div>
                <div class="section-subtitle">
                    Month-by-month movement in shipping lead time.
                </div>
            """, unsafe_allow_html=True)

            fig_trend = px.line(
                trend_df_display,
                x="Month",
                y="Avg_Lead_Time",
                markers=True
            )
            fig_trend.update_layout(
                height=380,
                xaxis_title="Month",
                xaxis=dict(tickangle=-30),
                yaxis_title="Average Lead Time (Days)",
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_trend, use_container_width=True, config=PLOTLY_CONFIG)

            st.markdown("</div>", unsafe_allow_html=True)

        with chart_right:
            st.markdown("""
            <div class="section-card">
                <div class="section-title">📦 Monthly Order Volume Trend</div>
                <div class="section-subtitle">
                    Month-by-month shipment volume pattern.
                </div>
            """, unsafe_allow_html=True)

            fig_orders = px.bar(
                trend_df_display,
                x="Month",
                y="Orders",
                text="Orders"
            )
            fig_orders.update_traces(textposition="outside")
            fig_orders.update_layout(
                bargap=0.2,
                height=380,
                xaxis_title="Month",
                yaxis_title="Orders",
                xaxis=dict(tickangle=-30),
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.3)"
            )
            st.plotly_chart(fig_orders, use_container_width=True, config=PLOTLY_CONFIG)

            st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------
        # TREND DATA TABLE
        # -------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Monthly Trend Summary Table**")

        trend_table = trend_df_display.copy()
        if "Avg_Lead_Time" in trend_table.columns:
            trend_table["Avg_Lead_Time"] = trend_table["Avg_Lead_Time"].round(2)

        st.dataframe(trend_table, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# FOOTER SECTION
# -------------------------
st.markdown("---")

st.markdown("### 📌 Project Information & Credits")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
**👨‍💻 Developed by:** Mohit Gupta
  
**🎯 Role:** Data Analyst Intern
        """
    )

with c2:
    st.markdown(
        """
**📊 Project:** Factory-to-Customer Shipping Route Efficiency Analysis for Nassau Candy Distributor
  
**🏢 Organization:** Unified Mentor Pvt. Ltd.
        """
    )

with c3:
    st.markdown(
        """
**👨‍🏫 Mentor:** Saiprasad Kagne
  
**📅 Year:** 2026
        """
    )

st.markdown(
    """
<div style="
    text-align: center;
    margin-top: 10px;
    color: #6b563d;
    font-size: 14px;
    font-weight: 600;
">
    💡 Built using Python, Pandas, Plotly & Streamlit
</div>
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)