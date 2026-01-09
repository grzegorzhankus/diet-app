#!/usr/bin/env python3
"""
Script to add i18n support to all pages
"""

import re
from pathlib import Path

# Pages to update
PAGES_DIR = Path("app/pages")
pages_files = list(PAGES_DIR.glob("*.py"))

print(f"Found {len(pages_files)} pages to update")

# Common imports to add
IMPORTS_TO_ADD = """
from core.i18n import t, get_text
"""

for page_file in pages_files:
    print(f"\\nUpdating {page_file.name}...")

    content = page_file.read_text()

    # Skip if already has i18n import
    if "from core.i18n import" in content:
        print(f"  ✓ {page_file.name} already has i18n imports, skipping")
        continue

    # Add imports after other core imports
    if "from core.storage import Storage" in content:
        content = content.replace(
            "from core.storage import Storage",
            f"from core.storage import Storage{IMPORTS_TO_ADD}"
        )
    elif "from core." in content:
        # Add after first core import
        lines = content.split("\\n")
        for i, line in enumerate(lines):
            if line.startswith("from core."):
                lines.insert(i + 1, IMPORTS_TO_ADD.strip())
                break
        content = "\\n".join(lines)
    else:
        # Add after st import
        content = content.replace(
            "import streamlit as st",
            f"import streamlit as st{IMPORTS_TO_ADD}"
        )

    # Add language initialization at the start of main content
    if "st.set_page_config(" in content:
        # Find where to insert language init (after st.set_page_config)
        config_match = re.search(r"st\\.set_page_config\\([^)]+\\)", content)
        if config_match:
            insert_pos = config_match.end()
            lang_init = """

# Get language from session state
if "language" not in st.session_state:
    st.session_state.language = "en"
lang = st.session_state.language
"""
            content = content[:insert_pos] + lang_init + content[insert_pos:]

    # Write back
    page_file.write_text(content)
    print(f"  ✓ Updated {page_file.name}")

print("\\n✅ All pages updated with i18n support!")
print("\\nNext steps:")
print("1. Manually update st.title() and st.markdown() calls to use t() function")
print("2. Replace hardcoded strings with translation keys")
print("3. Test language switching")
