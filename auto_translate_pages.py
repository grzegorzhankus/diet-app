#!/usr/bin/env python3
"""
Automatically translate all remaining pages
"""
import re
from pathlib import Path

# Mapping of common strings to translation keys
REPLACEMENTS = [
    # Titles
    (r'st\.title\("📊 Data History"\)', 'st.title(f"📊 {t(\'data_history\', lang)}")'),
    (r'st\.title\("📊 History"\)', 'st.title(f"📊 {t(\'history\', lang)}")'),
    (r'st\.title\("📈 Dashboard"\)', 'st.title(f"📈 {t(\'dashboard\', lang)}")'),
    (r'st\.title\("📊 KPIs"\)', 'st.title(f"📊 {t(\'kpis\', lang)}")'),
    (r'st\.title\("🚩 Red Flags"\)', 'st.title(f"🚩 {t(\'red_flags\', lang)}")'),
    (r'st\.title\("🔮 Forecast"\)', 'st.title(f"🔮 {t(\'forecast\', lang)}")'),
    (r'st\.title\("📤 Export"\)', 'st.title(f"📤 {t(\'export\', lang)}")'),
    (r'st\.title\("🤖 AI Insights"\)', 'st.title(f"🤖 {t(\'ai_insights\', lang)}")'),
    (r'st\.title\("🔬 Pattern Analysis"\)', 'st.title(f"🔬 {t(\'pattern_analysis\', lang)}")'),

    # Common labels
    (r'"Date"', 't("date", lang)'),
    (r'"Weight \(kg\)"', 't("weight_kg", lang)'),
    (r'"From Date"', 't("start_date", lang)'),
    (r'"To Date"', 't("end_date", lang)'),
    (r'"Total Entries"', 't("total_entries", lang)'),
    (r'"Latest Entry"', 't("latest_entry", lang)'),
    (r'"Oldest Entry"', 't("oldest_entry", lang)'),
]

PAGES_DIR = Path("app/pages")
pages = list(PAGES_DIR.glob("*.py"))

# Skip Daily Entry (already done)
pages = [p for p in pages if "1_" not in p.name]

print(f"Translating {len(pages)} pages...")

for page_file in pages:
    print(f"\\n📝 {page_file.name}")

    content = page_file.read_text()

    # Apply basic replacements
    for pattern, replacement in REPLACEMENTS:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print(f"  ✓ Replaced: {pattern[:40]}...")

    # Write back
    page_file.write_text(content)

print("\\n✅ Basic automatic translation complete!")
print("\\nNote: This is a basic pass. Manual review and additional translations may be needed.")
