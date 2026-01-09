"""
Internationalization (i18n) module for DIET_APP
Supports English (EN) and Polish (PL) languages
"""

from typing import Dict, Any

# Translation dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Common UI elements
    "language": {"en": "Language", "pl": "Język"},
    "select_language": {"en": "Select Language", "pl": "Wybierz język"},
    "english": {"en": "English", "pl": "Angielski"},
    "polish": {"en": "Polish", "pl": "Polski"},

    # Main page
    "app_title": {"en": "DIET_APP", "pl": "DIET_APP"},
    "app_subtitle": {"en": "CFO-grade diet and training tracker • Offline-first • Deterministic",
                     "pl": "Tracker diety i treningów klasy CFO • Offline-first • Deterministyczny"},
    "system_status": {"en": "System Status", "pl": "Status systemu"},
    "application": {"en": "Application", "pl": "Aplikacja"},
    "online": {"en": "Online", "pl": "Online"},
    "ok": {"en": "OK", "pl": "OK"},
    "runtime_mode": {"en": "Runtime Mode", "pl": "Tryb działania"},
    "offline": {"en": "Offline", "pl": "Offline"},
    "no_egress": {"en": "No egress", "pl": "Bez wycieku danych"},
    "storage_location": {"en": "Storage Location", "pl": "Lokalizacja danych"},
    "local": {"en": "Local", "pl": "Lokalnie"},
    "quick_actions": {"en": "Quick Actions", "pl": "Szybkie akcje"},
    "add_daily_entry": {"en": "➕ Add Daily Entry", "pl": "➕ Dodaj wpis dzienny"},
    "view_dashboard": {"en": "📊 View Dashboard", "pl": "📊 Zobacz dashboard"},
    "export_data": {"en": "📤 Export Data", "pl": "📤 Eksportuj dane"},
    "getting_started": {"en": "Getting Started", "pl": "Jak zacząć"},
    "getting_started_text": {"en": """
    1. **Daily Entry**: Log your daily weight, calories, and training
    2. **History**: Review your progress over time
    3. **Dashboard**: Analyze trends with visualizations
    4. **KPIs**: Track key performance indicators
    5. **Red Flags**: Get alerts on concerning patterns
    6. **Export**: Download your data in various formats
    """, "pl": """
    1. **Wpis dzienny**: Zapisz wagę, kalorie i trening
    2. **Historia**: Zobacz swoje postępy w czasie
    3. **Dashboard**: Analizuj trendy z wizualizacjami
    4. **KPI**: Śledź kluczowe wskaźniki wydajności
    5. **Red Flags**: Otrzymuj alerty o niepokojących wzorcach
    6. **Eksport**: Pobierz dane w różnych formatach
    """},

    # Navigation
    "daily_entry": {"en": "Daily Entry", "pl": "Wpis dzienny"},
    "history": {"en": "History", "pl": "Historia"},
    "dashboard": {"en": "Dashboard", "pl": "Dashboard"},
    "kpis": {"en": "KPIs", "pl": "KPI"},
    "red_flags": {"en": "Red Flags", "pl": "Red Flags"},
    "forecast": {"en": "Forecast", "pl": "Prognoza"},
    "export": {"en": "Export", "pl": "Eksport"},
    "ai_insights": {"en": "AI Insights", "pl": "Insighty AI"},
    "pattern_analysis": {"en": "Pattern Analysis", "pl": "Analiza wzorców"},

    # Daily Entry page
    "log_daily_data": {"en": "Log Your Daily Data", "pl": "Zapisz swoje dane dzienne"},
    "date": {"en": "Date", "pl": "Data"},
    "weight_kg": {"en": "Weight (kg)", "pl": "Waga (kg)"},
    "calories": {"en": "Calories", "pl": "Kalorie"},
    "training_minutes": {"en": "Training (minutes)", "pl": "Trening (minuty)"},
    "save_entry": {"en": "💾 Save Entry", "pl": "💾 Zapisz wpis"},
    "entry_saved": {"en": "✅ Entry saved successfully!", "pl": "✅ Wpis zapisany pomyślnie!"},
    "entry_updated": {"en": "✅ Entry updated successfully!", "pl": "✅ Wpis zaktualizowany pomyślnie!"},
    "entry_exists": {"en": "ℹ️ Entry for this date already exists. Updating...",
                     "pl": "ℹ️ Wpis dla tej daty już istnieje. Aktualizuję..."},

    # History page
    "data_history": {"en": "Data History", "pl": "Historia danych"},
    "total_entries": {"en": "Total Entries", "pl": "Łączna liczba wpisów"},
    "date_range": {"en": "Date Range", "pl": "Zakres dat"},
    "recent_entries": {"en": "Recent Entries", "pl": "Ostatnie wpisy"},
    "no_data": {"en": "No data available yet. Add your first entry!",
                "pl": "Brak danych. Dodaj swój pierwszy wpis!"},

    # Dashboard page
    "analytics_dashboard": {"en": "Analytics Dashboard", "pl": "Dashboard analityczny"},
    "weight_trend": {"en": "Weight Trend", "pl": "Trend wagi"},
    "calories_trend": {"en": "Calories Trend", "pl": "Trend kalorii"},
    "training_trend": {"en": "Training Trend", "pl": "Trend treningowy"},
    "correlation_analysis": {"en": "Correlation Analysis", "pl": "Analiza korelacji"},

    # KPIs page
    "key_performance_indicators": {"en": "Key Performance Indicators", "pl": "Kluczowe wskaźniki wydajności"},
    "current_weight": {"en": "Current Weight", "pl": "Aktualna waga"},
    "avg_daily_calories": {"en": "Avg Daily Calories", "pl": "Średnie dzienne kalorie"},
    "total_training_time": {"en": "Total Training Time", "pl": "Całkowity czas treningu"},
    "weight_change": {"en": "Weight Change", "pl": "Zmiana wagi"},

    # Red Flags page
    "risk_alerts": {"en": "Risk Alerts", "pl": "Alerty ryzyka"},
    "no_red_flags": {"en": "✅ No red flags detected. Keep up the good work!",
                     "pl": "✅ Nie wykryto red flags. Tak trzymaj!"},
    "severity": {"en": "Severity", "pl": "Ważność"},
    "high": {"en": "HIGH", "pl": "WYSOKA"},
    "medium": {"en": "MEDIUM", "pl": "ŚREDNIA"},
    "low": {"en": "LOW", "pl": "NISKA"},

    # Forecast page
    "weight_forecast": {"en": "Weight Forecast", "pl": "Prognoza wagi"},
    "forecast_days": {"en": "Forecast Days", "pl": "Dni prognozy"},
    "generate_forecast": {"en": "🔮 Generate Forecast", "pl": "🔮 Generuj prognozę"},
    "predicted_weight": {"en": "Predicted Weight", "pl": "Przewidywana waga"},

    # Export page
    "export_data_title": {"en": "Export Your Data", "pl": "Eksportuj swoje dane"},
    "export_format": {"en": "Export Format", "pl": "Format eksportu"},
    "export_csv": {"en": "📄 Export as CSV", "pl": "📄 Eksportuj jako CSV"},
    "export_excel": {"en": "📊 Export as Excel", "pl": "📊 Eksportuj jako Excel"},
    "export_pdf": {"en": "📕 Export as PDF Report", "pl": "📕 Eksportuj jako raport PDF"},

    # AI Insights page
    "ai_insights_title": {"en": "AI-Powered Insights", "pl": "Insighty oparte na AI"},
    "generate_insights": {"en": "🤖 Generate Insights", "pl": "🤖 Generuj insighty"},
    "analyzing": {"en": "Analyzing your data...", "pl": "Analizuję twoje dane..."},

    # Common buttons
    "refresh": {"en": "🔄 Refresh", "pl": "🔄 Odśwież"},
    "download": {"en": "⬇️ Download", "pl": "⬇️ Pobierz"},
    "clear": {"en": "🗑️ Clear", "pl": "🗑️ Wyczyść"},
    "back": {"en": "← Back", "pl": "← Wstecz"},

    # Time periods
    "last_7_days": {"en": "Last 7 days", "pl": "Ostatnie 7 dni"},
    "last_30_days": {"en": "Last 30 days", "pl": "Ostatnie 30 dni"},
    "last_90_days": {"en": "Last 90 days", "pl": "Ostatnie 90 dni"},
    "all_time": {"en": "All time", "pl": "Cały czas"},

    # Daily Entry specific

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


    # Units
    "kg": {"en": "kg", "pl": "kg"},
    "kcal": {"en": "kcal", "pl": "kcal"},
    "minutes": {"en": "minutes", "pl": "minut"},
    "hours": {"en": "hours", "pl": "godzin"},
    "days": {"en": "days", "pl": "dni"},
}


