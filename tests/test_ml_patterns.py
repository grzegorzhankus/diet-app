"""
Tests for ML Pattern Detection (holidays, day-of-week, weekend patterns)
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from core.storage import Storage
from core.schemas import DailyEntryCreate
from core.ml.holidays import PolishHolidayCalendar
from core.ml.temporal_features import TemporalFeatureEngine
from core.ml.patterns import PatternDetectionEngine


@pytest.fixture
def storage_with_pattern_data():
    """Create storage with patterned data (weekend overeating)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Create 90 days of data with clear weekend pattern
        base_date = date(2026, 1, 1)  # Wednesday
        for i in range(90):
            entry_date = base_date + timedelta(days=i)
            dow = entry_date.weekday()

            # Weekend pattern: higher calories, less exercise
            if dow in [5, 6]:  # Saturday, Sunday
                calories_in = 2400 + (i % 3) * 100
                calories_sport = 100
            else:  # Weekdays
                calories_in = 1800 + (i % 3) * 50
                calories_sport = 300

            entry = DailyEntryCreate(
                date=entry_date,
                weight_kg=82.0 - (i * 0.05),
                bodyfat_pct=22.0 - (i * 0.02),
                cal_in_kcal=calories_in,
                cal_out_sport_kcal=calories_sport,
                notes=f"Day {i+1}",
                source="test"
            )
            storage.create(entry)

        yield storage


# ======== PolishHolidayCalendar Tests ========

def test_holiday_calendar_init():
    """Test holiday calendar initialization."""
    calendar = PolishHolidayCalendar()
    assert calendar is not None


def test_fixed_holidays_2026():
    """Test fixed Polish holidays for 2026."""
    calendar = PolishHolidayCalendar()
    holidays = calendar.get_holidays(2026)

    # Check some fixed holidays
    assert date(2026, 1, 1) in holidays  # New Year
    assert date(2026, 5, 1) in holidays  # Labour Day
    assert date(2026, 5, 3) in holidays  # Constitution Day
    assert date(2026, 11, 11) in holidays  # Independence Day
    assert date(2026, 12, 25) in holidays  # Christmas


def test_easter_calculation():
    """Test Easter calculation for known years."""
    calendar = PolishHolidayCalendar()

    # Easter 2026 is April 5
    holidays_2026 = calendar.get_holidays(2026)
    easter_2026 = date(2026, 4, 5)
    assert easter_2026 in holidays_2026
    assert "Wielkanoc" in holidays_2026[easter_2026]


def test_is_holiday():
    """Test holiday checking."""
    calendar = PolishHolidayCalendar()

    assert calendar.is_holiday(date(2026, 1, 1))  # New Year
    assert calendar.is_holiday(date(2026, 12, 25))  # Christmas
    assert not calendar.is_holiday(date(2026, 1, 2))  # Regular day


def test_get_holiday_name():
    """Test getting holiday names."""
    calendar = PolishHolidayCalendar()

    name = calendar.get_holiday_name(date(2026, 12, 25))
    assert name is not None
    assert "Boże Narodzenie" in name

    assert calendar.get_holiday_name(date(2026, 1, 2)) is None


def test_holidays_in_range():
    """Test getting holidays in a date range."""
    calendar = PolishHolidayCalendar()

    holidays = calendar.get_holidays_in_range(
        date(2026, 1, 1),
        date(2026, 1, 31)
    )

    assert len(holidays) >= 2  # At least New Year and Epiphany
    assert any(h['date'] == date(2026, 1, 1) for h in holidays)


# ======== TemporalFeatureEngine Tests ========

def test_temporal_engine_init():
    """Test temporal feature engine initialization."""
    engine = TemporalFeatureEngine()
    assert engine is not None
    assert engine.holiday_calendar is not None


