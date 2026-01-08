# BLOK 10: Pattern Recognition & Day-of-Week Analysis ✅

**Status**: COMPLETE
**Version**: 0.10.0
**Date**: 2026-01-08

## Overview

Block 10 adds **Machine Learning pattern recognition** to DIET_APP, detecting behavioral patterns in diet and training data with a focus on temporal effects (weekends, holidays, day-of-week variations). This addresses the user's observation of weekend overeating and Polish holiday patterns vs. workweek discipline.

## User Requirements

> "I see already some patterns that I overeat during weekends and polish national holidays, during work week I have more balance diet and excercise, so maybe you can add days of week - work week, weekends and polish national holidays to your dataframe and further analysis"

The system now:
- Detects weekend vs weekday behavioral patterns
- Identifies Polish holiday effects on calorie intake
- Analyzes day-of-week variations (finding best/worst days)
- Uses statistical tests to determine if patterns are significant
- Provides comprehensive temporal analysis with guard-rails

## What Was Built

### 1. Core ML Modules (`core/ml/`)

#### **Polish Holiday Calendar** (`holidays.py`)
- Complete calendar of Polish national holidays (2020-2030)
- Fixed holidays: New Year, Epiphany, Labour Day, Constitution Day, Assumption of Mary, All Saints' Day, Independence Day, Christmas
- Movable holidays calculated from Easter: Easter Sunday, Easter Monday, Pentecost, Corpus Christi
- Easter calculation using **Meeus/Jones/Butcher algorithm** (accurate for all years)
- Long weekend detection
- Days to/from holiday calculations
- Bilingual names (Polish/English)

```python
from core.ml.holidays import PolishHolidayCalendar

calendar = PolishHolidayCalendar()
holidays_2026 = calendar.get_holidays(2026)
is_christmas = calendar.is_holiday(date(2026, 12, 25))  # True
```

#### **Temporal Feature Engine** (`temporal_features.py`)
- Enriches DataFrames with temporal features **without modifying storage**
- Features added:
  - `day_of_week` (0-6, Monday-Sunday)
  - `day_name` (Polish: Poniedziałek, Wtorek, etc.)
  - `day_name_en` (English: Monday, Tuesday, etc.)
  - `is_weekend` (Saturday, Sunday)
  - `is_workweek` (Monday-Friday, non-holidays)
  - `is_holiday` (Polish national holidays)
  - `holiday_name` (e.g., "Boże Narodzenie (Christmas Day)")
  - `is_long_weekend` (holidays near weekends)
  - `period_type` (Workweek, Weekend, Holiday, Long Weekend)
  - `days_to_next_holiday`
  - `days_since_last_holiday`

```python
from core.ml.temporal_features import TemporalFeatureEngine

engine = TemporalFeatureEngine()
df = engine.add_temporal_features(df, date_column='date')
```

#### **Pattern Detection Engine** (`patterns.py`)
- Detects behavioral patterns with statistical rigor
- **Weekend vs Weekday Analysis**:
  - Compares calorie intake, exercise, net balance
  - Statistical significance testing (scipy t-tests)
  - p-value < 0.05 threshold for significance
  - Excludes holidays from weekday comparison for accuracy
- **Holiday Pattern Analysis**:
  - Polish holidays vs normal days
  - Long weekend detection and analysis
  - Tracks which holidays were observed in period
- **Day-of-Week Pattern Analysis**:
  - Analyzes all 7 days separately
  - Finds best day (lowest calories) and worst day (highest calories)
  - Per-day statistics (mean, std, min, max)
- **Comprehensive Analysis**:
  - Combines all pattern types
  - Temporal summary (coverage, data quality)
  - Human-readable pattern summaries

```python
from core.ml.patterns import PatternDetectionEngine

engine = PatternDetectionEngine(storage)

# Weekend pattern
weekend = engine.detect_weekend_pattern(days=90)
# Returns: {'detected': True, 'calories': {...}, 'pattern_summary': '...'}

# Holiday pattern
holiday = engine.detect_holiday_pattern(days=180)

# Day-of-week pattern
dow = engine.detect_day_of_week_pattern(days=90)

# All patterns at once
analysis = engine.get_comprehensive_analysis(days=90)
```

### 2. Streamlit UI (`app/pages/9_🔬_Pattern_Analysis.py`)

Multi-tab interface for pattern visualization:

#### **Tab 1: Overview** 📊
- Comprehensive analysis combining all patterns
- Data summary: total days, weekdays, weekends, holidays
- Coverage percentage (data quality indicator)
- Side-by-side pattern summaries (Weekend, Holiday, Day-of-Week)
- Quick metrics showing calorie differences

#### **Tab 2: Weekend Pattern** 🎊
- Weekend vs Weekday detailed comparison
- Statistics for both groups (avg, std dev)
- Calorie intake analysis
- Exercise analysis
- Statistical significance testing (t-test results, p-values)

#### **Tab 3: Holiday Pattern** 🎉
- Polish holiday behavior analysis
- Holiday vs Normal day comparison
- Long weekend detection and analysis
- List of holidays observed in period
- Calorie difference metrics with percentage changes

