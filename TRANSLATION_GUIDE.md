# 🌐 Przewodnik tłumaczenia DIET_APP

## ✅ Co zostało zrobione:

### 1. System tłumaczeń (`core/i18n.py`)
- ✅ 180+ kluczy tłumaczeń EN/PL
- ✅ Funkcje `t()` i `get_text()`
- ✅ Szablony promptów LLM w obu językach
- ✅ Kompletne tłumaczenia dla wszystkich stron

### 2. Strony przetłumaczone:
- ✅ **Main page** (`app/main.py`) - częściowo
- ✅ **Daily Entry** (`app/pages/1_📝_Daily_Entry.py`) - **100% ukończone!**

### 3. Strony z infrastrukturą i18n (gotowe do tłumaczenia):
- ⏳ History (`2_📊_History.py`)
- ⏳ Dashboard (`3_📈_Dashboard.py`)
- ⏳ KPIs (`4_📊_KPIs.py`)
- ⏳ Red Flags (`5_🚩_Red_Flags.py`)
- ⏳ Forecast (`6_🔮_Forecast.py`)
- ⏳ Export (`7_📤_Export.py`)
- ⏳ AI Insights (`8_🤖_AI_Insights.py`)
- ⏳ Pattern Analysis (`9_🔬_Pattern_Analysis.py`)

---

## 📖 Jak przetłumaczyć stronę (krok po kroku)

### Wzór na podstawie Daily Entry:

#### Krok 1: Dodaj inicjalizację języka na początku strony

**Było:**
```python
st.set_page_config(...)

st.title("📊 History")
st.markdown("View your data")
```

**Powinno być:**
```python
st.set_page_config(...)

# Get language from session state
if "language" not in st.session_state:
    st.session_state.language = "en"
lang = st.session_state.language

st.title(f"📊 {t('history', lang)}")
st.markdown(t("view_all_data", lang))
```

#### Krok 2: Zamień wszystkie hardcode'owane stringi na t()

**Przykłady zamian:**

| Przed | Po |
|-------|-----|
| `"Date"` | `t("date", lang)` |
| `"Weight (kg)"` | `t("weight_kg", lang)` |
| `"Total Entries"` | `t("total_entries", lang)` |
| `"From Date"` | `t("start_date", lang)` |
| `"To Date"` | `t("end_date", lang)` |
| `"Save Entry"` | `t("save_entry", lang)` |
| `"Cancel"` | `t("cancel", lang)` |
| `"Edit"` | `t("edit", lang)` |
| `"Delete"` | `t("delete", lang)` |

#### Krok 3: Przetłumacz tytuły i podtytuły

```python
# Przed:
st.title("📊 KPIs")
st.subheader("Performance Metrics")
st.metric("Current Weight", weight)

# Po:
st.title(f"📊 {t('kpis', lang)}")
st.subheader(t("key_performance_indicators", lang))
st.metric(t("current_weight", lang), weight)
```

#### Krok 4: Przetłumacz komunikaty i przyciski

```python
# Przed:
st.success("Data saved successfully!")
st.error("Error saving data")
if st.button("Generate Report"):
    pass

# Po:
st.success(f"✅ {t('success', lang)}")
st.error(f"❌ {t('error', lang)}")
if st.button(t("generate_insights", lang)):
    pass
```

---

## 🔑 Dostępne klucze tłumaczeń

### Navigation
- `daily_entry`, `history`, `dashboard`, `kpis`, `red_flags`
- `forecast`, `export`, `ai_insights`, `pattern_analysis`

### History Page
- `data_history`, `total_entries`, `date_range`, `recent_entries`
- `no_data_yet`, `view_all_data`, `latest_entry`, `oldest_entry`

### Dashboard Page
- `analytics_dashboard`, `weight_trend`, `calories_trend`, `training_trend`
- `correlation_analysis`, `select_time_period`, `trend_analysis`

### KPIs Page
- `key_performance_indicators`, `current_weight`, `avg_daily_calories`
- `total_training_time`, `weight_change`, `avg_weight`, `min_weight`, `max_weight`
- `consistency_score`

### Red Flags Page
- `risk_alerts`, `no_red_flags`, `red_flags_detected`, `severity`
- `high`, `medium`, `low`, `description`, `recommendation`

### Forecast Page
- `weight_forecast`, `forecast_days`, `generate_forecast`
- `predicted_weight`, `confidence_interval`, `forecast_chart`

### Export Page
- `export_data_title`, `export_format`, `export_csv`, `export_excel`, `export_pdf`
- `select_date_range`, `start_date`, `end_date`, `include_charts`

### AI Insights Page
- `ai_insights_title`, `generate_insights`, `analyzing`
- `llm_model`, `temperature`, `insights_generated`

### Pattern Analysis Page
- `pattern_analysis_title`, `weekly_patterns`, `monthly_patterns`
- `anomalies_detected`, `analyze_patterns`

