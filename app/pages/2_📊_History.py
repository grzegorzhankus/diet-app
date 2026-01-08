"""
History page - View all entries with filtering
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
from core.storage import Storage

st.set_page_config(page_title="History", page_icon="📊", layout="wide")

st.title("📊 Data History")
st.markdown("View and analyze your historical data")

# Initialize storage
storage = Storage()

# Filters
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    start_date = st.date_input(
        "From Date",
        value=date.today() - timedelta(days=30),
        max_value=date.today()
    )

with col2:
    end_date = st.date_input(
        "To Date",
        value=date.today(),
        max_value=date.today()
    )

with col3:
    limit = st.number_input(
        "Max Rows",
        min_value=10,
        max_value=1000,
        value=100,
        step=10
    )

# Fetch data
entries = storage.get_all(
    limit=limit,
    start_date=start_date,
    end_date=end_date
)

st.divider()

# Statistics
if entries:
    col1, col2, col3, col4 = st.columns(4)

    weights = [e.weight_kg for e in entries]
    bf_values = [e.bodyfat_pct for e in entries if e.bodyfat_pct]
    # Calculate fat mass for entries with body fat %
    fat_mass_values = [e.weight_kg * (e.bodyfat_pct / 100.0) for e in entries if e.bodyfat_pct]

    with col1:
        st.metric(
            "Total Entries",
            len(entries)
        )

    with col2:
        st.metric(
            "Avg Weight",
            f"{sum(weights) / len(weights):.1f} kg"
        )

    with col3:
        if fat_mass_values:
            st.metric(
                "Avg Fat Mass",
                f"{sum(fat_mass_values) / len(fat_mass_values):.1f} kg"
            )
        else:
            st.metric("Avg Fat Mass", "N/A")

    with col4:
        weight_change = weights[-1] - weights[0]
        st.metric(
            "Weight Change",
            f"{weight_change:+.1f} kg",
            delta=f"{weight_change:+.1f} kg"
        )

    st.divider()

    # Data table
    st.subheader("Data Table")

    # Convert to DataFrame
    data = []
    for entry in entries:
        # Calculate fat mass if body fat % is available
        fat_mass = (entry.weight_kg * (entry.bodyfat_pct / 100.0)) if entry.bodyfat_pct else None

        row = {
            'Date': entry.date,
            'Weight (kg)': entry.weight_kg,
            'Fat Mass (kg)': fat_mass,
            'Cal IN (kcal)': entry.cal_in_kcal if entry.cal_in_kcal else None,
            'Exercise OUT (kcal)': entry.cal_out_sport_kcal if entry.cal_out_sport_kcal else None,
            'NET (kcal)': (entry.cal_in_kcal - 2000.0 - (entry.cal_out_sport_kcal or 0))
                if entry.cal_in_kcal else None,
            'Source': entry.source
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Display as interactive table
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            'Date': st.column_config.DateColumn('Date', format='YYYY-MM-DD'),
            'Weight (kg)': st.column_config.NumberColumn('Weight (kg)', format='%.1f'),
            'Fat Mass (kg)': st.column_config.NumberColumn('Fat Mass (kg)', format='%.1f'),
            'Cal IN (kcal)': st.column_config.NumberColumn('Cal IN', format='%.0f'),
            'Exercise OUT (kcal)': st.column_config.NumberColumn('Exercise OUT', format='%.0f'),
            'NET (kcal)': st.column_config.NumberColumn('NET (IN-BMR-SPORT)', format='%.0f'),
        }
    )

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f"diet_app_export_{date.today()}.csv",
        mime="text/csv"
    )

else:
    st.info("No entries found for the selected date range.")

# Footer
st.divider()
st.caption(f"Total entries in database: {storage.count()}")