#### **Tab 4: Day-of-Week** 📅
- Analysis by day (Monday through Sunday)
- Best day and worst day identification
- Daily breakdown table (count, avg calories, min, max, exercise)
- Helps identify which specific days need attention

#### **Tab 5: Calendar** 📆
- Reference calendar of Polish holidays
- Year selector (2020-2030)
- Grouped by month for easy viewing
- Bilingual holiday names

**Settings Sidebar**:
- Analysis period slider (30-180 days)
- Pattern type legend
- Analysis tips

### 3. Testing (`tests/test_ml_patterns.py`)

**15 comprehensive tests** covering:

**Holiday Calendar Tests (5)**:
- Fixed holiday verification
- Easter calculation accuracy
- Holiday checking (positive/negative cases)
- Long weekend detection
- Days to/from holiday calculations

**Temporal Features Tests (3)**:
- Feature addition to DataFrame
- Polish day names
- Weekend/workweek/holiday flags

**Pattern Detection Tests (5)**:
- Weekend pattern detection with synthetic data
- Holiday pattern detection
- Day-of-week pattern detection
- Best/worst day identification
- Minimal data handling (edge cases)

**Statistical Analysis Tests (2)**:
- T-test significance validation
- Pattern summary generation

All tests use **fixtures with clear patterns** (e.g., weekends have +500 kcal) to ensure detection works correctly.

## Technical Architecture

### Data Flow

```
Storage (SQLite)
    ↓
PatternDetectionEngine._get_enriched_data()
    ↓
TemporalFeatureEngine.add_temporal_features()
    ↓
DataFrame with temporal columns
    ↓
Pattern detection methods (detect_weekend_pattern, etc.)
    ↓
Statistical analysis (scipy.stats.ttest_ind)
    ↓
Pattern summaries with human-readable text
    ↓
Streamlit UI visualization
```

### Key Design Decisions

1. **Non-invasive temporal features**: Features are added to DataFrames at analysis time, never stored in database
2. **Statistical rigor**: Uses scipy t-tests for pattern significance (not just eyeballing differences)
3. **Polish-specific**: Holidays and day names in Polish (bilingual support)
4. **Offline-first**: All calculations local, no external APIs
5. **Guard-rails**: Requires minimum data points before claiming pattern detection
6. **Separation of concerns**:
   - `holidays.py`: Pure calendar logic
   - `temporal_features.py`: Feature engineering
   - `patterns.py`: Statistical pattern detection
   - Streamlit UI: Visualization only

## Dependencies Added

```
scipy>=1.11.0  # For statistical testing (t-tests)
```

All other dependencies already present (pandas, numpy from existing modules).

## Files Created

```
core/ml/
├── __init__.py                 # Module exports
├── holidays.py                 # Polish holiday calendar (222 lines)
├── temporal_features.py        # Temporal feature engineering (172 lines)
└── patterns.py                 # Pattern detection engine (412 lines)

app/pages/
└── 9_🔬_Pattern_Analysis.py    # Streamlit UI (331 lines)

tests/
└── test_ml_patterns.py         # 15 comprehensive tests (270 lines)

docs/
└── BLOK_10_COMPLETE.md         # This file
```

## Files Modified

```
requirements.txt                # Added scipy>=1.11.0
app/main.py                     # Version 0.9.0 → 0.10.0
tests/test_smoke.py             # Version assertion updated
```

## Test Results

**160 tests passing** (145 previous + 15 new ML tests)

```bash
$ .venv/bin/pytest -v
===================== test session starts ======================
tests/test_export.py::test_excel_export_basic PASSED
tests/test_forecast.py::test_forecast_engine_basic PASSED
tests/test_kpis.py::test_kpi_calculation_complete PASSED
tests/test_llm.py::test_ollama_client_init PASSED
tests/test_metrics.py::test_deficit_calculator PASSED
tests/test_ml_patterns.py::test_polish_holidays_fixed PASSED
tests/test_ml_patterns.py::test_easter_calculation PASSED
tests/test_ml_patterns.py::test_is_holiday PASSED
tests/test_ml_patterns.py::test_temporal_features PASSED
tests/test_ml_patterns.py::test_weekend_pattern_detection PASSED
tests/test_ml_patterns.py::test_holiday_pattern_detection PASSED
tests/test_ml_patterns.py::test_day_of_week_pattern PASSED
... (148 more tests)
===================== 160 passed in 4.32s ======================
```

## Usage Examples

### Example 1: Check Weekend Pattern

```python
from core.storage import Storage
from core.ml.patterns import PatternDetectionEngine

storage = Storage("data/diet_app.db")
engine = PatternDetectionEngine(storage)

result = engine.detect_weekend_pattern(days=90)

if result['detected']:
    cal = result['calories']
    print(f"Weekend avg: {cal['weekend_avg']:.0f} kcal")
    print(f"Weekday avg: {cal['weekday_avg']:.0f} kcal")
    print(f"Difference: {cal['difference']:+.0f} kcal ({cal['difference_pct']:+.1f}%)")

    if cal['statistical_test']['significant']:
        print(f"✅ Statistically significant (p={cal['statistical_test']['p_value']:.4f})")

    print(f"\n{result['pattern_summary']}")
```

