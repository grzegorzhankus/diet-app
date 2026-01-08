"""
Golden set tests for metrics engine
Tests on real data to ensure deterministic calculations.
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from core.storage import Storage
from core.metrics import MetricsEngine
from core.schemas import DailyEntryCreate


@pytest.fixture
def storage_with_data():
    """Create storage with sample golden data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Create 30 days of consistent data
        base_date = date(2026, 1, 1)
        for i in range(30):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0 - (i * 0.1),  # Decreasing weight
                bodyfat_pct=20.0 - (i * 0.05),  # Decreasing BF%
                cal_in_kcal=2000.0,
                cal_out_sport_kcal=400.0,
                source="test"
            )
            storage.create(entry)

        yield storage


def test_metrics_engine_init(storage_with_data):
    """Test metrics engine initialization."""
    metrics = MetricsEngine(storage_with_data)
    assert metrics.storage == storage_with_data


def test_get_metrics_dataframe_basic(storage_with_data):
    """Test getting metrics dataframe."""
    metrics = MetricsEngine(storage_with_data)
    df = metrics.get_metrics_dataframe()

    assert len(df) == 30
    assert 'bs_weight_kg' in df.columns
    assert 'date' in df.columns


def test_body_composition_calculation(storage_with_data):
    """Test body composition calculations are deterministic."""
    metrics = MetricsEngine(storage_with_data)
    df = metrics.get_metrics_dataframe()

    # Check fat mass calculation
    # First entry: 85.0 kg * 20.0% = 17.0 kg
    first_row = df.iloc[0]
    expected_fat_mass = 85.0 * 0.20
    assert abs(first_row['bs_fat_mass_kg'] - expected_fat_mass) < 0.01

    # Check lean mass calculation
    # Lean mass = 85.0 - 17.0 = 68.0 kg
    expected_lean_mass = 85.0 - expected_fat_mass
    assert abs(first_row['bs_lean_mass_kg'] - expected_lean_mass) < 0.01

    # Last entry: 82.1 kg * 18.6% (18.55% rounded) ≈ 15.27 kg
    last_row = df.iloc[-1]
    # Note: 18.55% gets rounded to 18.6% by our validator
    expected_fat_mass_last = 82.1 * (18.6 / 100.0)
    assert abs(last_row['bs_fat_mass_kg'] - expected_fat_mass_last) < 0.01


def test_calorie_metrics_calculation(storage_with_data):
    """Test calorie metrics are deterministic."""
    metrics = MetricsEngine(storage_with_data)
    df = metrics.get_metrics_dataframe()

    # Net calories = 2000 (IN) - 2000 (BMR) - 400 (SPORT) = -400 kcal (for all entries)
    expected_net = -400.0

    # Check all entries have correct net calories
    for idx, row in df.iterrows():
        assert abs(row['cal_net_kcal'] - expected_net) < 0.01


def test_rolling_averages_7d(storage_with_data):
    """Test 7-day rolling average calculation."""
    metrics = MetricsEngine(storage_with_data)
    df = metrics.get_metrics_dataframe()

    # Check 7-day rolling average exists
    assert 'bs_weight_7d_avg_kg' in df.columns

    # First 6 entries should have NaN or partial averages
    # 7th entry (index 6) should have first full 7-day average
    seventh_entry = df.iloc[6]

    # Average of first 7 days: 85.0, 84.9, 84.8, ..., 84.4
    # = (85.0 + 84.9 + 84.8 + 84.7 + 84.6 + 84.5 + 84.4) / 7
    expected_avg = sum([85.0 - (i * 0.1) for i in range(7)]) / 7
    assert abs(seventh_entry['bs_weight_7d_avg_kg'] - expected_avg) < 0.01


def test_rolling_averages_14d(storage_with_data):
    """Test 14-day rolling average calculation."""
    metrics = MetricsEngine(storage_with_data)
    df = metrics.get_metrics_dataframe()

    assert 'bs_weight_14d_avg_kg' in df.columns

    # 14th entry (index 13) should have first full 14-day average
    fourteenth_entry = df.iloc[13]

    expected_avg = sum([85.0 - (i * 0.1) for i in range(14)]) / 14
    assert abs(fourteenth_entry['bs_weight_14d_avg_kg'] - expected_avg) < 0.01


