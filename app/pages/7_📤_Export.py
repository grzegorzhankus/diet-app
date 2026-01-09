"""
Export page - Download comprehensive reports
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import streamlit as st
from datetime import date
import io

from core.storage import Storage
from core.i18n import t, get_text

from core.export import ExportEngine
from core.pdf_export import PDFExportEngine

st.set_page_config(page_title="Export", page_icon="📤", layout="wide", initial_sidebar_state="expanded")

st.title("📤 Export Data")
st.markdown("Download comprehensive reports in Excel or CSV format")

# Initialize
storage = Storage()
bmr_kcal = 2000.0  # TODO: Make this configurable from user settings
target_weight_kg = 75.0  # TODO: Make this configurable from user settings

engine = ExportEngine(storage, bmr_kcal=bmr_kcal, target_weight_kg=target_weight_kg)
pdf_engine = PDFExportEngine(storage, bmr_kcal=bmr_kcal, target_weight_kg=target_weight_kg)

# Check if data exists
if storage.count() == 0:
    st.warning("No data available to export. Go to **📝 Daily Entry** to add data.")
    st.stop()

st.divider()

# Export configuration
st.subheader("📋 Export Configuration")

col1, col2 = st.columns(2)

with col1:
    export_format = st.selectbox(
        "Export format",
        options=['excel', 'pdf', 'csv'],
        index=0,
        format_func=lambda x: {
            'excel': '📊 Excel (.xlsx) - Comprehensive report',
            'pdf': '📄 PDF (.pdf) - Professional report',
            'csv': '📄 CSV (.csv) - Simple data export'
        }[x]
    )

with col2:
    days = st.selectbox(
        "Time period",
        options=[7, 14, 30, 60, 90, 180, 365],
        index=2,  # Default: 30 days
        format_func=lambda x: f"Last {x} days"
    )

# Excel and PDF specific options
if export_format in ['excel', 'pdf']:
    st.markdown(f"**Include in {export_format.upper()} export:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        include_kpis = st.checkbox("📊 KPI Analysis", value=True, help="Include KPI calculations and status")

    with col2:
        include_red_flags = st.checkbox("🚩 Red Flags", value=True, help="Include anomaly detection results")

    with col3:
        if export_format == 'pdf':
            include_charts = st.checkbox("📈 Charts", value=True, help="Include trend charts")
        else:
            include_charts = False
else:
    include_kpis = False
    include_red_flags = False
    include_charts = False

st.divider()

# Preview section
st.subheader("📸 Preview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Entries", storage.count())

with col2:
    entries_in_period = len(engine.metrics.get_metrics_dataframe(days=days))
    st.metric("Entries in Period", entries_in_period)

with col3:
    if export_format == 'excel':
        sheets_count = 3  # Summary, Daily Data, Charts Data
        if include_kpis:
            sheets_count += 1
        if include_red_flags:
            sheets_count += 1
        st.metric("Excel Sheets", sheets_count)
    else:
        st.metric("Format", "CSV")

# Excel sheets breakdown
if export_format == 'excel':
    with st.expander("📑 Excel Sheets Included"):
        st.markdown("""
        **Always included:**
        - 📊 **Summary** - Key statistics and metrics overview
        - 📋 **Daily Data** - All daily entries with calculated metrics
        - 📈 **Charts Data** - Weekly aggregates for easy charting

        **Optional:**
        - 🎯 **KPIs** - Performance indicators with status and explanations
        - 🚩 **Red Flags** - Detected issues and recommendations
        """)

st.divider()

# Export buttons
st.subheader("💾 Download")

if export_format == 'excel':
    st.info("Excel export includes multiple sheets with formatted data, charts-ready aggregates, and color-coded insights.")

    if st.button("📥 Generate Excel Export", type="primary", use_container_width=True):
        with st.spinner("Generating Excel export..."):
            try:
                excel_bytes = engine.export_to_excel(
                    days=days,
                    include_kpis=include_kpis,
                    include_red_flags=include_red_flags
                )

                # Prepare filename
                filename = f"DIET_APP_Export_{date.today().isoformat()}.xlsx"

                st.download_button(
                    label="💾 Download Excel File",
                    data=excel_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                st.success(f"✅ Excel export generated successfully! ({len(excel_bytes) // 1024} KB)")

            except Exception as e:
                st.error(f"Error generating Excel export: {str(e)}")
                st.exception(e)

elif export_format == 'pdf':  # PDF
    st.info("PDF export includes comprehensive analytics with charts, KPIs, and red flags in a professional format.")

    if st.button("📥 Generate PDF Export", type="primary", use_container_width=True):
        with st.spinner("Generating PDF export..."):
            try:
                pdf_bytes = pdf_engine.export_to_pdf(
                    days=days,
                    include_kpis=include_kpis,
                    include_red_flags=include_red_flags,
                    include_charts=include_charts
                )

                # Prepare filename
                filename = f"DIET_APP_Report_{date.today().isoformat()}.pdf"

                st.download_button(
                    label="💾 Download PDF File",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )

                st.success(f"✅ PDF export generated successfully! ({len(pdf_bytes) // 1024} KB)")

            except Exception as e:
                st.error(f"Error generating PDF export: {str(e)}")
                st.exception(e)

else:  # CSV
    st.info("CSV export includes daily data with all metrics in a simple, portable format.")

    if st.button("📥 Generate CSV Export", type="primary", use_container_width=True):
        with st.spinner("Generating CSV export..."):
            try:
                csv_bytes = engine.export_to_csv(days=days)

                # Prepare filename
                filename = f"DIET_APP_Export_{date.today().isoformat()}.csv"

                st.download_button(
                    label="💾 Download CSV File",
                    data=csv_bytes,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True
                )

                st.success(f"✅ CSV export generated successfully! ({len(csv_bytes) // 1024} KB)")

            except Exception as e:
                st.error(f"Error generating CSV export: {str(e)}")
                st.exception(e)

st.divider()

# Export info
with st.expander("ℹ️ About Exports"):
    st.markdown("""
    ### Export Formats

    **Excel (.xlsx)**
    - Multiple sheets with different data views
    - Formatted headers and color-coded severity levels
    - Ready for charting and further analysis
    - Includes comprehensive metrics and insights

    **PDF (.pdf)**
    - Professional report format (1-4 pages)
    - Summary statistics with tables
    - Trend charts (weight, calories)
    - KPI analysis with status indicators
    - Red flag detection with color-coded severity
    - Perfect for sharing or archiving

    **CSV (.csv)**
    - Simple tabular format
    - Compatible with all spreadsheet applications
    - Easy to import into other tools
    - Contains daily data with all calculated metrics

    ### Data Included

    All exports include:
    - Weight measurements (raw and moving averages)
    - Body composition (fat mass, lean mass, body fat %)
    - Calorie data (intake, sport, NET balance)
    - Rolling averages (7-day, 14-day where applicable)

    Excel and PDF exports can additionally include:
    - KPI analysis with status indicators
    - Red flag detection with recommendations
    - Weekly aggregated data for trend analysis
    - Charts and visualizations (PDF)

    ### Privacy Note

    All exports are generated locally on your device. No data is uploaded or transmitted.
    Your exported files remain completely under your control.
    """)

# Footer
st.divider()
st.caption(f"""
**Export Settings:**
- BMR: {bmr_kcal:.0f} kcal/day
- Target Weight: {target_weight_kg:.1f} kg
- Time Period: Last {days} days
""")
