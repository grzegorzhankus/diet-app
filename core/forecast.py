"""
Forecast Engine for DIET_APP
Predictive analytics for weight loss trajectory based on current trends.
"""
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np

from core.storage import Storage
from core.metrics import MetricsEngine


@dataclass
class Forecast:
    """Represents a forecast prediction."""
    date: date
    predicted_weight_kg: float
    confidence_lower_kg: float  # Lower bound of confidence interval
    confidence_upper_kg: float  # Upper bound of confidence interval
    method: str  # 'linear', 'exponential', 'calorie_based'

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'date': self.date.isoformat(),
            'predicted_weight_kg': self.predicted_weight_kg,
            'confidence_lower_kg': self.confidence_lower_kg,
            'confidence_upper_kg': self.confidence_upper_kg,
            'method': self.method
        }


@dataclass
class ForecastSummary:
    """Summary of forecast predictions."""
    horizon_days: int
    start_weight_kg: float
    end_weight_kg: float
    total_change_kg: float
    avg_rate_kg_per_week: float
    target_weight_kg: Optional[float]
    target_date: Optional[date]
    confidence_level: float  # 0.0 to 1.0
    method: str

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'horizon_days': self.horizon_days,
            'start_weight_kg': self.start_weight_kg,
            'end_weight_kg': self.end_weight_kg,
            'total_change_kg': self.total_change_kg,
            'avg_rate_kg_per_week': self.avg_rate_kg_per_week,
            'target_weight_kg': self.target_weight_kg,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'confidence_level': self.confidence_level,
            'method': self.method
        }