### Common
- `date`, `weight_kg`, `bodyfat_pct`, `cal_in`, `cal_out`, `notes`
- `save_entry`, `update_entry`, `cancel`, `edit`, `delete`
- `refresh`, `download`, `clear`, `back`, `loading`, `error`, `success`, `warning`

### Units
- `kg`, `kcal`, `minutes`, `hours`, `days`, `percent`

---

## 🎯 Priorytet tłumaczeń

### Wysokim priorytet (najczęściej używane):
1. ✅ **Daily Entry** - UKOŃCZONE
2. ⏳ **History** - proste wyświetlanie danych
3. ⏳ **Dashboard** - wykresy (niewiele tekstu)
4. ⏳ **KPIs** - metryki (głównie liczby)

### Średni priorytet:
5. ⏳ **Red Flags** - alerty
6. ⏳ **Export** - eksport danych

### Niski priorytet (rzadziej używane):
7. ⏳ **Forecast** - prognozy
8. ⏳ **AI Insights** - LLM (placeholder)
9. ⏳ **Pattern Analysis** - analiza wzorców (placeholder)

---

## 🚀 Szybki start - Przetłumacz History Page

1. **Otwórz plik:** `app/pages/2_📊_History.py`

2. **Znajdź i zamień:**

```python
# Na początku pliku, po st.set_page_config:
if "language" not in st.session_state:
    st.session_state.language = "en"
lang = st.session_state.language
```

3. **Zamień tytuły:**

```python
# Było:
st.title("📊 Data History")
st.markdown("View and analyze your historical data")

# Powinno być:
st.title(f"📊 {t('data_history', lang)}")
st.markdown(t("view_all_data", lang))
```

4. **Zamień etykiety:**

```python
# Było:
start_date = st.date_input("From Date", ...)
end_date = st.date_input("To Date", ...)

# Powinno być:
start_date = st.date_input(t("start_date", lang), ...)
end_date = st.date_input(t("end_date", lang), ...)
```

5. **Zapisz i przetestuj:**
```bash
# Restart aplikacji
bash ~/app-manager.sh restart diet

# Sprawdź w przeglądarce: http://localhost:8501
```

---

## 📝 Checklist dla każdej strony

- [ ] Dodaj inicjalizację języka (`lang = st.session_state.language`)
- [ ] Przetłumacz `st.title()` i `st.markdown()`
- [ ] Przetłumacz wszystkie `st.subheader()`
- [ ] Przetłumacz etykiety w `st.date_input()`, `st.number_input()`, etc.
- [ ] Przetłumacz przyciski (`st.button()`)
- [ ] Przetłumacz komunikaty (`st.success()`, `st.error()`, `st.warning()`)
- [ ] Przetłumacz etykiety metryk (`st.metric()`)
- [ ] Przetestuj przełączanie EN/PL w aplikacji

---

## 🧪 Testowanie

1. Uruchom aplikację:
```bash
bash ~/app-manager.sh start diet
```

2. Otwórz: http://localhost:8501

3. W sidebarze zmień język na 🇵🇱 Polski

4. Przejdź przez wszystkie strony i sprawdź czy:
   - Wszystkie teksty są po polsku
   - Przyciski działają
   - Nie ma błędów w konsoli

---

## 💡 Wskazówki

1. **Używaj wzorca z Daily Entry** - to jest pełny, działający przykład

2. **Commit często:**
```bash
git add app/pages/2_📊_History.py
git commit -m "Feat: Translate History page to Polish"
git push origin main
```

3. **Jeśli brakuje klucza tłumaczenia:**
   - Dodaj go do `core/i18n.py` w sekcji `TRANSLATIONS`
   - Format: `"key": {"en": "English", "pl": "Polski"}`

4. **Testuj na bieżąco** - nie czekaj z testowaniem do końca

---

## 📦 Obecny stan

**Commity:**
- `47dfa78` - Initial i18n infrastructure
- `a6b817e` - Complete Daily Entry translation
- `708c3e9` - Complete translation dictionary

**Wersja:** 0.11.0

**Status:**
- Infrastruktura: ✅ 100%
- Daily Entry: ✅ 100%
- Słownik tłumaczeń: ✅ 100%
- Pozostałe strony: ⏳ 0-10% (podstawowa infrastruktura)

---

## 🎯 Następne kroki

1. Przetłumacz **History** (najprostsza strona)
2. Przetłumacz **KPIs** (głównie metryki)
3. Przetłumacz **Dashboard** (wykresy)
4. Przetłumacz **Red Flags** (alerty)
5. Przetłumacz pozostałe 4 strony według potrzeb

---

**Powodzenia! 🚀**

Jeśli masz pytania, wzoruj się na `app/pages/1_📝_Daily_Entry.py` - to jest kompletny, działający przykład.
