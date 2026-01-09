#!/usr/bin/env python3
"""
Automatically translate hardcoded strings in pages to use i18n
"""

import re
from pathlib import Path

# Mapping of common English strings to translation keys
TRANSLATIONS_MAP = {
    # Titles and headers
    "Daily Entry": ("daily_entry", True),
    "Record your daily measurements": ("log_daily_data", False),
    "Add New Entry": ("add_new_entry", False),
    "Edit Entry for": ("edit_entry_for", False),
    "Recent Entries": ("recent_entries", False),
    "Recent Entries (Last 7 Days)": ("recent_entries_7", False),

    # Form labels
    "Date": ("date", False),
    "Weight (kg)": ("weight_kg", False),
    "Body Fat %": ("bodyfat_pct", False),
    "Calories IN (kcal)": ("cal_in", False),
    "Exercise OUT (kcal)": ("cal_out", False),
    "Notes": ("notes", False),

    # Buttons
    "Save Entry": ("save_entry", False),
    "Update Entry": ("update_entry", False),
    "Cancel": ("cancel", False),
    "Edit": ("edit", False),
    "Delete": ("delete", False),

    # Messages
    "Entry saved for": ("entry_saved_for", False),
    "Entry updated for": ("entry_updated_for", False),
    "No entries yet": ("no_entries_yet", False),
    "Total entries in database": ("total_entries_db", False),
}

# Additional translations needed
ADDITIONAL_TRANSLATIONS = """
    # Daily Entry specific
    "add_new_entry": {"en": "Add New Entry", "pl": "Dodaj nowy wpis"},
    "edit_entry_for": {"en": "Edit Entry for", "pl": "Edytuj wpis dla"},
    "recent_entries_7": {"en": "Recent Entries (Last 7 Days)", "pl": "Ostatnie wpisy (ostatnie 7 dni)"},
    "bodyfat_pct": {"en": "Body Fat %", "pl": "Tłuszcz %"},
    "cal_in": {"en": "Calories IN (kcal)", "pl": "Kalorie IN (kcal)"},
    "cal_out": {"en": "Exercise OUT (kcal)", "pl": "Kalorie OUT sport (kcal)"},
    "notes": {"en": "Notes", "pl": "Notatki"},
    "update_entry": {"en": "Update Entry", "pl": "Zaktualizuj wpis"},
    "cancel": {"en": "Cancel", "pl": "Anuluj"},
    "edit": {"en": "Edit", "pl": "Edytuj"},
    "delete": {"en": "Delete", "pl": "Usuń"},
    "entry_saved_for": {"en": "Entry saved for", "pl": "Wpis zapisany dla"},
    "entry_updated_for": {"en": "Entry updated for", "pl": "Wpis zaktualizowany dla"},
    "no_entries_yet": {"en": "No entries yet. Add your first measurement above!",
                       "pl": "Brak wpisów. Dodaj swój pierwszy pomiar powyżej!"},
    "total_entries_db": {"en": "Total entries in database", "pl": "Łączna liczba wpisów w bazie"},
    "entry_exists_warning": {"en": "Entry for {date} already exists.",
                            "pl": "Wpis dla {date} już istnieje."},
    "override_entry": {"en": "Override this entry", "pl": "Nadpisz ten wpis"},
    "error_saving": {"en": "Error saving entry", "pl": "Błąd zapisu wpisu"},
    "net_balance": {"en": "NET Balance", "pl": "Bilans NETTO"},
    "source": {"en": "Source", "pl": "Źródło"},
"""

print("Adding additional translations to i18n.py...")

# Read current i18n.py
i18n_path = Path("core/i18n.py")
i18n_content = i18n_path.read_text()

# Find the TRANSLATIONS dict and add new entries before the closing brace
if "# Units" in i18n_content:
    # Add before Units section
    insert_marker = '    # Units'
    additional_section = f"""    # Daily Entry specific
{ADDITIONAL_TRANSLATIONS}

{insert_marker}"""
    i18n_content = i18n_content.replace(insert_marker, additional_section)
    i18n_path.write_text(i18n_content)
    print("✓ Added additional translations to i18n.py")

print("\\nDone! Next: manually update page files to use t() function.")
print("\\nExample changes needed:")
print('  st.title("📝 Daily Entry") → st.title(f"📝 {t(\'daily_entry\', lang)}")')
print('  "Weight (kg)" → t("weight_kg", lang)')
