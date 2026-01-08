"""
DIET_APP - CFO-grade diet and training tracker
Offline-first, deterministic analytics for personal use.
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

# App metadata
APP_VERSION = "0.10.0"
APP_TITLE = "DIET_APP"

# Import core modules
from core.storage import Storage

def main():
    """Main entry point for the Streamlit application."""

    # Page config
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Header
    st.title(f"{APP_TITLE} v{APP_VERSION}")
    st.markdown("**CFO-grade diet and training tracker** • Offline-first • Deterministic")

    st.divider()

    # Status section
    st.subheader("System Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Application", "Online", delta="OK")

    with col2:
        st.metric("Runtime Mode", "Offline", delta="No egress")

    with col3:
        st.metric("Version", APP_VERSION, delta="Blok 4")

    st.divider()

    # Database status
    storage = Storage()
    entry_count = storage.count()

    st.subheader("Database Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Entries", entry_count)

    with col2:
        if entry_count > 0:
            latest = storage.get_all(limit=1)[0]
            st.metric("Latest Entry", latest.date.strftime("%Y-%m-%d"))
        else:
            st.metric("Latest Entry", "N/A")

    with col3:
        if entry_count > 0:
            oldest = storage.get_all(limit=1, offset=entry_count-1)[0]
            st.metric("Oldest Entry", oldest.date.strftime("%Y-%m-%d"))
        else:
            st.metric("Oldest Entry", "N/A")

    st.divider()

    # Info section
    if entry_count == 0:
        st.warning("""
        **No data in database yet!**

        To get started:
        1. Go to **📝 Daily Entry** page to add today's measurement
        2. Or import historical data from Weight.xlsx (see below)
        """)

        # Import section
        st.subheader("📥 Import Historical Data")

        st.info("""
        You can import your historical data from **Weight.xlsx**.

        This will import ~2199 entries (2020-2026) with weight, body fat %, and calorie data.
        """)

        if st.button("🚀 Import Weight.xlsx Now", type="primary"):
            with st.spinner("Importing data..."):
                from core.importer import Importer
                importer = Importer(storage)

                try:
                    stats = importer.import_weight_xlsx("Weight.xlsx")
                    st.success(f"""
                    ✅ Import complete!

                    - **Total rows:** {stats['total']}
                    - **Imported:** {stats['imported']}
                    - **Skipped:** {stats['skipped']}
                    - **Errors:** {stats['errors']}
                    """)
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Import failed: {str(e)}")
    else:
        st.success(f"""
        **Blok 4 Complete:** KPI Engine with 12 indicators!

        **Database contains {entry_count} entries.**

        **Available features:**
        - 📝 Daily Entry - Add/edit measurements
        - 📊 History - View and export data
        - 📈 Dashboard - Trends and analytics
        - 📊 KPIs - 12 Key Performance Indicators

        **Next Steps:**
        - Blok 5: Red flags engine (10+ flags)
        - Blok 6: Forecast engine (7/14/30 day predictions)
        - Blok 7: PDF/Excel export
        """)

    # Footer
    st.divider()
    st.caption("DIET_APP • Grzegorz Hankus • 2026-01-07")

if __name__ == "__main__":
    main()
