"""
KPIs page - Key Performance Indicators
"""
import streamlit as st
from core.storage import Storage
from core.kpi_engine import KPIEngine

st.set_page_config(page_title="KPIs", page_icon="📊", layout="wide")

st.title("📊 Key Performance Indicators")
st.markdown("Track your progress with 12 data-driven KPIs")

# Initialize
storage = Storage()
kpi_engine = KPIEngine(storage, target_weight_kg=75.0)

# Check if data exists
if storage.count() == 0:
    st.warning("No data in database. Go to **📝 Daily Entry** to add data.")
    st.stop()

# Period selector
st.subheader("Analysis Period")

col1, col2 = st.columns([3, 1])

with col1:
    period = st.selectbox(
        "Select Period",
        options=["Last 7 days", "Last 14 days", "Last 30 days", "Last 60 days", "Last 90 days"],
        index=2  # Default: Last 30 days
    )

with col2:
    target_weight = st.number_input(
        "Target Weight (kg)",
        min_value=50.0,
        max_value=150.0,
        value=75.0,
        step=0.5
    )

# Map period to days
period_map = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 60 days": 60,
    "Last 90 days": 90
}

days = period_map[period]

# Update target
kpi_engine.target_weight_kg = target_weight

# Compute KPIs
with st.spinner("Computing KPIs..."):
    kpis = kpi_engine.compute_all_kpis(days=days)

if not kpis:
    st.warning(f"Insufficient data for KPI calculation. Need at least 7 days with data.")
    st.stop()

st.divider()

# Summary metrics at top
st.subheader("Quick Summary")

# Find key KPIs for summary
kpi_dict = {kpi.id: kpi for kpi in kpis}

col1, col2, col3, col4 = st.columns(4)

with col1:
    if 'KPI_Weight_Change_30d' in kpi_dict:
        kpi = kpi_dict['KPI_Weight_Change_30d']
        delta_color = "inverse" if kpi.value < 0 else "normal"
        st.metric(
            "Weight Change",
            f"{kpi.value:+.1f} kg",
            delta=f"{kpi.value:+.1f} kg",
            delta_color=delta_color,
            help=kpi.explanation
        )

with col2:
    if 'KPI_Weight_Trend_7d' in kpi_dict:
        kpi = kpi_dict['KPI_Weight_Trend_7d']
        delta_color = "inverse" if kpi.value < 0 else "normal"
        st.metric(
            "Trend (7d)",
            f"{kpi.value:+.2f} kg/week",
            delta=f"{kpi.value:+.2f} kg/week",
            delta_color=delta_color,
            help=kpi.explanation
        )

with col3:
    if 'KPI_Adherence_Score' in kpi_dict:
        kpi = kpi_dict['KPI_Adherence_Score']
        st.metric(
            "Adherence Score",
            f"{int(kpi.value)}/100",
            delta="Good" if kpi.is_good else "Needs improvement",
            delta_color="normal" if kpi.is_good else "inverse",
            help=kpi.explanation
        )

with col4:
    if 'KPI_Goal_ETA' in kpi_dict:
        kpi = kpi_dict['KPI_Goal_ETA']
        if kpi.value:
            st.metric(
                "Goal ETA",
                f"{int(kpi.value)} days",
                delta=f"~{int(kpi.value/30)} months",
                help=kpi.explanation
            )
        else:
            st.metric("Goal ETA", "N/A", help="Not losing weight currently")

st.divider()

# Categorize KPIs
weight_kpis = []
calorie_kpis = []
consistency_kpis = []
other_kpis = []

for kpi in kpis:
    if 'Weight' in kpi.id or 'BF' in kpi.id or 'FatMass' in kpi.id:
        weight_kpis.append(kpi)
    elif 'Calories' in kpi.id or 'Intake' in kpi.id or 'Sport' in kpi.id:
        calorie_kpis.append(kpi)
    elif 'Consistency' in kpi.id or 'Streak' in kpi.id or 'Volatility' in kpi.id:
        consistency_kpis.append(kpi)
    else:
        other_kpis.append(kpi)

# Display categorized KPIs
def display_kpi_card(kpi):
    """Display a single KPI card."""
    # Determine color based on is_good
    if kpi.is_good is True:
        border_color = "#2ca02c"  # Green
        emoji = "✅"
    elif kpi.is_good is False:
        border_color = "#d62728"  # Red
        emoji = "⚠️"
    else:
        border_color = "#1f77b4"  # Blue
        emoji = "📊"

    with st.container():
        # Create colored border effect
        st.markdown(f"""
        <div style="border-left: 4px solid {border_color}; padding-left: 10px;">
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{emoji} {kpi.name}**")
            if kpi.value is not None:
                st.markdown(f"<h2 style='margin: 0;'>{kpi.value} {kpi.unit}</h2>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h2 style='margin: 0;'>N/A</h2>", unsafe_allow_html=True)

        with col2:
            if kpi.target is not None:
                st.caption(f"Target: {kpi.target} {kpi.unit}")
            st.caption(f"Window: {kpi.window_days}d")

        with st.expander("ℹ️ Details"):
            st.caption(f"**Explanation:** {kpi.explanation}")
            st.caption(f"**Formula:** `{kpi.formula}`")
            if kpi.target is not None:
                status = "✅ On track" if kpi.is_good else "⚠️ Needs attention"
                st.caption(f"**Status:** {status}")

        st.markdown("</div>", unsafe_allow_html=True)

# Weight & Body Composition
if weight_kpis:
    st.subheader("⚖️ Weight & Body Composition")
    for kpi in weight_kpis:
        display_kpi_card(kpi)
        st.divider()

# Calories & Energy Balance
if calorie_kpis:
    st.subheader("🔥 Calories & Energy Balance")
    for kpi in calorie_kpis:
        display_kpi_card(kpi)
        st.divider()

# Consistency & Behavior
if consistency_kpis:
    st.subheader("📅 Consistency & Behavior")
    for kpi in consistency_kpis:
        display_kpi_card(kpi)
        st.divider()

# Other KPIs
if other_kpis:
    st.subheader("🎯 Goals & Overall")
    for kpi in other_kpis:
        display_kpi_card(kpi)
        st.divider()

# Export KPIs as JSON
st.subheader("📥 Export KPIs")

if st.button("Download KPIs as JSON"):
    import json
    from datetime import date

    kpi_export = {
        'export_date': date.today().isoformat(),
        'period_days': days,
        'target_weight_kg': target_weight,
        'kpis': [kpi.to_dict() for kpi in kpis]
    }

    json_str = json.dumps(kpi_export, indent=2)

    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name=f"kpis_{date.today()}.json",
        mime="application/json"
    )

# Footer
st.divider()
st.caption(f"Computed {len(kpis)} KPIs over {days} days")