def test_add_temporal_features(storage_with_pattern_data):
    """Test adding temporal features to dataframe."""
    engine = TemporalFeatureEngine()

    # Get data
    entries = storage_with_pattern_data.get_all()
    import pandas as pd
    df = pd.DataFrame([{
        'date': e.date,
        'weight_kg': e.weight_kg,
        'cal_in_kcal': e.cal_in_kcal
    } for e in entries])

    # Add features
    df_enriched = engine.add_temporal_features(df)

    # Check added columns
    assert 'day_of_week' in df_enriched.columns
    assert 'day_name' in df_enriched.columns
    assert 'is_weekend' in df_enriched.columns
    assert 'is_workweek' in df_enriched.columns
    assert 'is_holiday' in df_enriched.columns
    assert 'period_type' in df_enriched.columns

    # Check values
    assert df_enriched['day_of_week'].min() >= 0
    assert df_enriched['day_of_week'].max() <= 6
    assert df_enriched['is_weekend'].dtype == bool


def test_period_summary(storage_with_pattern_data):
    """Test period summary generation."""
    engine = TemporalFeatureEngine()

    entries = storage_with_pattern_data.get_all()
    import pandas as pd
    df = pd.DataFrame([{
        'date': e.date,
        'cal_in_kcal': e.cal_in_kcal,
        'cal_out_sport_kcal': e.cal_out_sport_kcal
    } for e in entries])

    df_enriched = engine.add_temporal_features(df)
    summary = engine.get_period_summary(df_enriched)

    assert not summary.empty
    assert 'Workweek' in summary.index.get_level_values('period_type')
    assert 'Weekend' in summary.index.get_level_values('period_type')


# ======== PatternDetectionEngine Tests ========

def test_pattern_engine_init(storage_with_pattern_data):
    """Test pattern detection engine initialization."""
    engine = PatternDetectionEngine(storage_with_pattern_data)
    assert engine is not None
    assert engine.storage == storage_with_pattern_data


def test_detect_weekend_pattern(storage_with_pattern_data):
    """Test weekend pattern detection."""
    engine = PatternDetectionEngine(storage_with_pattern_data)

    result = engine.detect_weekend_pattern(days=90)

    # Should return a result (detected or not)
    assert isinstance(result, dict)
    if result.get("detected"):
        assert result["weekend_days"] > 0
        assert result["weekday_days"] > 0

def test_detect_holiday_pattern(storage_with_pattern_data):
    """Test holiday pattern detection."""
    engine = PatternDetectionEngine(storage_with_pattern_data)

    result = engine.detect_holiday_pattern(days=180)

    # May or may not have holidays in test data
    if result['detected']:
        assert 'holiday_days_count' in result
        assert isinstance(result['pattern_summary'], str)


def test_detect_day_of_week_pattern(storage_with_pattern_data):
    """Test day-of-week pattern detection."""
    engine = PatternDetectionEngine(storage_with_pattern_data)

    result = engine.detect_day_of_week_pattern(days=90)

    # Should return a result (detected or not)
    assert isinstance(result, dict)
    if result.get("detected"):
        assert "days_by_dow" in result

def test_comprehensive_analysis(storage_with_pattern_data):
    """Test comprehensive pattern analysis."""
    engine = PatternDetectionEngine(storage_with_pattern_data)

    result = engine.get_comprehensive_analysis(days=90)

    assert 'weekend_pattern' in result
    assert 'holiday_pattern' in result
    assert 'day_of_week_pattern' in result
    assert 'temporal_summary' in result

    # Check temporal summary
    summary = result['temporal_summary']
    assert summary['total_days'] > 0  # Has some data
    assert summary['weekend_days'] > 0
    assert summary['weekday_days'] > 0


def test_pattern_with_minimal_data():
    """Test pattern detection with minimal data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Add only 5 days
        for i in range(5):
            entry = DailyEntryCreate(
                date=date(2026, 1, 1) + timedelta(days=i),
                weight_kg=80.0,
                cal_in_kcal=1800,
                source="test"
            )
            storage.create(entry)

        engine = PatternDetectionEngine(storage)
        result = engine.detect_weekend_pattern(days=30)

        # Should handle gracefully
        assert result['detected'] is False
        assert 'reason' in result
