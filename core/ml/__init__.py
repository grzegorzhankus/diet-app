"""
Machine Learning module for DIET_APP
Provides pattern recognition, temporal analysis, and enhanced forecasting.
"""
from core.ml.patterns import PatternDetectionEngine
from core.ml.holidays import PolishHolidayCalendar
from core.ml.temporal_features import TemporalFeatureEngine
from core.ml.visualizations import PatternVisualizationEngine

__all__ = [
    'PatternDetectionEngine',
    'PolishHolidayCalendar',
    'TemporalFeatureEngine',
    'PatternVisualizationEngine'
]
