"""
Power BI-ready dataset builder for the Nassau Candy logistics project.

This script does not run Streamlit UI inside Power BI.
Instead, it prepares Power BI-ready CSV tables from the same processed data
used by your Streamlit dashboard.

How to use:
1. Keep this file in your project folder
2. Run: python powerbi_ready_dataset_builder.py
3. Load the exported CSV files from data/powerbi_ready/ into Power BI
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np


BASE_DIR = Path(".")
INPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "powerbi_ready"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def performance_category(score: float) -> str:
    if pd.isna(score):
        return "N/A"
    if score >= 70:
        return "High"
    if score >= 45:
        return "Average"
    return "Poor"


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_data() -> pd.DataFrame:
    df_main = pd.read_csv(INPUT_DIR / "dashboard_main.csv")

    df_main["Order Date"] = pd.to_datetime(df_main["Order Date"], dayfirst=True, errors="coerce")
    df_main["Ship Date"] = pd.to_datetime(df_main["Ship Date"], dayfirst=True, errors="coerce")
    df_main["Shipping Lead Time"] = safe_numeric(df_main["Shipping Lead Time"])

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

    df_main = df_main.dropna(subset=["Order Date", "Ship Date", "Shipping Lead Time"]).copy()
    return df_main


def build_powerbi_tables(delay_threshold: int = 5) -> dict[str, pd.DataFrame]:
    df_main = load_data()

    df_main["Dynamic Delay Status"] = np.where(
        df_main["Shipping Lead Time"] > delay_threshold,
        "Delayed",
        "On-Time"
    )
    df_main["Order Month"] = df_main["Order Date"].dt.to_period("M").astype(str)
    df_main["Order Year"] = df_main["Order Date"].dt.year
    df_main["Order Month Name"] = df_main["Order Date"].dt.strftime("%b %Y")

    route_stats = (
        df_main.groupby("Route_State", as_index=False)
        .agg(
            Total_Shipments=("Order ID", "count"),
            Unique_Orders=("Order ID", "nunique"),
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

    region_stats = (
        df_main.groupby("Route_Region", as_index=False)
        .agg(
            Total_Shipments=("Order ID", "count"),
            Unique_Orders=("Order ID", "nunique"),
            Avg_Lead_Time=("Shipping Lead Time", "mean"),
            Lead_Time_Std=("Shipping Lead Time", "std"),
            Min_Lead_Time=("Shipping Lead Time", "min"),
            Max_Lead_Time=("Shipping Lead Time", "max")
        )
    )

    state_stats = (
        df_main.groupby("State/Province", as_index=False)
        .agg(
            Total_Shipments=("Order ID", "count"),
            Unique_Orders=("Order ID", "nunique"),
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

    ship_mode_stats = (
        df_main.groupby("Ship Mode", as_index=False)
        .agg(
            Total_Shipments=("Order ID", "count"),
            Unique_Orders=("Order ID", "nunique"),
            Avg_Lead_Time=("Shipping Lead Time", "mean"),
            Lead_Time_Std=("Shipping Lead Time", "std"),
            Delayed=("Dynamic Delay Status", lambda x: (x == "Delayed").mean() * 100),
            On_Time=("Dynamic Delay Status", lambda x: (x == "On-Time").mean() * 100)
        )
    )

    if not ship_mode_stats.empty:
        ship_mode_stats["Efficiency_Rank"] = ship_mode_stats["Avg_Lead_Time"].rank(
            ascending=True,
            method="dense"
        ).astype(int)

    monthly_trend = (
        df_main.groupby("Order Month", as_index=False)
        .agg(
            Avg_Lead_Time=("Shipping Lead Time", "mean"),
            Orders=("Order ID", "count"),
            Unique_Orders=("Order ID", "nunique")
        )
        .sort_values("Order Month")
    )

    total_shipments = len(df_main)
    unique_orders = df_main["Order ID"].nunique()
    avg_shipments_per_order = total_shipments / unique_orders if unique_orders else 0
    shipping_lead_time = df_main["Shipping Lead Time"].median() if not df_main.empty else 0
    average_lead_time = df_main["Shipping Lead Time"].mean() if not df_main.empty else 0
    route_volume = route_stats["Total_Shipments"].mean() if not route_stats.empty else 0
    delay_frequency = (df_main["Dynamic Delay Status"] == "Delayed").mean() * 100 if not df_main.empty else 0
    route_efficiency_score = route_stats["Efficiency_Score"].mean() if not route_stats.empty else 0

    kpi_table = pd.DataFrame({
        "Metric": [
            "Shipping Lead Time",
            "Average Lead Time",
            "Route Volume",
            "Delay Frequency",
            "Route Efficiency Score",
            "Total Shipments",
            "Unique Orders",
            "Avg Shipments/Order",
        ],
        "Value": [
            shipping_lead_time,
            average_lead_time,
            route_volume,
            delay_frequency,
            route_efficiency_score,
            total_shipments,
            unique_orders,
            avg_shipments_per_order,
        ]
    })

    return {
        "fact_orders": df_main,
        "route_stats": route_stats,
        "region_stats": region_stats,
        "state_stats": state_stats,
        "ship_mode_stats": ship_mode_stats,
        "monthly_trend": monthly_trend,
        "kpi_table": kpi_table,
    }


def export_powerbi_tables(delay_threshold: int = 5) -> list[Path]:
    tables = build_powerbi_tables(delay_threshold=delay_threshold)
    exported_files = []

    for name, df in tables.items():
        path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        exported_files.append(path)

    return exported_files


if __name__ == "__main__":
    files = export_powerbi_tables(delay_threshold=5)
    print("Power BI-ready files exported:")
    for file in files:
        print(f"- {file}")