def get_text(key: str, lang: str = "en") -> str:
    """
    Get translated text for a given key and language.

    Args:
        key: Translation key
        lang: Language code ('en' or 'pl')

    Returns:
        Translated text, or the key itself if translation not found
    """
    lang = lang.lower()
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get("en", key))
    return key


def t(key: str, lang: str = "en") -> str:
    """Shorthand alias for get_text"""
    return get_text(key, lang)


# LLM prompt templates for different languages
LLM_PROMPTS = {
    "insights": {
        "en": """You are a health and fitness coach analyzing diet and training data.
Analyze the following data and provide actionable insights:

{data}

Focus on:
1. Weight trends and patterns
2. Calorie intake consistency
3. Training frequency and intensity
4. Correlations between factors
5. Specific recommendations for improvement

Be concise, specific, and actionable.""",

        "pl": """Jesteś trenerem zdrowia i fitness analizującym dane dotyczące diety i treningów.
Przeanalizuj poniższe dane i dostarcz praktyczne wnioski:

{data}

Skup się na:
1. Trendach i wzorcach wagi
2. Konsystencji spożycia kalorii
3. Częstotliwości i intensywności treningów
4. Korelacjach między czynnikami
5. Konkretnych rekomendacjach do poprawy

Bądź zwięzły, konkretny i praktyczny."""
    },

    "pattern_analysis": {
        "en": """Analyze the following diet and training patterns:

{data}

Identify:
1. Weekly patterns
2. Anomalies or unusual behavior
3. Success factors
4. Areas needing attention

Provide brief, actionable feedback.""",

        "pl": """Przeanalizuj poniższe wzorce diety i treningów:

{data}

Zidentyfikuj:
1. Wzorce tygodniowe
2. Anomalie lub nietypowe zachowania
3. Czynniki sukcesu
4. Obszary wymagające uwagi

Dostarcz krótką, praktyczną opinię."""
    }
}


def get_llm_prompt(prompt_type: str, lang: str = "en", **kwargs) -> str:
    """
    Get LLM prompt template for a given type and language.

    Args:
        prompt_type: Type of prompt ('insights', 'pattern_analysis', etc.)
        lang: Language code ('en' or 'pl')
        **kwargs: Variables to format into the prompt

    Returns:
        Formatted prompt string
    """
    lang = lang.lower()
    template = LLM_PROMPTS.get(prompt_type, {}).get(lang, LLM_PROMPTS.get(prompt_type, {}).get("en", ""))
    return template.format(**kwargs)
