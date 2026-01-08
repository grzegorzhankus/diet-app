"""
Dashboard page - Metrics and trends visualization
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import streamlit as st
import pandas as pd
from datetime import date, timedelta
import altair as alt

from core.storage import Storage
from core.metrics import MetricsEngine

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")

st.title("📈 Dashboard")
st.markdown("Trends, metrics, and analytics")

# Initialize
storage = Storage()
metrics = MetricsEngine(storage)

# Check if data exists
if storage.count() == 0:
    st.warning("No data in database. Go to **📝 Daily Entry** to add data or import historical data.")
    st.stop()

# Date range selector
st.subheader("Time Period")

col1, col2 = st.columns([3, 1])

with col1:
    period = st.selectbox(
        "Select Period",
        options=["Last 7 days", "Last 14 days", "Last 30 days", "Last 60 days", "Last 90 days", "Last 6 months", "Last year", "All time"],
        index=2  # Default: Last 30 days
    )

with col2:
    show_rolling_avg = st.checkbox("Show rolling averages", value=True)

# Map period to days
period_map = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 60 days": 60,
    "Last 90 days": 90,
    "Last 6 months": 180,
    "Last year": 365,
    "All time": None
}

days = period_map[period]

# Fetch metrics
if days:
    df = metrics.get_metrics_dataframe(days=days)
else:
    df = metrics.get_metrics_dataframe()

if df.empty:
    st.warning(f"No data for selected period: {period}")
    st.stop()

st.divider()

# Summary stats
st.subheader("Summary Statistics")

stats = metrics.get_summary_stats(days=days if days else 365)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Current Weight",
        f"{stats['weight_current_kg']:.1f} kg",
        delta=f"{stats['weight_change_kg']:+.1f} kg",
        help=f"Change over {stats['period_days']} days"
    )

with col2:
    if stats.get('weight_7d_avg_kg'):
        st.metric(
            "7-Day Average",
            f"{stats['weight_7d_avg_kg']:.1f} kg",
            help="7-day rolling average"
        )
    else:
        st.metric("7-Day Average", "N/A")

with col3:
    if stats.get('fm_current_kg'):
        st.metric(
            "Fat Mass",
            f"{stats['fm_current_kg']:.1f} kg",
            help="Most recent fat mass in kg"
        )
    else:
        st.metric("Fat Mass", "N/A")

with col4:
    if stats.get('cal_net_avg_kcal'):
        st.metric(
            "Avg NET Calories",
            f"{stats['cal_net_avg_kcal']:.0f} kcal",
            help="Average daily net calorie balance (IN - BMR[2000] - SPORT)"
        )
    else:
        st.metric("Avg NET Calories", "N/A")

st.divider()

# Weight trend chart
st.subheader("Weight Trend")

# Prepare data for chart
chart_data = df[['date', 'bs_weight_kg']].copy()
chart_data['date'] = pd.to_datetime(chart_data['date'])

# Base weight line
weight_chart = alt.Chart(chart_data).mark_line(
    color='#1f77b4',
    strokeWidth=2
).encode(
    x=alt.X('date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d')),
    y=alt.Y('bs_weight_kg:Q', title='Weight (kg)', scale=alt.Scale(zero=False)),
    tooltip=[
        alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('bs_weight_kg:Q', title='Weight (kg)', format='.1f')
    ]
).properties(
    height=400
)

# Add rolling averages if requested
layers = [weight_chart]

if show_rolling_avg and 'bs_weight_7d_avg_kg' in df.columns:
    # 7-day rolling average
    ra_7d_data = df[['date', 'bs_weight_7d_avg_kg']].dropna().copy()
    ra_7d_data['date'] = pd.to_datetime(ra_7d_data['date'])

    ra_7d_chart = alt.Chart(ra_7d_data).mark_line(
        color='#ff7f0e',
        strokeWidth=2,
        strokeDash=[5, 5]
    ).encode(
        x='date:T',
        y=alt.Y('bs_weight_7d_avg_kg:Q', title=''),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('bs_weight_7d_avg_kg:Q', title='7d Avg (kg)', format='.1f')
        ]
    )
    layers.append(ra_7d_chart)

    # 14-day rolling average
    if 'bs_weight_14d_avg_kg' in df.columns:
        ra_14d_data = df[['date', 'bs_weight_14d_avg_kg']].dropna().copy()
        ra_14d_data['date'] = pd.to_datetime(ra_14d_data['date'])

        ra_14d_chart = alt.Chart(ra_14d_data).mark_line(
            color='#2ca02c',
            strokeWidth=2,
            strokeDash=[10, 5]
        ).encode(
            x='date:T',
            y=alt.Y('bs_weight_14d_avg_kg:Q', title=''),
            tooltip=[
                alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
                alt.Tooltip('bs_weight_14d_avg_kg:Q', title='14d Avg (kg)', format='.1f')
            ]
        )
        layers.append(ra_14d_chart)

final_chart = alt.layer(*layers).resolve_scale(y='shared')

st.altair_chart(final_chart, width='stretch')

# Legend
if show_rolling_avg:
    st.caption("🔵 Daily Weight | 🟠 7-day avg (dashed) | 🟢 14-day avg (dashed)")
else:
    st.caption("🔵 Daily Weight")

st.divider()

# Fat mass trend (if data exists)
if df['bs_fat_mass_kg'].notna().any():
    st.subheader("Fat Mass Trend")

    fm_data = df[['date', 'bs_fat_mass_kg']].dropna().copy()
    fm_data['date'] = pd.to_datetime(fm_data['date'])

    fm_chart = alt.Chart(fm_data).mark_line(
        color='#d62728',
        strokeWidth=2,
        point=True
    ).encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('bs_fat_mass_kg:Q', title='Fat Mass (kg)', scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('bs_fat_mass_kg:Q', title='Fat Mass (kg)', format='.1f')
        ]
    ).properties(
        height=300
    )

    st.altair_chart(fm_chart, width='stretch')
    st.divider()

# Calorie balance chart (if data exists)
if df['cal_net_kcal'].notna().any():
    st.subheader("Calorie Balance")

    cal_data = df[['date', 'cal_in_kcal', 'cal_out_sport_kcal', 'cal_net_kcal']].dropna(subset=['cal_net_kcal']).copy()
    cal_data['date'] = pd.to_datetime(cal_data['date'])

    # Net calories bar chart
    cal_chart = alt.Chart(cal_data).mark_bar().encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('cal_net_kcal:Q', title='Net Calories (kcal)'),
        color=alt.condition(
            alt.datum.cal_net_kcal > 0,
            alt.value('#d62728'),  # Red for surplus
            alt.value('#2ca02c')   # Green for deficit
        ),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('cal_in_kcal:Q', title='IN (kcal)', format='.0f'),
            alt.Tooltip('cal_out_sport_kcal:Q', title='SPORT (kcal)', format='.0f'),
            alt.Tooltip('cal_net_kcal:Q', title='NET (kcal)', format='.0f')
        ]
    ).properties(
        height=300
    )

    st.altair_chart(cal_chart, width='stretch')
    st.caption("🔴 Surplus (positive) | 🟢 Deficit (negative) | NET = IN - BMR(2000) - SPORT")

    # Show rolling average for net calories
    if show_rolling_avg and 'cal_net_7d_avg_kcal' in df.columns:
        cal_avg_data = df[['date', 'cal_net_7d_avg_kcal']].dropna().copy()
        cal_avg_data['date'] = pd.to_datetime(cal_avg_data['date'])

        cal_avg_chart = alt.Chart(cal_avg_data).mark_line(
            color='#ff7f0e',
            strokeWidth=2
        ).encode(
            x='date:T',
            y=alt.Y('cal_net_7d_avg_kcal:Q', title='7d Avg NET (kcal)'),
            tooltip=[
                alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
                alt.Tooltip('cal_net_7d_avg_kcal:Q', title='7d Avg NET', format='.0f')
            ]
        ).properties(
            height=200
        )

        st.altair_chart(cal_avg_chart, width='stretch')
        st.caption("🟠 7-day rolling average NET calories")

# Footer
st.divider()
st.caption(f"Showing {len(df)} days of data | Data coverage: {stats.get('data_coverage', 0):.1f}%")