def test_rolling_averages_30d(storage_with_data):
    """Test 30-day rolling average calculation."""
    metrics = MetricsEngine(storage_with_data)
    df = metrics.get_metrics_dataframe()

    assert 'bs_weight_30d_avg_kg' in df.columns

    # Last entry should have full 30-day average
    last_entry = df.iloc[-1]

    expected_avg = sum([85.0 - (i * 0.1) for i in range(30)]) / 30
    assert abs(last_entry['bs_weight_30d_avg_kg'] - expected_avg) < 0.01


def test_calorie_rolling_averages(storage_with_data):
    """Test calorie rolling averages."""
    metrics = MetricsEngine(storage_with_data)
    df = metrics.get_metrics_dataframe()

    assert 'cal_net_7d_avg_kcal' in df.columns

    # Since net calories are constant (-400), rolling average should also be -400
    seventh_entry = df.iloc[6]
    assert abs(seventh_entry['cal_net_7d_avg_kcal'] - (-400.0)) < 0.01


def test_summary_stats_deterministic(storage_with_data):
    """Test summary statistics are deterministic."""
    metrics = MetricsEngine(storage_with_data)

    # Get all data (no date filter)
    df = metrics.get_metrics_dataframe()

    # Verify we have all 30 entries
    assert len(df) == 30

    # Test that stats calculation is deterministic
    # Using actual values from dataframe rather than hardcoded expectations
    stats = metrics.get_summary_stats(days=30)

    # Weight change should be negative (decreasing trend)
    assert stats['weight_change_kg'] < 0

    # Current weight should be less than start weight
    assert stats['weight_current_kg'] < stats['weight_start_kg']

    # Check calorie stats are correct
    assert abs(stats['cal_net_avg_kcal'] - (-400.0)) < 0.01
    assert abs(stats['cal_in_avg_kcal'] - 2000.0) < 0.01
    assert abs(stats['cal_out_sport_avg_kcal'] - 400.0) < 0.01
    assert stats['cal_out_bmr_kcal'] == 2000.0
    assert abs(stats['cal_out_total_avg_kcal'] - 2400.0) < 0.01

    # Verify actual dataframe values match expected pattern
    # First entry: 85.0 kg
    assert abs(df.iloc[0]['bs_weight_kg'] - 85.0) < 0.01
    # Last entry: 82.1 kg
    assert abs(df.iloc[-1]['bs_weight_kg'] - 82.1) < 0.01


def test_metrics_with_missing_data():
    """Test metrics handle missing data correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Create data with gaps (today = 2026-01-07, so only last 4 entries in 11-day window)
        base_date = date(2026, 1, 1)
        for i in [0, 2, 4, 6, 8, 10]:  # Only even days
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0,
                source="test"
            )
            storage.create(entry)

        metrics = MetricsEngine(storage)
        df = metrics.get_metrics_dataframe(days=11)

        # Storage get_all with days filter uses date range, not all entries
        # Should have 4 entries within last 11 days from latest (2026-01-11)
        assert len(df) >= 4

        # Data coverage
        stats = metrics.get_summary_stats(days=11)
        # Coverage is based on actual days present vs requested
        assert stats['data_coverage'] > 0


def test_metrics_empty_dataframe():
    """Test metrics with no data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        metrics = MetricsEngine(storage)
        df = metrics.get_metrics_dataframe()

        assert df.empty

        stats = metrics.get_summary_stats()
        assert stats == {}


def test_deterministic_repeated_calls(storage_with_data):
    """Test that repeated calls give identical results (determinism)."""
    import math
    metrics = MetricsEngine(storage_with_data)

    df1 = metrics.get_metrics_dataframe()
    df2 = metrics.get_metrics_dataframe()

    # Should be identical
    assert df1.equals(df2)

    stats1 = metrics.get_summary_stats(days=30)
    stats2 = metrics.get_summary_stats(days=30)

    # Should be identical (handle NaN comparison)
    for key in stats1:
        val1, val2 = stats1[key], stats2[key]
        # Handle NaN case
        if isinstance(val1, float) and math.isnan(val1):
            assert math.isnan(val2), f"Key {key}: {val1} != {val2}"
        else:
            assert val1 == val2, f"Key {key}: {val1} != {val2}"
