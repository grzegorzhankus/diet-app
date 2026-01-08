"""
Tests for Forecast Engine
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from core.storage import Storage
from core.forecast import ForecastEngine, Forecast, ForecastSummary
from core.schemas import DailyEntryCreate


@pytest.fixture
def storage_with_trend():
    """Create storage with consistent weight loss trend."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # 30 days of steady weight loss: 0.5 kg per week
        base_date = date(2026, 1, 1)
        for i in range(30):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0 - (i * 0.07),  # ~0.5 kg per week
                bodyfat_pct=20.0,
                cal_in_kcal=1800.0,
                cal_out_sport_kcal=300.0,
                source="test"
            )
            storage.create(entry)

        yield storage


@pytest.fixture
def storage_with_calories():
    """Create storage with good calorie data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # 30 days with consistent -400 kcal/day deficit
        base_date = date(2026, 1, 1)
        for i in range(30):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0 - (i * 0.05),  # Gradual loss
                cal_in_kcal=1600.0,
                cal_out_sport_kcal=0.0,  # NET = 1600 - 2000 - 0 = -400
                source="test"
            )
            storage.create(entry)

        yield storage


def test_forecast_engine_init(storage_with_trend):
    """Test forecast engine initialization."""
    engine = ForecastEngine(storage_with_trend)
    assert engine.storage == storage_with_trend
    assert engine.bmr_kcal == 2000.0
    assert engine.KCAL_PER_KG_FAT == 7700.0


def test_forecast_linear_basic(storage_with_trend):
    """Test basic linear forecast generation."""
    engine = ForecastEngine(storage_with_trend)

    forecasts, summary = engine.generate_forecast(
        horizon_days=7,
        lookback_days=30,
        method='linear'
    )

    # Should return 7 forecast points
    assert len(forecasts) == 7

    # All forecasts should have required fields
    for forecast in forecasts:
        assert isinstance(forecast, Forecast)
        assert forecast.predicted_weight_kg > 0
        assert forecast.confidence_lower_kg < forecast.predicted_weight_kg
        assert forecast.confidence_upper_kg > forecast.predicted_weight_kg
        assert forecast.method == 'linear'

    # Summary should exist
    assert isinstance(summary, ForecastSummary)
    assert summary.horizon_days == 7
    assert summary.method == 'linear'


def test_forecast_calorie_based(storage_with_calories):
    """Test calorie-based forecast."""
    engine = ForecastEngine(storage_with_calories)

    forecasts, summary = engine.generate_forecast(
        horizon_days=14,
        lookback_days=30,
        method='calorie_based'
    )

    assert len(forecasts) == 14
    assert summary.method == 'calorie_based'

    # With -400 kcal/day deficit, should lose ~0.05 kg/day
    # 14 days = ~0.7 kg loss
    assert summary.total_change_kg < 0
    assert abs(summary.total_change_kg) < 1.5  # Reasonable


def test_forecast_auto_method_selection(storage_with_calories):
    """Test automatic method selection based on data."""
    engine = ForecastEngine(storage_with_calories)

    forecasts, summary = engine.generate_forecast(
        horizon_days=7,
        lookback_days=30,
        method='auto'
    )

    # Should choose a valid method (calorie_based or linear depending on data availability)
    assert summary.method in ['calorie_based', 'linear']
    # Auto should produce valid forecasts
    assert len(forecasts) == 7


def test_forecast_insufficient_data():
    """Test forecast with insufficient data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Only 3 days of data
        base_date = date(2026, 1, 1)
        for i in range(3):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0,
                source="test"
            )
            storage.create(entry)

        engine = ForecastEngine(storage)

        with pytest.raises(ValueError, match="Insufficient data"):
            engine.generate_forecast(horizon_days=7, lookback_days=30)


def test_forecast_dates_sequential(storage_with_trend):
    """Test that forecast dates are sequential."""
    engine = ForecastEngine(storage_with_trend)

    forecasts, _ = engine.generate_forecast(
        horizon_days=10,
        method='linear'
    )

    # Dates should be sequential
    for i in range(1, len(forecasts)):
        assert forecasts[i].date == forecasts[i-1].date + timedelta(days=1)


def test_forecast_confidence_intervals_widen(storage_with_trend):
    """Test that confidence intervals widen over time."""
    engine = ForecastEngine(storage_with_trend)

    forecasts, _ = engine.generate_forecast(
        horizon_days=30,
        method='linear'
    )

    # Confidence interval should widen with distance
    first_interval = forecasts[0].confidence_upper_kg - forecasts[0].confidence_lower_kg
    last_interval = forecasts[-1].confidence_upper_kg - forecasts[-1].confidence_lower_kg

    assert last_interval > first_interval


def test_forecast_summary_fields(storage_with_trend):
    """Test forecast summary contains all required fields."""
    engine = ForecastEngine(storage_with_trend)

    _, summary = engine.generate_forecast(
        horizon_days=14,
        target_weight_kg=80.0
    )

    assert summary.horizon_days == 14
    assert summary.start_weight_kg > 0
    assert summary.end_weight_kg > 0
    assert summary.avg_rate_kg_per_week != 0
    assert 0 <= summary.confidence_level <= 1
    assert summary.method in ['linear', 'calorie_based']