class ForecastEngine:
    """Generates weight loss forecasts based on historical data."""

    def __init__(self, storage: Storage, bmr_kcal: float = 2000.0):
        """
        Initialize forecast engine.

        Args:
            storage: Storage instance
            bmr_kcal: Basal Metabolic Rate in kcal/day
        """
        self.storage = storage
        self.metrics = MetricsEngine(storage, bmr_kcal=bmr_kcal)
        self.bmr_kcal = bmr_kcal

        # Constants
        self.KCAL_PER_KG_FAT = 7700.0  # Calories in 1 kg of body fat

    def generate_forecast(
        self,
        horizon_days: int,
        lookback_days: int = 30,
        target_weight_kg: Optional[float] = None,
        method: str = 'auto'
    ) -> Tuple[List[Forecast], ForecastSummary]:
        """
        Generate weight forecast.

        Args:
            horizon_days: Number of days to forecast into future
            lookback_days: Number of historical days to use for trend
            target_weight_kg: Optional target weight for goal date calculation
            method: Forecast method ('auto', 'linear', 'calorie_based')

        Returns:
            Tuple of (forecast list, summary)
        """
        # Get historical data
        df = self.metrics.get_metrics_dataframe(days=lookback_days)

        if df.empty or len(df) < 7:
            raise ValueError("Insufficient data for forecasting (need at least 7 days)")

        # Choose method
        if method == 'auto':
            # Use calorie-based if we have calorie data, otherwise linear
            has_calories = df['cal_net_kcal'].notna().sum() >= lookback_days * 0.5
            method = 'calorie_based' if has_calories else 'linear'

        # Generate forecast based on method
        if method == 'calorie_based':
            forecasts, summary = self._forecast_calorie_based(
                df, horizon_days, target_weight_kg
            )
        else:  # linear
            forecasts, summary = self._forecast_linear(
                df, horizon_days, target_weight_kg
            )

        return forecasts, summary

    def _forecast_linear(
        self,
        df: pd.DataFrame,
        horizon_days: int,
        target_weight_kg: Optional[float]
    ) -> Tuple[List[Forecast], ForecastSummary]:
        """
        Linear regression forecast based on recent weight trend.
        """
        # Try to use 7-day rolling average if available and has enough data
        if 'bs_weight_7d_avg_kg' in df.columns:
            df_with_avg = df[df['bs_weight_7d_avg_kg'].notna()].copy()
            if len(df_with_avg) >= 7:
                weight_col = 'bs_weight_7d_avg_kg'
                df_trend = df_with_avg
            else:
                # Fall back to raw weight
                weight_col = 'bs_weight_kg'
                df_trend = df.copy()
        else:
            weight_col = 'bs_weight_kg'
            df_trend = df.copy()

        if len(df_trend) < 7:
            raise ValueError("Insufficient data for trend analysis")

        # Convert dates to days since start
        df_trend = df_trend.sort_values('date')
        # Ensure date is datetime
        df_trend['date'] = pd.to_datetime(df_trend['date'])
        df_trend['days_since_start'] = (df_trend['date'] - df_trend['date'].iloc[0]).dt.days

        # Linear regression
        X = df_trend['days_since_start'].values
        y = df_trend[weight_col].values

        # Calculate slope and intercept
        n = len(X)
        slope = (n * np.sum(X * y) - np.sum(X) * np.sum(y)) / (n * np.sum(X**2) - np.sum(X)**2)
        intercept = (np.sum(y) - slope * np.sum(X)) / n

        # Calculate residual standard error for confidence intervals
        y_pred = slope * X + intercept
        residuals = y - y_pred
        std_error = np.sqrt(np.sum(residuals**2) / (n - 2))

        # Current weight (last observation)
        last_date = df_trend['date'].iloc[-1]
        last_weight = df_trend[weight_col].iloc[-1]
        last_day = df_trend['days_since_start'].iloc[-1]

        # Generate forecasts
        forecasts = []
        for i in range(1, horizon_days + 1):
            forecast_day = last_day + i
            forecast_date = last_date + timedelta(days=i)

            # Predicted weight
            predicted_weight = slope * forecast_day + intercept

            # Confidence interval (95%) - widens with distance from data
            # Standard error increases with distance from mean
            mean_x = np.mean(X)
            se_forecast = std_error * np.sqrt(1 + 1/n + (forecast_day - mean_x)**2 / np.sum((X - mean_x)**2))

            # 95% confidence interval (approximately 2 standard errors)
            confidence_lower = predicted_weight - 2 * se_forecast
            confidence_upper = predicted_weight + 2 * se_forecast

            forecasts.append(Forecast(
                date=forecast_date,
                predicted_weight_kg=predicted_weight,
                confidence_lower_kg=confidence_lower,
                confidence_upper_kg=confidence_upper,
                method='linear'
            ))

        # Calculate summary
        end_weight = forecasts[-1].predicted_weight_kg
        total_change = end_weight - last_weight
        avg_rate_per_week = (slope * 7)  # slope is per day, convert to per week

        # Calculate confidence level based on R²
        ss_tot = np.sum((y - np.mean(y))**2)
        ss_res = np.sum(residuals**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence_level = max(0.0, min(1.0, r_squared))

        # Estimate target date if provided
        target_date = None
        if target_weight_kg and slope != 0:
            days_to_target = (target_weight_kg - last_weight) / slope
            if 0 < days_to_target <= 365:  # Only if reasonable
                target_date = last_date + timedelta(days=int(days_to_target))

        summary = ForecastSummary(
            horizon_days=horizon_days,
            start_weight_kg=last_weight,
            end_weight_kg=end_weight,
            total_change_kg=total_change,
            avg_rate_kg_per_week=avg_rate_per_week,
            target_weight_kg=target_weight_kg,
            target_date=target_date,
            confidence_level=confidence_level,
            method='linear'
        )

        return forecasts, summary

    def _forecast_calorie_based(
        self,
        df: pd.DataFrame,
        horizon_days: int,
        target_weight_kg: Optional[float]
    ) -> Tuple[List[Forecast], ForecastSummary]:
        """
        Forecast based on average calorie deficit/surplus.
        More accurate than linear when calorie data is available.
        """
        # Get recent calorie data
        cal_data = df[df['cal_net_kcal'].notna()].copy()

        if len(cal_data) < 7:
            # Fall back to linear if not enough calorie data
            return self._forecast_linear(df, horizon_days, target_weight_kg)

        # Calculate average net calorie balance
        avg_net_kcal = cal_data['cal_net_kcal'].mean()

        # Current weight
        last_date = df['date'].iloc[-1]
        last_weight = df['bs_weight_kg'].iloc[-1]

        # Calculate expected weight change per day based on calories
        # 1 kg fat = 7700 kcal
        # Daily weight change = net_calories / 7700
        daily_weight_change_kg = avg_net_kcal / self.KCAL_PER_KG_FAT

        # Calculate variability for confidence intervals
        cal_std = cal_data['cal_net_kcal'].std()
        weight_std = df['bs_weight_kg'].std()

        # Generate forecasts
        forecasts = []
        current_weight = last_weight

        for i in range(1, horizon_days + 1):
            forecast_date = last_date + timedelta(days=i)

            # Predicted weight based on calorie deficit
            predicted_weight = last_weight + (daily_weight_change_kg * i)

            # Confidence interval based on calorie and weight variability
            # Uncertainty increases with forecast horizon
            days_factor = np.sqrt(i / 7.0)  # Increases with square root of weeks
            uncertainty = (weight_std * 0.5 + (cal_std / self.KCAL_PER_KG_FAT) * i * 0.5) * days_factor

            confidence_lower = predicted_weight - 2 * uncertainty
            confidence_upper = predicted_weight + 2 * uncertainty

            forecasts.append(Forecast(
                date=forecast_date,
                predicted_weight_kg=predicted_weight,
                confidence_lower_kg=confidence_lower,
                confidence_upper_kg=confidence_upper,
                method='calorie_based'
            ))

        # Calculate summary
        end_weight = forecasts[-1].predicted_weight_kg
        total_change = end_weight - last_weight
        avg_rate_per_week = daily_weight_change_kg * 7

        # Confidence level based on consistency of calorie tracking
        cal_coverage = len(cal_data) / len(df)
        cal_consistency = 1.0 - (cal_std / abs(avg_net_kcal)) if avg_net_kcal != 0 else 0.5
        confidence_level = max(0.0, min(1.0, cal_coverage * cal_consistency))

        # Estimate target date if provided
        target_date = None
        if target_weight_kg and daily_weight_change_kg != 0:
            days_to_target = (target_weight_kg - last_weight) / daily_weight_change_kg
            if 0 < days_to_target <= 365:
                target_date = last_date + timedelta(days=int(days_to_target))

        summary = ForecastSummary(
            horizon_days=horizon_days,
            start_weight_kg=last_weight,
            end_weight_kg=end_weight,
            total_change_kg=total_change,
            avg_rate_kg_per_week=avg_rate_per_week,
            target_weight_kg=target_weight_kg,
            target_date=target_date,
            confidence_level=confidence_level,
            method='calorie_based'
        )

        return forecasts, summary

    def calculate_target_calories(
        self,
        target_weight_kg: float,
        target_days: int,
        current_weight_kg: float,
        avg_sport_kcal: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate required daily calories to reach target weight.

        Args:
            target_weight_kg: Goal weight
            target_days: Days to reach goal
            current_weight_kg: Current weight
            avg_sport_kcal: Average daily sport calories burned

        Returns:
            Dictionary with calorie recommendations
        """
        # Calculate required weight change
        weight_change_kg = target_weight_kg - current_weight_kg

        # Total calorie deficit/surplus needed
        total_kcal_needed = weight_change_kg * self.KCAL_PER_KG_FAT

        # Daily calorie deficit/surplus needed
        daily_net_kcal_needed = total_kcal_needed / target_days

        # Calculate required intake
        # NET = INTAKE - BMR - SPORT
        # INTAKE = NET + BMR + SPORT
        required_intake_kcal = daily_net_kcal_needed + self.bmr_kcal + avg_sport_kcal

        # Calculate rate
        weekly_rate_kg = (weight_change_kg / target_days) * 7

        return {
            'required_intake_kcal': required_intake_kcal,
            'daily_net_kcal': daily_net_kcal_needed,
            'weekly_rate_kg': weekly_rate_kg,
            'total_change_kg': weight_change_kg,
            'is_healthy': abs(weekly_rate_kg) <= 1.0  # Healthy rate: ≤1kg per week
        }
