"""
Red Flags page - Anomaly detection and warnings
"""
import streamlit as st
from datetime import date, timedelta

from core.storage import Storage
from core.red_flags import RedFlagsEngine

st.set_page_config(page_title="Red Flags", page_icon="🚩", layout="wide")

st.title("🚩 Red Flags")
st.markdown("Anomaly detection and potential issues in your tracking data")

# Initialize
storage = Storage()
engine = RedFlagsEngine(storage, bmr_kcal=2000.0)

# Check if data exists
if storage.count() == 0:
    st.warning("No data in database. Go to **📝 Daily Entry** to add data or import historical data.")
    st.stop()

# Time period selector
st.subheader("Analysis Period")

col1, col2 = st.columns([3, 1])

with col1:
    days = st.selectbox(
        "Period to analyze",
        options=[7, 14, 30, 60, 90],
        index=2,  # Default: 30 days
        format_func=lambda x: f"Last {x} days"
    )

with col2:
    severity_filter = st.multiselect(
        "Filter by severity",
        options=['critical', 'high', 'medium', 'low'],
        default=['critical', 'high', 'medium', 'low']
    )

st.divider()

# Detect all flags
with st.spinner("Analyzing data for anomalies..."):
    all_flags = engine.detect_all_flags(days=days)

# Filter by severity
flags = [f for f in all_flags if f.severity in severity_filter]

# Summary stats
st.subheader("Summary")

col1, col2, col3, col4 = st.columns(4)

critical_count = len([f for f in flags if f.severity == 'critical'])
high_count = len([f for f in flags if f.severity == 'high'])
medium_count = len([f for f in flags if f.severity == 'medium'])
low_count = len([f for f in flags if f.severity == 'low'])

with col1:
    st.metric("🔴 Critical", critical_count)

with col2:
    st.metric("🟠 High", high_count)

with col3:
    st.metric("🟡 Medium", medium_count)

with col4:
    st.metric("🟢 Low", low_count)

st.divider()

# Display flags
if len(flags) == 0:
    st.success(f"✅ No issues detected in the last {days} days! Your tracking looks great.")
    st.balloons()
else:
    st.subheader(f"Detected Issues ({len(flags)})")

    # Group by category
    categories = {
        'health': '🏥 Health Concerns',
        'data_quality': '📊 Data Quality',
        'consistency': '📈 Consistency',
        'progress': '🎯 Progress'
    }

    # Sort flags by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_flags = sorted(flags, key=lambda f: severity_order.get(f.severity, 99))

    for category_id, category_name in categories.items():
        category_flags = [f for f in sorted_flags if f.category == category_id]

        if len(category_flags) > 0:
            st.markdown(f"### {category_name}")

            for flag in category_flags:
                # Severity icon
                severity_icons = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }
                icon = severity_icons.get(flag.severity, '⚪')

                # Severity color
                severity_colors = {
                    'critical': 'red',
                    'high': 'orange',
                    'medium': 'yellow',
                    'low': 'green'
                }
                color = severity_colors.get(flag.severity, 'gray')

                # Display flag in expander
                with st.expander(f"{icon} **{flag.title}**", expanded=(flag.severity in ['critical', 'high'])):
                    st.markdown(f"**Severity:** :{color}[{flag.severity.upper()}]")
                    st.markdown(f"**Description:** {flag.description}")

                    # Show value and threshold if available
                    if flag.value is not None and flag.threshold is not None:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Value", f"{flag.value:.1f}")
                        with col2:
                            st.metric("Threshold", f"{flag.threshold:.1f}")

                    # Show affected dates if available
                    if flag.dates_affected and len(flag.dates_affected) > 0:
                        if len(flag.dates_affected) <= 5:
                            dates_str = ", ".join([d.strftime("%Y-%m-%d") for d in flag.dates_affected])
                            st.markdown(f"**Dates affected:** {dates_str}")
                        else:
                            st.markdown(f"**Dates affected:** {len(flag.dates_affected)} days")

                    # Show recommendation
                    if flag.recommendation:
                        st.info(f"💡 **Recommendation:** {flag.recommendation}")

            st.divider()

# Export section
st.subheader("Export")

if len(flags) > 0:
    # Prepare export data
    export_data = []
    for flag in flags:
        export_data.append({
            'Severity': flag.severity,
            'Category': flag.category,
            'Title': flag.title,
            'Description': flag.description,
            'Value': flag.value,
            'Threshold': flag.threshold,
            'Recommendation': flag.recommendation
        })

    import pandas as pd
    df_export = pd.DataFrame(export_data)

    # Display table
    st.dataframe(
        df_export,
        width='stretch',
        hide_index=True
    )

    # Download button
    csv = df_export.to_csv(index=False)
    st.download_button(
        label="📥 Download Red Flags Report (CSV)",
        data=csv,
        file_name=f"red_flags_{date.today().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        width='stretch'
    )

# Footer
st.divider()
st.caption(f"Analyzed {days} days of data | {len(all_flags)} total flags detected")
st.caption("Red flags are automatically detected based on your tracking patterns and health guidelines.")