Output:
```
Weekend avg: 2150 kcal
Weekday avg: 1900 kcal
Difference: +250 kcal (+13.2%)
✅ Statistically significant (p=0.0032)

Weekend calorie intake is 250 kcal (13.2%) higher than weekdays (statistically significant).
```

### Example 2: Find Best and Worst Days

```python
result = engine.detect_day_of_week_pattern(days=90)

if result['detected']:
    best = result['best_day']
    worst = result['worst_day']

    print(f"🟢 Best day: {best['name']} ({best['avg_calories']:.0f} kcal)")
    print(f"🔴 Worst day: {worst['name']} ({worst['avg_calories']:.0f} kcal)")
    print(f"Difference: {worst['avg_calories'] - best['avg_calories']:.0f} kcal")
```

Output:
```
🟢 Best day: Wtorek (1850 kcal)
🔴 Worst day: Sobota (2200 kcal)
Difference: 350 kcal
```

### Example 3: Comprehensive Analysis

```python
analysis = engine.get_comprehensive_analysis(days=90)

print("📊 Temporal Summary:")
summary = analysis['temporal_summary']
print(f"  Total days: {summary['total_days']}")
print(f"  Weekends: {summary['weekend_days']}")
print(f"  Holidays: {summary['holiday_days']}")
print(f"  Coverage: {summary['coverage_pct']:.1f}%")

print("\n🎊 Weekend Pattern:")
if analysis['weekend_pattern']['detected']:
    print(f"  {analysis['weekend_pattern']['pattern_summary']}")

print("\n🎉 Holiday Pattern:")
if analysis['holiday_pattern']['detected']:
    print(f"  {analysis['holiday_pattern']['pattern_summary']}")

print("\n📅 Day-of-Week Pattern:")
if analysis['day_of_week_pattern']['detected']:
    print(f"  {analysis['day_of_week_pattern']['pattern_summary']}")
```

## Business Value

### For the User

1. **Quantifies intuition**: User observed weekend/holiday overeating - now has hard numbers
2. **Identifies specific problem days**: Knows exactly which days need attention
3. **Statistical validation**: Can trust patterns are real (not random variation)
4. **Actionable insights**: Can plan interventions for high-risk periods
5. **Progress tracking**: Monitor if weekend/holiday patterns improve over time

### Example Insights Generated

- "You consume 320 kcal more on weekends (statistically significant)"
- "Your best day is Tuesday (1850 kcal avg), worst is Saturday (2200 kcal avg)"
- "Polish holidays show 15% higher calorie intake vs normal days"
- "Long weekends: 8 days observed, avg 2100 kcal"

## Future Enhancements (Not Implemented)

Ideas for potential expansion:

1. **Holiday-aware forecasting**: Adjust predictions based on upcoming holidays
2. **Pattern visualizations**: Charts showing day-of-week trends over time
3. **Intervention recommendations**: Suggest specific actions for problem days
4. **Pattern alerts**: Notify user when entering high-risk periods (e.g., long weekend approaching)
5. **Habit strength scoring**: Quantify how consistent behavioral patterns are
6. **Cross-pattern analysis**: How weekends + holidays compound effects

## Lessons Learned

### Technical Challenges

1. **Attribute naming consistency**: Had to carefully match `cal_in_kcal` vs `calories_in` across codebase
2. **Date range handling**: Test fixtures needed to align with lookback periods
3. **Statistical significance**: Required scipy dependency for proper t-tests
4. **Easter calculation**: Complex algorithm but critical for Polish holiday accuracy
5. **Coverage percentage edge case**: Fixed bug where coverage could exceed 100% (when more data than requested period exists), causing Streamlit progress bar to crash

### Best Practices Applied

1. **Guard-rails**: Require minimum data before claiming patterns exist
2. **Separation of concerns**: Calendar logic separate from feature engineering separate from pattern detection
3. **Testability**: Clear synthetic data with obvious patterns for validation
4. **User language**: Pattern summaries in plain language (not just numbers)
5. **Bilingual support**: Polish names with English translations

## Conclusion

Block 10 successfully transforms the user's qualitative observation ("I overeat on weekends and holidays") into **quantitative, statistically-validated insights**. The ML pattern recognition engine provides:

✅ Weekend vs weekday behavioral analysis
✅ Polish holiday effect detection
✅ Day-of-week pattern identification
✅ Statistical significance testing
✅ Comprehensive temporal analysis
✅ User-friendly Streamlit interface
✅ 15 comprehensive tests (160 total)
✅ Offline-first, deterministic, CFO-grade

**The system now answers**: "How much more do I eat on weekends?" with precision and statistical confidence.

---

**Next Blocks**: Open for user direction. Potential areas:
- Advanced forecasting with pattern integration
- Habit strength scoring
- Intervention planning
- Goal optimization with temporal awareness
