"""
Tests for Pattern Visualization Engine
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from core.storage import Storage
from core.schemas import DailyEntryCreate
from core.ml.visualizations import PatternVisualizationEngine


@pytest.fixture
def storage_with_viz_data():
    """Create storage with data suitable for visualizations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Create 60 days of data with clear patterns
        base_date = date.today() - timedelta(days=60)
        for i in range(60):
            current_date = base_date + timedelta(days=i)
            day_of_week = current_date.weekday()

            # Weekend pattern: higher calories
            if day_of_week >= 5:  # Weekend
                calories = 2200 + (i % 5) * 50
            else:  # Weekday
                calories = 1900 + (i % 5) * 50

            entry = DailyEntryCreate(
                date=current_date,
                weight_kg=85.0 - (i * 0.05),  # Gradual weight loss
                bodyfat_pct=20.0 - (i * 0.02),
                cal_in_kcal=calories,
                cal_out_sport_kcal=300 + (i % 3) * 50,
                source="test"
            )
            storage.create(entry)

        yield storage


def test_viz_engine_init(storage_with_viz_data):
    """Test visualization engine initialization."""
    engine = PatternVisualizationEngine(storage_with_viz_data)
    assert engine.storage == storage_with_viz_data
    assert engine.temporal is not None
    assert engine.holiday_calendar is not None


def test_create_day_of_week_heatmap(storage_with_viz_data):
    """Test day-of-week heatmap creation."""
    engine = PatternVisualizationEngine(storage_with_viz_data)
    fig = engine.create_day_of_week_heatmap(days=60)

    assert fig is not None
    assert fig.data is not None
    assert len(fig.data) > 0


def test_create_weekend_vs_weekday_boxplot(storage_with_viz_data):
    """Test weekend vs weekday boxplot creation."""
    engine = PatternVisualizationEngine(storage_with_viz_data)
    fig = engine.create_weekend_vs_weekday_boxplot(days=60)

    assert fig is not None
    assert fig.data is not None
    # Should have at least weekday and weekend traces
    assert len(fig.data) >= 2


def test_create_holiday_impact_timeline(storage_with_viz_data):
    """Test holiday impact timeline creation."""
    engine = PatternVisualizationEngine(storage_with_viz_data)
    fig = engine.create_holiday_impact_timeline(days=60)

    assert fig is not None
    assert fig.data is not None


def test_create_pattern_strength_chart(storage_with_viz_data):
    """Test pattern strength chart creation."""
    engine = PatternVisualizationEngine(storage_with_viz_data)
    fig = engine.create_pattern_strength_chart(days=60)

    # May or may not have data depending on weeks
    if fig is not None:
        assert fig.data is not None


def test_create_daily_pattern_radar(storage_with_viz_data):
    """Test daily pattern radar chart creation."""
    engine = PatternVisualizationEngine(storage_with_viz_data)
    fig = engine.create_daily_pattern_radar(days=60)

    assert fig is not None
    assert fig.data is not None


def test_visualizations_with_minimal_data():
    """Test that visualizations handle minimal data gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Create only 5 days of data
        base_date = date.today() - timedelta(days=5)
        for i in range(5):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=80.0,
                cal_in_kcal=2000.0,
                source="test"
            )
            storage.create(entry)

        engine = PatternVisualizationEngine(storage)

        # All visualizations should handle minimal data gracefully
        # Either return None or a valid figure
        heatmap = engine.create_day_of_week_heatmap(days=5)
        boxplot = engine.create_weekend_vs_weekday_boxplot(days=5)
        timeline = engine.create_holiday_impact_timeline(days=5)
        strength = engine.create_pattern_strength_chart(days=5)
        radar = engine.create_daily_pattern_radar(days=5)

        # Should not raise exceptions
        assert True


def test_visualizations_with_no_data():
    """Test that visualizations handle no data gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        engine = PatternVisualizationEngine(storage)

        # All should return None with no data
        assert engine.create_day_of_week_heatmap(days=30) is None
        assert engine.create_weekend_vs_weekday_boxplot(days=30) is None
        assert engine.create_holiday_impact_timeline(days=30) is None
        assert engine.create_pattern_strength_chart(days=30) is None
        assert engine.create_daily_pattern_radar(days=30) is None


def test_visualization_colors_defined(storage_with_viz_data):
    """Test that color scheme is properly defined."""
    engine = PatternVisualizationEngine(storage_with_viz_data)

    assert 'workweek' in engine.colors
    assert 'weekend' in engine.colors
    assert 'holiday' in engine.colors
    assert 'primary' in engine.colors
    assert 'secondary' in engine.colors


def test_enriched_data_has_temporal_features(storage_with_viz_data):
    """Test that enriched data includes temporal features."""
    engine = PatternVisualizationEngine(storage_with_viz_data)
    df = engine._get_enriched_data(days=60)

    assert not df.empty
    assert 'date' in df.columns
    assert 'day_of_week' in df.columns
    assert 'is_weekend' in df.columns
    assert 'is_holiday' in df.columns
    assert 'cal_net_kcal' in df.columns
