"""
Golden set tests for KPI engine
Tests deterministic KPI calculations.
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from core.storage import Storage
from core.kpi_engine import KPIEngine
from core.schemas import DailyEntryCreate


@pytest.fixture
def storage_with_losing_trend():
    """Create storage with weight-losing trend data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Create 30 days of weight-losing data
        base_date = date(2026, 1, 1)
        for i in range(30):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0 - (i * 0.1),  # Losing 0.1 kg/day
                bodyfat_pct=20.0 - (i * 0.05),
                cal_in_kcal=2000.0,
                cal_out_sport_kcal=400.0,
                source="test"
            )
            storage.create(entry)

        yield storage


def test_kpi_engine_init(storage_with_losing_trend):
    """Test KPI engine initialization."""
    kpi_engine = KPIEngine(storage_with_losing_trend, target_weight_kg=75.0)
    assert kpi_engine.storage == storage_with_losing_trend
    assert kpi_engine.target_weight_kg == 75.0


def test_compute_all_kpis(storage_with_losing_trend):
    """Test computing all KPIs."""
    kpi_engine = KPIEngine(storage_with_losing_trend, target_weight_kg=75.0)
    kpis = kpi_engine.compute_all_kpis(days=30)

    # Should return multiple KPIs (at least 8 core ones)
    assert len(kpis) >= 8

    # All KPIs should have required fields
    for kpi in kpis:
        assert kpi.id is not None
        assert kpi.name is not None
        assert kpi.unit is not None
        assert kpi.explanation is not None
        assert kpi.formula is not None


def test_kpi_weight_change_exists(storage_with_losing_trend):
    """Test that weight change KPI is computed."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    change_kpi = next((k for k in kpis if k.id == 'KPI_Weight_Change_30d'), None)
    assert change_kpi is not None
    assert change_kpi.value < 0  # Should be losing weight


def test_kpi_bf_change_exists(storage_with_losing_trend):
    """Test that body fat change KPI is computed."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    bf_kpi = next((k for k in kpis if k.id == 'KPI_BF_Change_30d'), None)
    assert bf_kpi is not None
    assert bf_kpi.value < 0  # Should be losing BF%


def test_kpi_calories_exist(storage_with_losing_trend):
    """Test that calorie KPIs are computed."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    # Find calorie-related KPIs
    cal_kpis = [k for k in kpis if 'Calories' in k.id or 'Intake' in k.id or 'Sport' in k.id]
    assert len(cal_kpis) >= 2  # Should have at least intake and sport


def test_kpi_consistency_coverage(storage_with_losing_trend):
    """Test consistency coverage KPI."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    cov_kpi = next((k for k in kpis if k.id == 'KPI_Consistency_Coverage_30d'), None)
    assert cov_kpi is not None

    # Should have some coverage
    assert cov_kpi.value > 0


def test_kpi_streak_days(storage_with_losing_trend):
    """Test streak days KPI."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    streak_kpi = next((k for k in kpis if k.id == 'KPI_Streak_Days'), None)
    assert streak_kpi is not None
    assert streak_kpi.value >= 7  # Should have at least 7-day streak


def test_kpi_adherence_score(storage_with_losing_trend):
    """Test adherence score KPI."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    adh_kpi = next((k for k in kpis if k.id == 'KPI_Adherence_Score'), None)
    assert adh_kpi is not None

    # Should have reasonable score
    assert 0 <= adh_kpi.value <= 100


def test_kpi_with_missing_data():
    """Test KPIs with missing data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Create sparse data
        base_date = date(2026, 1, 1)
        for i in [0, 3, 7, 10, 15, 20, 25, 29]:  # Only 8 days out of 30
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0 - (i * 0.1),
                source="test"
            )
            storage.create(entry)

        kpi_engine = KPIEngine(storage)
        kpis = kpi_engine.compute_all_kpis(days=30)

        # Should still compute some KPIs
        assert len(kpis) > 0


def test_kpi_deterministic_repeated_calls(storage_with_losing_trend):
    """Test that repeated KPI calculations are deterministic."""
    kpi_engine = KPIEngine(storage_with_losing_trend, target_weight_kg=75.0)

    kpis1 = kpi_engine.compute_all_kpis(days=30)
    kpis2 = kpi_engine.compute_all_kpis(days=30)

    # Should have same number of KPIs
    assert len(kpis1) == len(kpis2)

    # Each KPI should have identical values
    for kpi1, kpi2 in zip(kpis1, kpis2):
        assert kpi1.id == kpi2.id
        # Handle None values
        if kpi1.value is None:
            assert kpi2.value is None
        else:
            assert kpi1.value == kpi2.value
        assert kpi1.is_good == kpi2.is_good


def test_kpi_to_dict(storage_with_losing_trend):
    """Test KPI to_dict serialization."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    for kpi in kpis:
        kpi_dict = kpi.to_dict()

        assert 'id' in kpi_dict
        assert 'name' in kpi_dict
        assert 'value' in kpi_dict
        assert 'unit' in kpi_dict
        assert 'explanation' in kpi_dict
        assert 'formula' in kpi_dict


def test_kpi_values_reasonable(storage_with_losing_trend):
    """Test that KPI values are reasonable."""
    kpi_engine = KPIEngine(storage_with_losing_trend)
    kpis = kpi_engine.compute_all_kpis(days=30)

    for kpi in kpis:
        # All numeric KPIs should have value or None
        if kpi.value is not None:
            assert isinstance(kpi.value, (int, float))

        # is_good should be bool or None
        assert kpi.is_good in [True, False, None]
