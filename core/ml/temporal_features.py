"""
Temporal Feature Engineering for DIET_APP
Enriches data with day-of-week, weekend, holiday, and time-based features.
"""
import pandas as pd
from datetime import date
from typing import Optional

from core.ml.holidays import PolishHolidayCalendar


class TemporalFeatureEngine:
    """
    Adds temporal features to diet/training data for pattern analysis.
    """

    # Polish day names for better readability
    POLISH_DAYS = {
        0: 'Poniedziałek',
        1: 'Wtorek',
        2: 'Środa',
        3: 'Czwartek',
        4: 'Piątek',
        5: 'Sobota',
        6: 'Niedziela'
    }

    def __init__(self):
        """Initialize temporal feature engine."""
        self.holiday_calendar = PolishHolidayCalendar()

    def add_temporal_features(self, df: pd.DataFrame, date_column: str = 'date') -> pd.DataFrame:
        """
        Add comprehensive temporal features to dataframe.

        Args:
            df: DataFrame with date column
            date_column: Name of date column

        Returns:
            DataFrame with added temporal features
        """
        if df.empty:
            return df

        df = df.copy()

        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column])

        # Basic day features
        df['day_of_week'] = df[date_column].dt.dayofweek
        df['day_name'] = df['day_of_week'].map(self.POLISH_DAYS)
        df['day_name_en'] = df[date_column].dt.day_name()

        # Weekend indicator
        df['is_weekend'] = df['day_of_week'].isin([5, 6])  # Saturday, Sunday

        # Work week indicator
        df['is_workweek'] = ~df['is_weekend']

        # Week number
        df['week_of_year'] = df[date_column].dt.isocalendar().week
        df['month'] = df[date_column].dt.month
        df['quarter'] = df[date_column].dt.quarter
        df['year'] = df[date_column].dt.year

        # Holiday features
        df['is_holiday'] = df[date_column].apply(
            lambda x: self.holiday_calendar.is_holiday(x.date())
        )
        df['holiday_name'] = df[date_column].apply(
            lambda x: self.holiday_calendar.get_holiday_name(x.date())
        )

        # Long weekend indicator
        df['is_long_weekend'] = df[date_column].apply(
            lambda x: self.holiday_calendar.is_long_weekend(x.date())
        )

        # Days to/from holiday
        df['days_to_next_holiday'] = df[date_column].apply(
            lambda x: self.holiday_calendar.days_to_next_holiday(x.date())
        )
        df['days_since_last_holiday'] = df[date_column].apply(
            lambda x: self.holiday_calendar.days_since_last_holiday(x.date())
        )

        # Period type (workweek/weekend/holiday)
        df['period_type'] = 'Workweek'
        df.loc[df['is_weekend'], 'period_type'] = 'Weekend'
        df.loc[df['is_holiday'], 'period_type'] = 'Holiday'
        df.loc[df['is_long_weekend'] & ~df['is_holiday'], 'period_type'] = 'Long Weekend'

        # Day type for analysis (useful for grouping)
        df['day_type'] = df['period_type'].copy()

        return df

    def get_period_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary statistics by period type (workweek/weekend/holiday).

        Args:
            df: DataFrame with temporal features

        Returns:
            Summary DataFrame
        """
        if 'period_type' not in df.columns:
            df = self.add_temporal_features(df)

        # Columns to summarize
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        # Remove temporal feature columns from aggregation
        exclude_cols = ['day_of_week', 'week_of_year', 'month', 'quarter', 'year',
                       'days_to_next_holiday', 'days_since_last_holiday']
        agg_cols = [col for col in numeric_cols if col not in exclude_cols]

        if not agg_cols:
            return pd.DataFrame()

        # Group by period type and compute statistics
        summary = df.groupby('period_type')[agg_cols].agg(['mean', 'std', 'count'])

        return summary

    def get_dow_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary statistics by day of week.

        Args:
            df: DataFrame with temporal features

        Returns:
            Summary DataFrame indexed by day name
        """
        if 'day_name' not in df.columns:
            df = self.add_temporal_features(df)

        # Columns to summarize
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        # Remove temporal feature columns
        exclude_cols = ['day_of_week', 'week_of_year', 'month', 'quarter', 'year',
                       'days_to_next_holiday', 'days_since_last_holiday']
        agg_cols = [col for col in numeric_cols if col not in exclude_cols]

        if not agg_cols:
            return pd.DataFrame()

        # Group by day and compute statistics
        summary = df.groupby(['day_of_week', 'day_name'])[agg_cols].agg(['mean', 'std', 'count'])

        # Sort by day of week
        summary = summary.sort_index(level='day_of_week')

        return summary

    def get_holiday_analysis(self, df: pd.DataFrame) -> dict:
        """
        Analyze behavior around holidays.

        Args:
            df: DataFrame with temporal features

        Returns:
            Dict with holiday analysis
        """
        if 'is_holiday' not in df.columns:
            df = self.add_temporal_features(df)

        analysis = {
            'total_days': len(df),
            'holiday_days': df['is_holiday'].sum(),
            'long_weekend_days': df['is_long_weekend'].sum(),
            'workweek_days': df['is_workweek'].sum(),
            'weekend_days': df['is_weekend'].sum(),
        }

        # Get holidays in dataset
        holidays = df[df['is_holiday']].copy()
        if not holidays.empty:
            analysis['holidays_list'] = holidays[['date', 'holiday_name']].to_dict('records')
        else:
            analysis['holidays_list'] = []

        return analysis
