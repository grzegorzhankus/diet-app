"""
Pattern Detection Engine for DIET_APP
Identifies behavioral patterns in diet and training data.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from scipy import stats

from core.storage import Storage
from core.ml.temporal_features import TemporalFeatureEngine


class PatternDetectionEngine:
    """
    Detects patterns in diet and training behavior.
    Focus: weekend vs weekday, holidays, day-of-week effects.
    """

    def __init__(self, storage: Storage):
        """
        Initialize pattern detection engine.

        Args:
            storage: Data storage instance
        """
        self.storage = storage
        self.temporal = TemporalFeatureEngine()

    def _get_enriched_data(self, days: int = 90) -> pd.DataFrame:
        """
        Get data enriched with temporal features.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame with temporal features
        """
        # Get data from storage
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        entries = self.storage.get_all(start_date=start_date, end_date=end_date)

        if not entries:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for entry in entries:
            data.append({
                'date': entry.date,
                'weight_kg': entry.weight_kg,
                'bodyfat_pct': entry.bodyfat_pct,
                'cal_in_kcal': entry.cal_in_kcal,
                'cal_out_sport_kcal': entry.cal_out_sport_kcal,
                'notes': entry.notes
            })

        df = pd.DataFrame(data)

        # Add temporal features
        df = self.temporal.add_temporal_features(df)

        # Calculate net calories
        df['cal_net_kcal'] = df['cal_in_kcal'] - df['cal_out_sport_kcal'].fillna(0)

        return df

    def detect_weekend_pattern(self, days: int = 90) -> Dict:
        """
        Detect weekend vs weekday patterns.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with pattern analysis
        """
        df = self._get_enriched_data(days)

        if df.empty or len(df) < 14:
            return {'detected': False, 'reason': 'Insufficient data'}

        # Separate weekend and weekday data
        weekend_data = df[df['is_weekend']]
        weekday_data = df[df['is_workweek'] & ~df['is_holiday']]

        if len(weekend_data) < 4 or len(weekday_data) < 10:
            return {'detected': False, 'reason': 'Insufficient weekend or weekday data'}

        result = {
            'detected': True,
            'period_days': days,
            'weekend_days': len(weekend_data),
            'weekday_days': len(weekday_data),
        }

        # Analyze calorie intake
        if 'cal_in_kcal' in df.columns:
            weekend_cal = weekend_data['cal_in_kcal'].dropna()
            weekday_cal = weekday_data['cal_in_kcal'].dropna()

            if len(weekend_cal) > 0 and len(weekday_cal) > 0:
                result['calories'] = {
                    'weekend_avg': float(weekend_cal.mean()),
                    'weekday_avg': float(weekday_cal.mean()),
                    'difference': float(weekend_cal.mean() - weekday_cal.mean()),
                    'difference_pct': float((weekend_cal.mean() - weekday_cal.mean()) / weekday_cal.mean() * 100),
                    'weekend_std': float(weekend_cal.std()),
                    'weekday_std': float(weekday_cal.std()),
                }

                # Statistical test
                if len(weekend_cal) >= 3 and len(weekday_cal) >= 3:
                    t_stat, p_value = stats.ttest_ind(weekend_cal, weekday_cal)
                    result['calories']['statistical_test'] = {
                        't_statistic': float(t_stat),
                        'p_value': float(p_value),
                        'significant': p_value < 0.05
                    }

        # Analyze exercise
        if 'cal_out_sport_kcal' in df.columns:
            weekend_sport = weekend_data['cal_out_sport_kcal'].fillna(0)
            weekday_sport = weekday_data['cal_out_sport_kcal'].fillna(0)

            result['exercise'] = {
                'weekend_avg': float(weekend_sport.mean()),
                'weekday_avg': float(weekday_sport.mean()),
                'difference': float(weekend_sport.mean() - weekday_sport.mean()),
                'weekend_std': float(weekend_sport.std()),
                'weekday_std': float(weekday_sport.std()),
            }

        # Analyze NET balance
        if 'cal_net_kcal' in df.columns:
            weekend_net = weekend_data['cal_net_kcal'].dropna()
            weekday_net = weekday_data['cal_net_kcal'].dropna()

            if len(weekend_net) > 0 and len(weekday_net) > 0:
                result['net_balance'] = {
                    'weekend_avg': float(weekend_net.mean()),
                    'weekday_avg': float(weekday_net.mean()),
                    'difference': float(weekend_net.mean() - weekday_net.mean()),
                    'weekend_std': float(weekend_net.std()),
                    'weekday_std': float(weekday_net.std()),
                }

        # Pattern summary
        result['pattern_summary'] = self._generate_weekend_summary(result)

        return result

    def _generate_weekend_summary(self, analysis: Dict) -> str:
        """Generate human-readable summary of weekend pattern."""
        if not analysis.get('detected'):
            return "No pattern detected."

        summary_parts = []

        if 'calories' in analysis:
            cal_data = analysis['calories']
            diff = cal_data['difference']
            diff_pct = cal_data['difference_pct']

            if abs(diff) > 100:  # Meaningful difference
                direction = "higher" if diff > 0 else "lower"
                summary_parts.append(
                    f"Weekend calorie intake is {abs(diff):.0f} kcal ({abs(diff_pct):.1f}%) {direction} than weekdays"
                )

                if cal_data.get('statistical_test', {}).get('significant'):
                    summary_parts.append("(statistically significant)")

        if 'exercise' in analysis:
            sport_data = analysis['exercise']
            diff = sport_data['difference']

            if abs(diff) > 50:
                direction = "more" if diff > 0 else "less"
                summary_parts.append(
                    f"Weekend exercise is {abs(diff):.0f} kcal {direction} than weekdays"
                )

        if not summary_parts:
            return "No significant weekend vs weekday differences detected."

        return ". ".join(summary_parts) + "."

    def detect_holiday_pattern(self, days: int = 180) -> Dict:
        """
        Detect patterns around Polish holidays.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with holiday pattern analysis
        """
        df = self._get_enriched_data(days)

        if df.empty:
            return {'detected': False, 'reason': 'No data'}

        holiday_days = df[df['is_holiday']]
        non_holiday_days = df[~df['is_holiday'] & ~df['is_long_weekend']]

        if len(holiday_days) < 2:
            return {'detected': False, 'reason': 'Insufficient holiday data'}

        result = {
            'detected': True,
            'period_days': days,
            'holiday_days_count': len(holiday_days),
            'non_holiday_days_count': len(non_holiday_days),
            'holidays_observed': holiday_days['holiday_name'].dropna().unique().tolist()
        }

        # Analyze calorie patterns
        if 'cal_in_kcal' in df.columns:
            holiday_cal = holiday_days['cal_in_kcal'].dropna()
            normal_cal = non_holiday_days['cal_in_kcal'].dropna()

            if len(holiday_cal) > 0 and len(normal_cal) > 0:
                result['calories'] = {
                    'holiday_avg': float(holiday_cal.mean()),
                    'normal_avg': float(normal_cal.mean()),
                    'difference': float(holiday_cal.mean() - normal_cal.mean()),
                    'difference_pct': float((holiday_cal.mean() - normal_cal.mean()) / normal_cal.mean() * 100),
                }

        # Long weekend analysis
        long_weekend_days = df[df['is_long_weekend']]
        if len(long_weekend_days) >= 2 and 'cal_in_kcal' in df.columns:
            lw_cal = long_weekend_days['cal_in_kcal'].dropna()
            if len(lw_cal) > 0:
                result['long_weekends'] = {
                    'days_count': len(long_weekend_days),
                    'avg_calories': float(lw_cal.mean())
                }

        result['pattern_summary'] = self._generate_holiday_summary(result)

        return result

    def _generate_holiday_summary(self, analysis: Dict) -> str:
        """Generate human-readable summary of holiday pattern."""
        if not analysis.get('detected'):
            return "No pattern detected."

        summary_parts = []

        if 'calories' in analysis:
            cal_data = analysis['calories']
            diff = cal_data['difference']
            diff_pct = cal_data['difference_pct']

            if abs(diff) > 100:
                direction = "higher" if diff > 0 else "lower"
                summary_parts.append(
                    f"Holiday calorie intake is {abs(diff):.0f} kcal ({abs(diff_pct):.1f}%) {direction} than normal days"
                )

        if 'long_weekends' in analysis:
            lw_data = analysis['long_weekends']
            summary_parts.append(
                f"Long weekends: {lw_data['days_count']} days observed, avg {lw_data['avg_calories']:.0f} kcal"
            )

        if not summary_parts:
            return "No significant holiday patterns detected."

        return ". ".join(summary_parts) + "."

    def detect_day_of_week_pattern(self, days: int = 90) -> Dict:
        """
        Analyze patterns by day of week.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with day-of-week analysis
        """
        df = self._get_enriched_data(days)

        if df.empty or len(df) < 21:  # Need at least 3 weeks
            return {'detected': False, 'reason': 'Insufficient data'}

        result = {
            'detected': True,
            'period_days': days,
            'days_by_dow': {}
        }

        # Analyze by day of week
        for dow in range(7):
            day_data = df[df['day_of_week'] == dow]
            if len(day_data) < 2:
                continue

            day_name = self.temporal.POLISH_DAYS[dow]
            day_stats = {
                'day_name': day_name,
                'day_name_en': day_data['day_name_en'].iloc[0] if not day_data.empty else '',
                'count': len(day_data)
            }

            # Calorie stats
            if 'cal_in_kcal' in day_data.columns:
                cal_data = day_data['cal_in_kcal'].dropna()
                if len(cal_data) > 0:
                    day_stats['calories'] = {
                        'mean': float(cal_data.mean()),
                        'std': float(cal_data.std()),
                        'min': float(cal_data.min()),
                        'max': float(cal_data.max())
                    }

            # Exercise stats
            if 'cal_out_sport_kcal' in day_data.columns:
                sport_data = day_data['cal_out_sport_kcal'].fillna(0)
                day_stats['exercise'] = {
                    'mean': float(sport_data.mean()),
                    'std': float(sport_data.std())
                }

            result['days_by_dow'][dow] = day_stats

        # Find best and worst days
        if all('calories' in v for v in result['days_by_dow'].values()):
            cal_means = {k: v['calories']['mean'] for k, v in result['days_by_dow'].items()}
            best_day = min(cal_means, key=cal_means.get)
            worst_day = max(cal_means, key=cal_means.get)

            result['best_day'] = {
                'dow': best_day,
                'name': self.temporal.POLISH_DAYS[best_day],
                'avg_calories': cal_means[best_day]
            }
            result['worst_day'] = {
                'dow': worst_day,
                'name': self.temporal.POLISH_DAYS[worst_day],
                'avg_calories': cal_means[worst_day]
            }

        result['pattern_summary'] = self._generate_dow_summary(result)

        return result

    def _generate_dow_summary(self, analysis: Dict) -> str:
        """Generate human-readable summary of day-of-week pattern."""
        if not analysis.get('detected'):
            return "No pattern detected."

        summary_parts = []

        if 'best_day' in analysis and 'worst_day' in analysis:
            best = analysis['best_day']
            worst = analysis['worst_day']
            diff = worst['avg_calories'] - best['avg_calories']

            summary_parts.append(
                f"Best day: {best['name']} ({best['avg_calories']:.0f} kcal avg)"
            )
            summary_parts.append(
                f"Worst day: {worst['name']} ({worst['avg_calories']:.0f} kcal avg)"
            )
            summary_parts.append(
                f"Difference: {diff:.0f} kcal"
            )

        if not summary_parts:
            return "Insufficient data for day-of-week analysis."

        return ". ".join(summary_parts) + "."

    def get_comprehensive_analysis(self, days: int = 90) -> Dict:
        """
        Get comprehensive pattern analysis.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with all pattern analyses
        """
        return {
            'weekend_pattern': self.detect_weekend_pattern(days=days),
            'holiday_pattern': self.detect_holiday_pattern(days=min(days * 2, 180)),
            'day_of_week_pattern': self.detect_day_of_week_pattern(days=days),
            'temporal_summary': self._get_temporal_summary(days=days)
        }

    def _get_temporal_summary(self, days: int) -> Dict:
        """Get overall temporal summary."""
        df = self._get_enriched_data(days)

        if df.empty:
            return {}

        return {
            'total_days': len(df),
            'weekend_days': int(df['is_weekend'].sum()),
            'weekday_days': int(df['is_workweek'].sum()),
            'holiday_days': int(df['is_holiday'].sum()),
            'long_weekend_days': int(df['is_long_weekend'].sum()),
            'coverage_pct': min(len(df) / days * 100, 100.0) if days > 0 else 0
        }