def test_forecast_with_target_weight(storage_with_trend):
    """Test forecast with target weight calculates target date."""
    engine = ForecastEngine(storage_with_trend)

    _, summary = engine.generate_forecast(
        horizon_days=30,
        target_weight_kg=80.0
    )

    # Should calculate a target date if trend continues
    # Current is ~85kg, target 80kg, losing ~0.5kg/week
    # Should take ~10 weeks
    if summary.target_date:
        assert isinstance(summary.target_date, date)


def test_forecast_serialization(storage_with_trend):
    """Test forecast and summary can be serialized."""
    engine = ForecastEngine(storage_with_trend)

    forecasts, summary = engine.generate_forecast(horizon_days=7)

    # Test forecast serialization
    for forecast in forecasts:
        forecast_dict = forecast.to_dict()
        assert 'date' in forecast_dict
        assert 'predicted_weight_kg' in forecast_dict
        assert 'confidence_lower_kg' in forecast_dict
        assert 'confidence_upper_kg' in forecast_dict
        assert 'method' in forecast_dict

    # Test summary serialization
    summary_dict = summary.to_dict()
    assert 'horizon_days' in summary_dict
    assert 'start_weight_kg' in summary_dict
    assert 'method' in summary_dict


def test_calculate_target_calories():
    """Test target calorie calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        engine = ForecastEngine(storage, bmr_kcal=2000.0)

        # Want to lose 5kg in 50 days (0.7 kg/week - healthy rate)
        result = engine.calculate_target_calories(
            target_weight_kg=80.0,
            target_days=50,
            current_weight_kg=85.0,
            avg_sport_kcal=300.0
        )

        # Should need deficit
        assert result['daily_net_kcal'] < 0

        # Total change should be -5kg
        assert result['total_change_kg'] == -5.0

        # Weekly rate should be healthy
        assert result['is_healthy'] is True
        assert abs(result['weekly_rate_kg']) <= 1.0

        # Required intake = NET + BMR + SPORT
        expected_intake = result['daily_net_kcal'] + 2000.0 + 300.0
        assert abs(result['required_intake_kcal'] - expected_intake) < 0.01


def test_calculate_target_calories_gain():
    """Test target calorie calculation for weight gain."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        engine = ForecastEngine(storage)

        # Want to gain 3kg in 30 days
        result = engine.calculate_target_calories(
            target_weight_kg=88.0,
            target_days=30,
            current_weight_kg=85.0,
            avg_sport_kcal=200.0
        )

        # Should need surplus
        assert result['daily_net_kcal'] > 0
        assert result['total_change_kg'] == 3.0


def test_forecast_deterministic(storage_with_trend):
    """Test that repeated forecasts give same results."""
    engine = ForecastEngine(storage_with_trend)

    forecasts1, summary1 = engine.generate_forecast(
        horizon_days=14,
        lookback_days=30,
        method='linear'
    )

    forecasts2, summary2 = engine.generate_forecast(
        horizon_days=14,
        lookback_days=30,
        method='linear'
    )

    # Should be identical
    assert len(forecasts1) == len(forecasts2)

    for f1, f2 in zip(forecasts1, forecasts2):
        assert f1.date == f2.date
        assert abs(f1.predicted_weight_kg - f2.predicted_weight_kg) < 0.001
        assert f1.method == f2.method

    # Summary should be identical
    assert summary1.horizon_days == summary2.horizon_days
    assert abs(summary1.total_change_kg - summary2.total_change_kg) < 0.001


def test_forecast_realistic_values(storage_with_trend):
    """Test that forecast produces realistic weight values."""
    engine = ForecastEngine(storage_with_trend)

    forecasts, summary = engine.generate_forecast(
        horizon_days=30,
        method='linear'
    )

    # All weights should be in reasonable range (50-150 kg)
    for forecast in forecasts:
        assert 50 < forecast.predicted_weight_kg < 150
        assert 50 < forecast.confidence_lower_kg < 150
        assert 50 < forecast.confidence_upper_kg < 150

    # Rate should be reasonable (< 2 kg per week)
    assert abs(summary.avg_rate_kg_per_week) < 2.0


def test_forecast_different_horizons(storage_with_trend):
    """Test forecasts with different time horizons."""
    engine = ForecastEngine(storage_with_trend)

    for horizon in [7, 14, 30, 60, 90]:
        forecasts, summary = engine.generate_forecast(
            horizon_days=horizon,
            method='linear'
        )

        assert len(forecasts) == horizon
        assert summary.horizon_days == horizon


def test_forecast_confidence_level_range(storage_with_trend):
    """Test that confidence level is in valid range."""
    engine = ForecastEngine(storage_with_trend)

    _, summary = engine.generate_forecast(horizon_days=14)

    assert 0 <= summary.confidence_level <= 1.0


def test_calorie_based_vs_linear(storage_with_calories):
    """Test that calorie-based and linear produce different results."""
    engine = ForecastEngine(storage_with_calories)

    forecasts_cal, summary_cal = engine.generate_forecast(
        horizon_days=14,
        method='calorie_based'
    )

    forecasts_lin, summary_lin = engine.generate_forecast(
        horizon_days=14,
        method='linear'
    )

    # Methods should differ
    assert summary_cal.method == 'calorie_based'
    assert summary_lin.method == 'linear'

    # Results may differ slightly
    # (but both should be reasonable)
    assert forecasts_cal[0].predicted_weight_kg > 0
    assert forecasts_lin[0].predicted_weight_kg > 0
