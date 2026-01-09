"""
Daily Entry page - Add/Edit daily measurements
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import date, timedelta
from core.storage import Storage
from core.i18n import t, get_text

from core.schemas import DailyEntryCreate, DailyEntryUpdate

st.set_page_config(page_title="Daily Entry", page_icon="📝", layout="wide", initial_sidebar_state="expanded")

# Get language from session state
if "language" not in st.session_state:
    st.session_state.language = "en"
lang = st.session_state.language

st.title(f"📝 {t('daily_entry', lang)}")
st.markdown(t("log_daily_data", lang))

# Initialize storage
storage = Storage()

# Check if we're in edit mode
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'edit_entry' not in st.session_state:
    st.session_state.edit_entry = None

# Form for new/edit entry
if st.session_state.edit_mode and st.session_state.edit_entry:
    st.subheader(f"✏️ {t('edit_entry_for', lang)} {st.session_state.edit_entry.date}")
    entry = st.session_state.edit_entry
    default_date = entry.date
    default_weight = entry.weight_kg
    default_bodyfat = entry.bodyfat_pct if entry.bodyfat_pct else None
    default_cal_in = entry.cal_in_kcal if entry.cal_in_kcal else None
    default_cal_out = entry.cal_out_sport_kcal if entry.cal_out_sport_kcal else None
    default_notes = entry.notes if entry.notes else ""
    form_key = f"edit_form_{entry.id}"
    submit_label = f"💾 {t('update_entry', lang)}"
else:
    st.subheader(t("add_new_entry", lang))
    default_date = date.today()
    default_weight = 80.0
    default_bodyfat = None
    default_cal_in = None
    default_cal_out = None
    default_notes = ""
    form_key = "daily_entry_form"
    submit_label = f"💾 {t('save_entry', lang)}"

with st.form(form_key):
    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input(
            t("date", lang),
            value=default_date,
            max_value=date.today(),
            disabled=st.session_state.edit_mode  # Can't change date in edit mode
        )

        weight_kg = st.number_input(
            "Weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=default_weight,
            step=0.1,
            help="Body weight in kilograms (30-200 kg)"
        )

        bodyfat_pct = st.number_input(
            "Body Fat %",
            min_value=0.0,
            max_value=100.0,
            value=default_bodyfat,
            step=0.1,
            help="Body fat percentage (optional, 0-100%)"
        )

    with col2:
        cal_in_kcal = st.number_input(
            "Calories IN (kcal)",
            min_value=0.0,
            value=default_cal_in,
            step=10.0,
            help="Total calories consumed (optional)"
        )

        cal_out_sport_kcal = st.number_input(
            "Exercise OUT (kcal)",
            min_value=0.0,
            value=default_cal_out,
            step=10.0,
            help="Calories burned through exercise (optional)"
        )

        notes = st.text_area(
            "Notes",
            value=default_notes,
            placeholder="Optional notes (e.g., 'Morning, fasted')",
            max_chars=500
        )

    col_submit, col_cancel = st.columns([3, 1])

    with col_submit:
        submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)

    with col_cancel:
        if st.session_state.edit_mode:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
            if cancel:
                st.session_state.edit_mode = False
                st.session_state.edit_entry = None
                st.rerun()

    if submitted:
        try:
            if st.session_state.edit_mode and st.session_state.edit_entry:
                # Update existing entry
                updates = DailyEntryUpdate(
                    weight_kg=weight_kg,
                    bodyfat_pct=bodyfat_pct if bodyfat_pct else None,
                    cal_in_kcal=cal_in_kcal if cal_in_kcal else None,
                    cal_out_sport_kcal=cal_out_sport_kcal if cal_out_sport_kcal else None,
                    notes=notes if notes.strip() else None
                )

                updated = storage.update(st.session_state.edit_entry.id, updates)
                st.success(f"✅ Entry updated for {updated.date}")

                # Exit edit mode
                st.session_state.edit_mode = False
                st.session_state.edit_entry = None
                st.rerun()
            else:
                # Check if entry exists
                existing = storage.get_by_date(entry_date)

                if existing:
                    st.warning(f"⚠️ Entry for {entry_date} already exists.")
                    if st.button("🔄 Override this entry"):
                        # Switch to edit mode with this entry
                        st.session_state.edit_mode = True
                        st.session_state.edit_entry = existing
                        st.rerun()
                else:
                    # Create new entry
                    entry = DailyEntryCreate(
                        date=entry_date,
                        weight_kg=weight_kg,
                        bodyfat_pct=bodyfat_pct if bodyfat_pct else None,
                        cal_in_kcal=cal_in_kcal if cal_in_kcal else None,
                        cal_out_sport_kcal=cal_out_sport_kcal if cal_out_sport_kcal else None,
                        notes=notes if notes.strip() else None,
                        source="manual"
                    )

                    saved = storage.create(entry)
                    st.success(f"✅ Entry saved for {saved.date}")
                    st.balloons()

        except Exception as e:
            st.error(f"❌ Error saving entry: {str(e)}")

st.divider()

# Recent entries with edit buttons
st.subheader("Recent Entries (Last 7 Days)")

recent = storage.get_all(limit=7)

if recent:
    for entry in recent:
        with st.expander(f"📅 {entry.date} - {entry.weight_kg} kg"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Weight", f"{entry.weight_kg} kg")
                if entry.bodyfat_pct:
                    st.metric("Body Fat %", f"{entry.bodyfat_pct:.1f}%")

            with col2:
                if entry.cal_in_kcal:
                    st.metric("Calories IN", f"{entry.cal_in_kcal:.0f} kcal")
                if entry.cal_out_sport_kcal:
                    st.metric("Exercise OUT", f"{entry.cal_out_sport_kcal:.0f} kcal")

            with col3:
                if entry.cal_in_kcal and entry.cal_out_sport_kcal:
                    net = entry.cal_in_kcal - entry.cal_out_sport_kcal
                    st.metric("NET Balance", f"{net:.0f} kcal")

            if entry.notes:
                st.caption(f"📝 {entry.notes}")

            st.caption(f"Source: {entry.source}")

            # Edit and Delete buttons
            col_edit, col_delete, col_spacer = st.columns([1, 1, 3])

            with col_edit:
                if st.button(f"✏️ Edit", key=f"edit_{entry.id}"):
                    st.session_state.edit_mode = True
                    st.session_state.edit_entry = entry
                    st.rerun()

            with col_delete:
                if st.button(f"🗑️ Delete", key=f"delete_{entry.id}"):
                    if storage.delete(entry.id):
                        st.success(f"Deleted entry for {entry.date}")
                        st.rerun()
                    else:
                        st.error("Failed to delete entry")
else:
    st.info("No entries yet. Add your first measurement above!")

# Footer
st.divider()
st.caption(f"Total entries in database: {storage.count()}")
