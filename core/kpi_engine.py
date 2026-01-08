"""
KPI Engine for DIET_APP
Computes Key Performance Indicators for diet and training tracking.
"""
from datetime import date, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from core.storage import Storage
from core.metrics import MetricsEngine


class KPI:
    """Represents a single KPI."""

    def __init__(
        self,
        id: str,
        name: str,
        value: Optional[float],
        unit: str,
        window_days: int,
        explanation: str,
        formula: str,
        target: Optional[float] = None,
        is_good: Optional[bool] = None
    ):
        self.id = id
        self.name = name
        self.value = value
        self.unit = unit
        self.window_days = window_days
        self.explanation = explanation
        self.formula = formula
        self.target = target
        self.is_good = is_good

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'window_days': self.window_days,
            'explanation': self.explanation,
            'formula': self.formula,
            'target': self.target,
            'is_good': self.is_good
        }


class KPIEngine:
    """Computes KPIs from daily entries."""

    def __init__(self, storage: Storage, target_weight_kg: float = 75.0, bmr_kcal: float = 2000.0):
        """
        Initialize KPI engine.

        Args:
            storage: Storage instance
            target_weight_kg: Target weight for goal calculations
            bmr_kcal: Basal Metabolic Rate in kcal/day (default 2000)
        """
        self.storage = storage
        self.metrics = MetricsEngine(storage, bmr_kcal=bmr_kcal)
        self.target_weight_kg = target_weight_kg
        self.bmr_kcal = bmr_kcal

    def compute_all_kpis(self, days: int = 30) -> List[KPI]:
        """
        Compute all KPIs.

        Args:
            days: Number of days to analyze (default 30)

        Returns:
            List of KPI objects
        """
        df = self.metrics.get_metrics_dataframe(days=days)

        if df.empty:
            return []

        kpis = [
            self._kpi_weight_trend_7d(df),
            self._kpi_weight_change_30d(df),
            self._kpi_bf_change_30d(df),
            self._kpi_fat_mass_change_30d(df),
            self._kpi_net_calories_7d(df),
            self._kpi_intake_7d(df),
            self._kpi_sport_7d(df),
            self._kpi_consistency_coverage_30d(df, days),
            self._kpi_volatility_weight_14d(df),
            self._kpi_streak_days(df),
            self._kpi_goal_eta(df),
            self._kpi_adherence_score(df, days)
        ]

        return [kpi for kpi in kpis if kpi is not None]

    def _kpi_weight_trend_7d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Weight trend (kg/week) based on 7-day average."""
        if len(df) < 7:
            return None

        # Get 7-day averages
        if 'bs_weight_7d_avg_kg' not in df.columns:
            return None

        df_with_avg = df[df['bs_weight_7d_avg_kg'].notna()].copy()
        if len(df_with_avg) < 7:
            return None

        # Linear regression on 7-day averages
        recent = df_with_avg.tail(7)
        x = np.arange(len(recent))
        y = recent['bs_weight_7d_avg_kg'].values

        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        trend_per_week = slope * 7  # Convert daily slope to weekly

        return KPI(
            id='KPI_Weight_Trend_7d',
            name='Weight Trend (7d)',
            value=round(trend_per_week, 2),
            unit='kg/week',
            window_days=7,
            explanation='Rate of weight change per week based on 7-day rolling average',
            formula='Linear regression slope on 7-day avg × 7',
            target=-0.5,  # Target: -0.5 kg/week (healthy loss)
            is_good=trend_per_week < 0  # Negative is good (losing weight)
        )

    def _kpi_weight_change_30d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Total weight change over 30 days."""
        if len(df) < 2:
            return None

        # Compare 7-day averages if available, otherwise raw weight
        if 'bs_weight_7d_avg_kg' in df.columns:
            df_with_avg = df[df['bs_weight_7d_avg_kg'].notna()]
            if len(df_with_avg) >= 2:
                change = df_with_avg['bs_weight_7d_avg_kg'].iloc[-1] - df_with_avg['bs_weight_7d_avg_kg'].iloc[0]
            else:
                change = df['bs_weight_kg'].iloc[-1] - df['bs_weight_kg'].iloc[0]
        else:
            change = df['bs_weight_kg'].iloc[-1] - df['bs_weight_kg'].iloc[0]

        return KPI(
            id='KPI_Weight_Change_30d',
            name='Weight Change (30d)',
            value=round(change, 2),
            unit='kg',
            window_days=30,
            explanation='Total weight change over the period',
            formula='Latest 7d avg - First 7d avg',
            target=-2.0,  # Target: -2 kg/month
            is_good=change < 0
        )

    def _kpi_bf_change_30d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Body fat % change over 30 days."""
        bf_data = df[df['bs_bodyfat_pct'].notna()]
        if len(bf_data) < 2:
            return None

        change = bf_data['bs_bodyfat_pct'].iloc[-1] - bf_data['bs_bodyfat_pct'].iloc[0]

        return KPI(
            id='KPI_BF_Change_30d',
            name='Body Fat Change (30d)',
            value=round(change, 2),
            unit='pp',
            window_days=30,
            explanation='Change in body fat percentage over the period',
            formula='Latest BF% - First BF%',
            target=-1.0,  # Target: -1 pp/month
            is_good=change < 0
        )

    def _kpi_fat_mass_change_30d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Fat mass change over 30 days."""
        fm_data = df[df['bs_fat_mass_kg'].notna()]
        if len(fm_data) < 2:
            return None

        change = fm_data['bs_fat_mass_kg'].iloc[-1] - fm_data['bs_fat_mass_kg'].iloc[0]

        return KPI(
            id='KPI_FatMass_Change_30d',
            name='Fat Mass Change (30d)',
            value=round(change, 2),
            unit='kg',
            window_days=30,
            explanation='Change in fat mass over the period',
            formula='Latest fat mass - First fat mass',
            target=-1.5,  # Target: -1.5 kg fat/month
            is_good=change < 0
        )

    def _kpi_net_calories_7d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Average net calories over 7 days."""
        cal_data = df[df['cal_net_kcal'].notna()]
        if len(cal_data) < 1:
            return None

        recent = cal_data.tail(7)
        avg_net = recent['cal_net_kcal'].mean()

        return KPI(
            id='KPI_NetCalories_7d',
            name='Avg NET Calories (7d)',
            value=round(avg_net, 0),
            unit='kcal/day',
            window_days=7,
            explanation=f'Average daily net calorie balance (IN - BMR[{self.bmr_kcal}] - SPORT)',
            formula=f'Mean of (cal_in - {self.bmr_kcal} - cal_out_sport) over 7 days',
            target=-300,  # Target: -300 kcal/day deficit
            is_good=avg_net < 0  # Negative is good (deficit)
        )

    def _kpi_intake_7d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Average calorie intake over 7 days."""
        cal_data = df[df['cal_in_kcal'].notna()]
        if len(cal_data) < 1:
            return None

        recent = cal_data.tail(7)
        avg_in = recent['cal_in_kcal'].mean()

        return KPI(
            id='KPI_Intake_7d',
            name='Avg Intake (7d)',
            value=round(avg_in, 0),
            unit='kcal/day',
            window_days=7,
            explanation='Average daily calorie intake',
            formula='Mean of cal_in over 7 days',
            target=2000,  # Example target
            is_good=None  # Neutral
        )

    def _kpi_sport_7d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Average sport calories over 7 days."""
        cal_data = df[df['cal_out_sport_kcal'].notna()]
        if len(cal_data) < 1:
            return None

        recent = cal_data.tail(7)
        avg_sport = recent['cal_out_sport_kcal'].mean()

        return KPI(
            id='KPI_Sport_7d',
            name='Avg Sport (7d)',
            value=round(avg_sport, 0),
            unit='kcal/day',
            window_days=7,
            explanation='Average daily calories burned through exercise',
            formula='Mean of cal_out_sport over 7 days',
            target=400,  # Example target
            is_good=avg_sport >= 300  # Good if >= 300 kcal/day
        )

    def _kpi_consistency_coverage_30d(self, df: pd.DataFrame, days: int) -> Optional[KPI]:
        """KPI: Data consistency (% of days with complete data)."""
        # Complete data = has weight + calories
        complete = df[df['cal_in_kcal'].notna() & df['cal_out_sport_kcal'].notna()]

        coverage = (len(complete) / days) * 100

        return KPI(
            id='KPI_Consistency_Coverage_30d',
            name='Data Coverage (30d)',
            value=round(coverage, 1),
            unit='%',
            window_days=days,
            explanation='Percentage of days with complete data (weight + calories)',
            formula='(Days with complete data / Total days) × 100',
            target=90.0,  # Target: 90% coverage
            is_good=coverage >= 80  # Good if >= 80%
        )

    def _kpi_volatility_weight_14d(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Weight volatility (standard deviation over 14 days)."""
        if len(df) < 14:
            return None

        recent = df.tail(14)
        std = recent['bs_weight_kg'].std()

        return KPI(
            id='KPI_Volatility_Weight_14d',
            name='Weight Volatility (14d)',
            value=round(std, 2),
            unit='kg (std)',
            window_days=14,
            explanation='Standard deviation of weight over 14 days (measures fluctuation/water retention)',
            formula='Std dev of weight over 14 days',
            target=0.5,  # Target: low volatility
            is_good=std < 1.0  # Good if std < 1 kg
        )

    def _kpi_streak_days(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Current streak of consecutive days with data."""
        if len(df) < 1:
            return None

        # Sort by date descending
        df_sorted = df.sort_values('date', ascending=False)

        # Count consecutive days from most recent
        streak = 0
        prev_date = None

        for idx, row in df_sorted.iterrows():
            current_date = row['date']

            if prev_date is None:
                # First entry
                streak = 1
                prev_date = current_date
            else:
                # Check if consecutive (1 day difference)
                diff = (prev_date - current_date).days
                if diff == 1:
                    streak += 1
                    prev_date = current_date
                else:
                    # Streak broken
                    break

        return KPI(
            id='KPI_Streak_Days',
            name='Current Streak',
            value=streak,
            unit='days',
            window_days=365,  # Can be any length
            explanation='Number of consecutive days with data entries',
            formula='Count of consecutive days from most recent',
            target=30,  # Target: 30-day streak
            is_good=streak >= 7  # Good if >= 7 days
        )

    def _kpi_goal_eta(self, df: pd.DataFrame) -> Optional[KPI]:
        """KPI: Estimated days to reach target weight."""
        if len(df) < 14:
            return None

        # Get current weight (7d avg if available)
        if 'bs_weight_7d_avg_kg' in df.columns:
            df_with_avg = df[df['bs_weight_7d_avg_kg'].notna()]
            if len(df_with_avg) > 0:
                current_weight = df_with_avg['bs_weight_7d_avg_kg'].iloc[-1]
            else:
                current_weight = df['bs_weight_kg'].iloc[-1]
        else:
            current_weight = df['bs_weight_kg'].iloc[-1]

        # Calculate trend (kg/day)
        recent = df.tail(14)
        x = np.arange(len(recent))
        y = recent['bs_weight_kg'].values
        slope = np.polyfit(x, y, 1)[0]  # kg/day

        if slope >= 0:
            # Not losing weight
            return KPI(
                id='KPI_Goal_ETA',
                name='Goal ETA',
                value=None,
                unit='days',
                window_days=14,
                explanation='Estimated days to reach target weight (not losing)',
                formula='(Current - Target) / Trend',
                target=None,
                is_good=False
            )

        # Calculate ETA
        weight_to_lose = current_weight - self.target_weight_kg
        eta_days = weight_to_lose / abs(slope)

        return KPI(
            id='KPI_Goal_ETA',
            name='Goal ETA',
            value=round(eta_days, 0),
            unit='days',
            window_days=14,
            explanation=f'Estimated days to reach {self.target_weight_kg} kg at current rate',
            formula='(Current weight - Target) / |Trend slope|',
            target=90,  # Target: 3 months
            is_good=eta_days <= 120  # Good if <= 4 months
        )

    def _kpi_adherence_score(self, df: pd.DataFrame, days: int) -> Optional[KPI]:
        """KPI: Overall adherence score (heuristic 0-100)."""
        if len(df) < 7:
            return None

        score = 100.0

        # Coverage penalty (max -30 points)
        complete = df[df['cal_in_kcal'].notna() & df['cal_out_sport_kcal'].notna()]
        coverage = (len(complete) / days) * 100
        if coverage < 90:
            score -= (90 - coverage) / 3  # Lose 10 points per 30% below 90%

        # Trend penalty (max -30 points)
        if 'bs_weight_7d_avg_kg' in df.columns:
            df_with_avg = df[df['bs_weight_7d_avg_kg'].notna()]
            if len(df_with_avg) >= 7:
                recent = df_with_avg.tail(7)
                x = np.arange(len(recent))
                y = recent['bs_weight_7d_avg_kg'].values
                slope = np.polyfit(x, y, 1)[0] * 7  # kg/week

                if slope > 0:  # Gaining weight
                    score -= 30
                elif slope > -0.2:  # Losing too slowly
                    score -= 15

        # Consistency penalty (max -20 points)
        streak_kpi = self._kpi_streak_days(df)
        if streak_kpi and streak_kpi.value < 7:
            score -= (7 - streak_kpi.value) * 3

        # Volatility penalty (max -20 points)
        if len(df) >= 14:
            std = df.tail(14)['bs_weight_kg'].std()
            if std > 1.5:
                score -= min(20, (std - 1.5) * 10)

        score = max(0, min(100, score))

        return KPI(
            id='KPI_Adherence_Score',
            name='Adherence Score',
            value=round(score, 0),
            unit='points (0-100)',
            window_days=days,
            explanation='Overall adherence score based on coverage, trend, consistency, and volatility',
            formula='100 - penalties (coverage, trend, streak, volatility)',
            target=80,  # Target: 80+ points
            is_good=score >= 70  # Good if >= 70
        )
