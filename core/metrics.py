"""
Metrics engine for DIET_APP
Computes derived metrics, rolling averages, and body composition.
"""
from datetime import date, timedelta
from typing import Dict, List, Optional
import pandas as pd

from core.storage import Storage
from core.schemas import DailyEntry


class MetricsEngine:
    """Computes metrics from daily entries."""

    def __init__(self, storage: Storage, bmr_kcal: float = 2000.0):
        """
        Initialize metrics engine.

        Args:
            storage: Storage instance
            bmr_kcal: Basal Metabolic Rate in kcal/day (default 2000)
        """
        self.storage = storage
        self.bmr_kcal = bmr_kcal

    def get_metrics_dataframe(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get metrics as pandas DataFrame.

        Args:
            start_date: Start date filter
            end_date: End date filter
            days: Alternative to start_date - get last N days

        Returns:
            DataFrame with metrics
        """
        if days:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

        # Fetch entries
        entries = self.storage.get_all(
            start_date=start_date,
            end_date=end_date
        )

        if not entries:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for entry in entries:
            row = {
                'date': entry.date,
                'bs_weight_kg': entry.weight_kg,
                'bs_bodyfat_pct': entry.bodyfat_pct,
                'cal_in_kcal': entry.cal_in_kcal,
                'cal_out_sport_kcal': entry.cal_out_sport_kcal,
            }
            data.append(row)

        df = pd.DataFrame(data)
        df = df.sort_values('date')

        # Compute derived metrics
        df = self._compute_body_composition(df)
        df = self._compute_calorie_metrics(df, bmr_kcal=self.bmr_kcal)
        df = self._compute_rolling_averages(df)

        return df

    def _compute_body_composition(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute body composition metrics.

        Adds:
        - bs_fat_mass_kg: Fat mass in kg
        - bs_lean_mass_kg: Lean mass in kg
        """
        df = df.copy()

        # Fat mass = weight * bodyfat%
        df['bs_fat_mass_kg'] = df['bs_weight_kg'] * (df['bs_bodyfat_pct'] / 100.0)

        # Lean mass = weight - fat mass
        df['bs_lean_mass_kg'] = df['bs_weight_kg'] - df['bs_fat_mass_kg']

        return df

    def _compute_calorie_metrics(self, df: pd.DataFrame, bmr_kcal: float = 2000.0) -> pd.DataFrame:
        """
        Compute calorie-related metrics.

        Adds:
        - cal_net_kcal: Net calorie balance (in - BMR - sport)

        Args:
            bmr_kcal: Basal Metabolic Rate (default 2000 kcal/day)
        """
        df = df.copy()

        # Net calories = in - BMR - sport
        # BMR is the baseline calories burned per day
        df['cal_net_kcal'] = df['cal_in_kcal'] - bmr_kcal - df['cal_out_sport_kcal'].fillna(0)

        # Set to NaN where cal_in is missing
        df.loc[df['cal_in_kcal'].isna(), 'cal_net_kcal'] = None

        return df

    def _compute_rolling_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute rolling averages.

        Adds:
        - bs_weight_7d_avg_kg: 7-day rolling average of weight
        - bs_weight_14d_avg_kg: 14-day rolling average of weight
        - bs_weight_30d_avg_kg: 30-day rolling average of weight
        - cal_net_7d_avg_kcal: 7-day rolling average of net calories
        - cal_net_14d_avg_kcal: 14-day rolling average of net calories
        - cal_net_30d_avg_kcal: 30-day rolling average of net calories

        Note: Rolling averages require at least 70% data coverage in window.
        """
        df = df.copy()

        # Ensure sorted by date
        df = df.sort_values('date')

        # Weight rolling averages
        for window in [7, 14, 30]:
            min_periods = max(1, int(window * 0.7))  # 70% coverage required
            df[f'bs_weight_{window}d_avg_kg'] = df['bs_weight_kg'].rolling(
                window=window,
                min_periods=min_periods,
                center=False
            ).mean()

        # Calorie rolling averages (only where net calories exist)
        for window in [7, 14, 30]:
            min_periods = max(1, int(window * 0.7))
            df[f'cal_net_{window}d_avg_kcal'] = df['cal_net_kcal'].rolling(
                window=window,
                min_periods=min_periods,
                center=False
            ).mean()

        return df

    def get_summary_stats(self, days: int = 30) -> Dict:
        """
        Get summary statistics for recent period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with summary stats
        """
        df = self.get_metrics_dataframe(days=days)

        if df.empty:
            return {}

        stats = {
            'period_days': days,
            'data_coverage': len(df) / days * 100,

            # Weight stats
            'weight_current_kg': df['bs_weight_kg'].iloc[-1],
            'weight_start_kg': df['bs_weight_kg'].iloc[0],
            'weight_change_kg': df['bs_weight_kg'].iloc[-1] - df['bs_weight_kg'].iloc[0],
            'weight_avg_kg': df['bs_weight_kg'].mean(),
            'weight_min_kg': df['bs_weight_kg'].min(),
            'weight_max_kg': df['bs_weight_kg'].max(),
            'weight_std_kg': df['bs_weight_kg'].std(),

            # Body fat stats (if available)
            'bf_current_pct': df['bs_bodyfat_pct'].iloc[-1] if df['bs_bodyfat_pct'].notna().any() else None,
            'bf_avg_pct': df['bs_bodyfat_pct'].mean() if df['bs_bodyfat_pct'].notna().any() else None,

            # Fat mass stats (if available)
            'fm_current_kg': df['bs_fat_mass_kg'].iloc[-1] if df['bs_fat_mass_kg'].notna().any() else None,
            'fm_avg_kg': df['bs_fat_mass_kg'].mean() if df['bs_fat_mass_kg'].notna().any() else None,

            # Calorie stats (if available)
            'cal_net_avg_kcal': df['cal_net_kcal'].mean() if df['cal_net_kcal'].notna().any() else None,
            'cal_in_avg_kcal': df['cal_in_kcal'].mean() if df['cal_in_kcal'].notna().any() else None,
            'cal_out_sport_avg_kcal': df['cal_out_sport_kcal'].mean() if df['cal_out_sport_kcal'].notna().any() else None,
            'cal_out_bmr_kcal': self.bmr_kcal,
            'cal_out_total_avg_kcal': (self.bmr_kcal + df['cal_out_sport_kcal'].mean()) if df['cal_out_sport_kcal'].notna().any() else self.bmr_kcal,
        }

        # Add rolling average (latest values)
        if f'bs_weight_7d_avg_kg' in df.columns:
            stats['weight_7d_avg_kg'] = df['bs_weight_7d_avg_kg'].iloc[-1]
        if f'bs_weight_14d_avg_kg' in df.columns:
            stats['weight_14d_avg_kg'] = df['bs_weight_14d_avg_kg'].iloc[-1]

        return stats
