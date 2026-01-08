"""
Red Flags Engine for DIET_APP
Detects anomalies, inconsistencies, and potential issues in tracking data.
"""
from datetime import date, timedelta
from typing import List, Optional
from dataclasses import dataclass
import pandas as pd

from core.storage import Storage
from core.metrics import MetricsEngine


@dataclass
class RedFlag:
    """Represents a red flag (anomaly/warning)."""
    id: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'data_quality', 'health', 'consistency', 'progress'
    title: str
    description: str
    dates_affected: List[date]
    value: Optional[float] = None
    threshold: Optional[float] = None
    recommendation: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'severity': self.severity,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'dates_affected': [d.isoformat() for d in self.dates_affected],
            'value': self.value,
            'threshold': self.threshold,
            'recommendation': self.recommendation
        }


class RedFlagsEngine:
    """Detects red flags in diet tracking data."""

    def __init__(self, storage: Storage, bmr_kcal: float = 2000.0):
        """
        Initialize red flags engine.

        Args:
            storage: Storage instance
            bmr_kcal: Basal Metabolic Rate in kcal/day (default 2000)
        """
        self.storage = storage
        self.metrics = MetricsEngine(storage, bmr_kcal=bmr_kcal)
        self.bmr_kcal = bmr_kcal

    def detect_all_flags(self, days: int = 30) -> List[RedFlag]:
        """
        Detect all red flags in the data.

        Args:
            days: Number of days to analyze (default 30)

        Returns:
            List of detected red flags
        """
        df = self.metrics.get_metrics_dataframe(days=days)

        if df.empty:
            return []

        flags = []

        # Data quality flags
        flags.extend(self._detect_missing_data(df, days))
        flags.extend(self._detect_inconsistent_tracking(df))
        flags.extend(self._detect_duplicate_patterns(df))

        # Health flags
        flags.extend(self._detect_extreme_weight_changes(df))
        flags.extend(self._detect_extreme_calorie_deficit(df))
        flags.extend(self._detect_extreme_calorie_surplus(df))
        flags.extend(self._detect_low_calorie_intake(df))
        flags.extend(self._detect_rapid_fat_loss(df))

        # Consistency flags
        flags.extend(self._detect_weight_plateaus(df))
        flags.extend(self._detect_yo_yo_pattern(df))
        flags.extend(self._detect_inconsistent_bodyfat(df))

        # Progress flags
        flags.extend(self._detect_stalled_progress(df))
        flags.extend(self._detect_unexpected_weight_gain(df))

        return flags

    def _detect_missing_data(self, df: pd.DataFrame, days: int) -> List[RedFlag]:
        """Detect significant gaps in data."""
        flags = []

        # Calculate data coverage
        coverage = len(df) / days * 100

        if coverage < 50:
            flags.append(RedFlag(
                id='RF_MissingData_Low',
                severity='high',
                category='data_quality',
                title='Low Data Coverage',
                description=f'Only {coverage:.1f}% of days have data in the last {days} days. Consistent tracking is essential for accurate analysis.',
                dates_affected=[],
                value=coverage,
                threshold=50.0,
                recommendation='Try to log your weight daily or at least 5 days per week for reliable trends.'
            ))
        elif coverage < 70:
            flags.append(RedFlag(
                id='RF_MissingData_Medium',
                severity='medium',
                category='data_quality',
                title='Moderate Data Coverage',
                description=f'Only {coverage:.1f}% of days have data. More consistent tracking would improve accuracy.',
                dates_affected=[],
                value=coverage,
                threshold=70.0,
                recommendation='Aim for at least 5 days of tracking per week.'
            ))

        # Check for long gaps
        df_sorted = df.sort_values('date')
        if len(df_sorted) > 1:
            df_sorted['gap'] = df_sorted['date'].diff().dt.days
            max_gap = df_sorted['gap'].max()

            if max_gap > 7:
                gap_idx = df_sorted['gap'].idxmax()
                gap_date = df_sorted.loc[gap_idx, 'date']
                flags.append(RedFlag(
                    id='RF_LongGap',
                    severity='medium',
                    category='data_quality',
                    title=f'{int(max_gap)}-Day Gap in Tracking',
                    description=f'Found a {int(max_gap)}-day gap in tracking around {gap_date.strftime("%Y-%m-%d")}.',
                    dates_affected=[gap_date],
                    value=max_gap,
                    threshold=7.0,
                    recommendation='Long gaps make it harder to track trends. Try to maintain consistency.'
                ))

        return flags

    def _detect_inconsistent_tracking(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect inconsistent tracking patterns."""
        flags = []

        # Check if bodyfat is tracked inconsistently
        bf_count = df['bs_bodyfat_pct'].notna().sum()
        total_count = len(df)
        bf_coverage = bf_count / total_count * 100

        if 0 < bf_coverage < 30:
            flags.append(RedFlag(
                id='RF_InconsistentBF',
                severity='low',
                category='data_quality',
                title='Inconsistent Body Fat Tracking',
                description=f'Body fat is only tracked {bf_coverage:.1f}% of the time. This limits body composition analysis.',
                dates_affected=[],
                value=bf_coverage,
                threshold=30.0,
                recommendation='Consider tracking body fat % consistently for better composition insights.'
            ))

        # Check if calorie tracking is inconsistent
        cal_count = df['cal_in_kcal'].notna().sum()
        cal_coverage = cal_count / total_count * 100

        if 0 < cal_coverage < 50:
            flags.append(RedFlag(
                id='RF_InconsistentCalories',
                severity='medium',
                category='data_quality',
                title='Inconsistent Calorie Tracking',
                description=f'Calories are only tracked {cal_coverage:.1f}% of the time. This limits calorie balance analysis.',
                dates_affected=[],
                value=cal_coverage,
                threshold=50.0,
                recommendation='Track calories consistently to understand your energy balance better.'
            ))

        return flags

    def _detect_duplicate_patterns(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect suspicious duplicate values."""
        flags = []

        # Check for too many identical weight values in a row
        if len(df) >= 5:
            df_sorted = df.sort_values('date')
            weight_values = df_sorted['bs_weight_kg'].values

            max_streak = 1
            current_streak = 1
            streak_value = None

            for i in range(1, len(weight_values)):
                if weight_values[i] == weight_values[i-1]:
                    current_streak += 1
                    if current_streak > max_streak:
                        max_streak = current_streak
                        streak_value = weight_values[i]
                else:
                    current_streak = 1

            if max_streak >= 7:
                flags.append(RedFlag(
                    id='RF_IdenticalWeights',
                    severity='low',
                    category='data_quality',
                    title='Identical Weight Values',
                    description=f'Weight has been exactly {streak_value:.1f} kg for {max_streak} consecutive days. Natural weight fluctuates daily.',
                    dates_affected=[],
                    value=max_streak,
                    threshold=7.0,
                    recommendation='Verify scale accuracy and weighing conditions. Weight naturally varies 0.5-1 kg daily.'
                ))

        return flags

    def _detect_extreme_weight_changes(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect extreme daily weight changes."""
        flags = []

        df_sorted = df.sort_values('date')
        if len(df_sorted) < 2:
            return flags

        df_sorted['weight_change'] = df_sorted['bs_weight_kg'].diff()

        # Check for extreme single-day changes (>2 kg)
        extreme_changes = df_sorted[abs(df_sorted['weight_change']) > 2.0]

        for idx, row in extreme_changes.iterrows():
            change = row['weight_change']
            change_date = row['date']

            flags.append(RedFlag(
                id=f'RF_ExtremeWeightChange_{change_date.strftime("%Y%m%d")}',
                severity='high',
                category='health',
                title=f'Extreme Weight Change: {change:+.1f} kg',
                description=f'Weight changed by {change:+.1f} kg on {change_date.strftime("%Y-%m-%d")}. This is unusual for a single day.',
                dates_affected=[change_date],
                value=abs(change),
                threshold=2.0,
                recommendation='Verify measurement accuracy. Extreme daily changes are usually water weight or measurement errors.'
            ))

        return flags

    def _detect_extreme_calorie_deficit(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect dangerously low calorie deficits."""
        flags = []

        cal_data = df[df['cal_net_kcal'].notna()]
        if len(cal_data) == 0:
            return flags

        # Check for extreme deficit days (< -1000 kcal)
        extreme_deficit = cal_data[cal_data['cal_net_kcal'] < -1000]

        if len(extreme_deficit) > 0:
            dates = extreme_deficit['date'].tolist()
            avg_deficit = extreme_deficit['cal_net_kcal'].mean()

            flags.append(RedFlag(
                id='RF_ExtremeDeficit',
                severity='critical',
                category='health',
                title='Extreme Calorie Deficit',
                description=f'Found {len(extreme_deficit)} days with calorie deficit below -1000 kcal (avg: {avg_deficit:.0f} kcal). This is too aggressive.',
                dates_affected=dates,
                value=avg_deficit,
                threshold=-1000.0,
                recommendation='Very large deficits can harm metabolism and muscle mass. Aim for -300 to -500 kcal/day deficit.'
            ))

        # Check 7-day average deficit
        if 'cal_net_7d_avg_kcal' in df.columns:
            recent_avg = df['cal_net_7d_avg_kcal'].dropna()
            if len(recent_avg) > 0:
                latest_avg = recent_avg.iloc[-1]
                if latest_avg < -800:
                    flags.append(RedFlag(
                        id='RF_SustainedDeficit',
                        severity='high',
                        category='health',
                        title='Sustained Extreme Deficit',
                        description=f'7-day average deficit is {latest_avg:.0f} kcal/day. This is too aggressive for sustained weight loss.',
                        dates_affected=[],
                        value=latest_avg,
                        threshold=-800.0,
                        recommendation='Reduce deficit to -300 to -500 kcal/day for sustainable, healthy weight loss.'
                    ))

        return flags

    def _detect_extreme_calorie_surplus(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect large calorie surpluses during cutting phase."""
        flags = []

        cal_data = df[df['cal_net_kcal'].notna()]
        if len(cal_data) == 0:
            return flags

        # Check for large surplus days (> +500 kcal)
        large_surplus = cal_data[cal_data['cal_net_kcal'] > 500]

        if len(large_surplus) > 3:
            dates = large_surplus['date'].tolist()
            avg_surplus = large_surplus['cal_net_kcal'].mean()

            flags.append(RedFlag(
                id='RF_FrequentSurplus',
                severity='medium',
                category='progress',
                title='Frequent Calorie Surplus',
                description=f'Found {len(large_surplus)} days with calorie surplus above +500 kcal (avg: {avg_surplus:.0f} kcal).',
                dates_affected=dates,
                value=avg_surplus,
                threshold=500.0,
                recommendation='Frequent surpluses will slow or reverse weight loss progress. Stay consistent with deficit.'
            ))

        return flags

    def _detect_low_calorie_intake(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect dangerously low calorie intake."""
        flags = []

        cal_data = df[df['cal_in_kcal'].notna()]
        if len(cal_data) == 0:
            return flags

        # Check for very low intake days (< 1200 kcal for prolonged periods)
        low_intake = cal_data[cal_data['cal_in_kcal'] < 1200]

        if len(low_intake) > 5:
            dates = low_intake['date'].tolist()
            avg_intake = low_intake['cal_in_kcal'].mean()

            flags.append(RedFlag(
                id='RF_LowIntake',
                severity='critical',
                category='health',
                title='Very Low Calorie Intake',
                description=f'Found {len(low_intake)} days with intake below 1200 kcal (avg: {avg_intake:.0f} kcal). This is too low for most adults.',
                dates_affected=dates,
                value=avg_intake,
                threshold=1200.0,
                recommendation='Minimum intake should be ~1500 kcal for men, ~1200 for women. Very low intake risks nutrient deficiency.'
            ))

        return flags

    def _detect_rapid_fat_loss(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect too rapid fat mass loss."""
        flags = []

        fm_data = df[df['bs_fat_mass_kg'].notna()].sort_values('date')
        if len(fm_data) < 14:
            return flags

        # Check 14-day fat mass change
        recent_14d = fm_data.tail(14)
        if len(recent_14d) >= 10:  # Need at least 10 data points
            fm_start = recent_14d['bs_fat_mass_kg'].iloc[0]
            fm_end = recent_14d['bs_fat_mass_kg'].iloc[-1]
            fm_change = fm_end - fm_start

            # Healthy fat loss: 0.5-1.0 kg per week (1-2 kg per 14 days)
            if fm_change < -3.0:
                flags.append(RedFlag(
                    id='RF_RapidFatLoss',
                    severity='high',
                    category='health',
                    title='Rapid Fat Mass Loss',
                    description=f'Fat mass decreased by {abs(fm_change):.1f} kg in 14 days. Healthy rate is 1-2 kg per 2 weeks.',
                    dates_affected=[],
                    value=fm_change,
                    threshold=-3.0,
                    recommendation='Rapid fat loss often includes muscle loss. Slow down to 0.5-1.0 kg fat loss per week.'
                ))

        return flags

    def _detect_weight_plateaus(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect weight loss plateaus."""
        flags = []

        if len(df) < 14:
            return flags

        # Check 14-day rolling average change
        if 'bs_weight_14d_avg_kg' in df.columns:
            df_sorted = df.sort_values('date')
            recent_14d = df_sorted[df_sorted['bs_weight_14d_avg_kg'].notna()].tail(14)

            if len(recent_14d) >= 10:
                start_avg = recent_14d['bs_weight_14d_avg_kg'].iloc[0]
                end_avg = recent_14d['bs_weight_14d_avg_kg'].iloc[-1]
                change = end_avg - start_avg

                # If 14-day average changed less than 0.3 kg, it's a plateau
                if abs(change) < 0.3:
                    flags.append(RedFlag(
                        id='RF_Plateau',
                        severity='low',
                        category='progress',
                        title='Weight Plateau Detected',
                        description=f'14-day average weight changed only {change:.2f} kg. Progress has stalled.',
                        dates_affected=[],
                        value=abs(change),
                        threshold=0.3,
                        recommendation='Consider adjusting calorie intake or increasing activity if goal is weight loss.'
                    ))

        return flags

    def _detect_yo_yo_pattern(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect yo-yo dieting pattern."""
        flags = []

        if len(df) < 30:
            return flags

        df_sorted = df.sort_values('date')

        # Calculate 7-day trends (up or down)
        if 'bs_weight_7d_avg_kg' in df.columns:
            df_sorted['trend'] = df_sorted['bs_weight_7d_avg_kg'].diff()

            # Count direction changes
            direction_changes = 0
            for i in range(1, len(df_sorted)):
                if pd.notna(df_sorted['trend'].iloc[i]) and pd.notna(df_sorted['trend'].iloc[i-1]):
                    if df_sorted['trend'].iloc[i] * df_sorted['trend'].iloc[i-1] < 0:
                        direction_changes += 1

            # If more than 4 direction changes in 30 days, flag it
            if direction_changes > 4:
                flags.append(RedFlag(
                    id='RF_YoYo',
                    severity='medium',
                    category='consistency',
                    title='Yo-Yo Weight Pattern',
                    description=f'Weight trend changed direction {direction_changes} times in recent period. This indicates inconsistent habits.',
                    dates_affected=[],
                    value=direction_changes,
                    threshold=4.0,
                    recommendation='Focus on consistent daily habits rather than aggressive short-term efforts.'
                ))

        return flags

    def _detect_inconsistent_bodyfat(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect inconsistent body fat measurements."""
        flags = []

        bf_data = df[df['bs_bodyfat_pct'].notna()].sort_values('date')
        if len(bf_data) < 5:
            return flags

        # Check for large single-measurement changes (> 2% in one day)
        bf_data['bf_change'] = bf_data['bs_bodyfat_pct'].diff()
        large_changes = bf_data[abs(bf_data['bf_change']) > 2.0]

        if len(large_changes) > 0:
            for idx, row in large_changes.iterrows():
                change = row['bf_change']
                change_date = row['date']

                flags.append(RedFlag(
                    id=f'RF_InconsistentBF_{change_date.strftime("%Y%m%d")}',
                    severity='low',
                    category='data_quality',
                    title=f'Body Fat Jump: {change:+.1f}%',
                    description=f'Body fat changed by {change:+.1f}% on {change_date.strftime("%Y-%m-%d")}. True BF% changes slowly.',
                    dates_affected=[change_date],
                    value=abs(change),
                    threshold=2.0,
                    recommendation='Body fat % should change gradually. Check measurement conditions (hydration, time of day).'
                ))

        return flags

    def _detect_stalled_progress(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect stalled progress toward goals."""
        flags = []

        if len(df) < 21:
            return flags

        # Check 21-day weight change
        df_sorted = df.sort_values('date')
        weight_start = df_sorted['bs_weight_kg'].iloc[0]
        weight_end = df_sorted['bs_weight_kg'].iloc[-1]
        weight_change = weight_end - weight_start

        # If minimal change over 21 days and still above target, flag it
        if abs(weight_change) < 0.5:
            # Assume target is to lose weight if current is high
            if weight_end > 75:  # Example target threshold
                flags.append(RedFlag(
                    id='RF_StalledProgress',
                    severity='medium',
                    category='progress',
                    title='Minimal Progress',
                    description=f'Weight changed only {weight_change:.2f} kg over {len(df)} days. Progress is very slow.',
                    dates_affected=[],
                    value=abs(weight_change),
                    threshold=0.5,
                    recommendation='Review your calorie tracking accuracy and consider adjusting your deficit.'
                ))

        return flags

    def _detect_unexpected_weight_gain(self, df: pd.DataFrame) -> List[RedFlag]:
        """Detect unexpected weight gain during deficit."""
        flags = []

        if len(df) < 14:
            return flags

        # Check if in deficit on average but gaining weight
        cal_data = df[df['cal_net_kcal'].notna()]
        if len(cal_data) >= 7:
            avg_net_cal = cal_data['cal_net_kcal'].mean()

            # If average is deficit
            if avg_net_cal < -200:
                df_sorted = df.sort_values('date')
                weight_change = df_sorted['bs_weight_kg'].iloc[-1] - df_sorted['bs_weight_kg'].iloc[0]

                # But weight is increasing
                if weight_change > 0.5:
                    flags.append(RedFlag(
                        id='RF_UnexpectedGain',
                        severity='high',
                        category='progress',
                        title='Weight Gain Despite Deficit',
                        description=f'Average deficit is {avg_net_cal:.0f} kcal/day, but weight increased by {weight_change:.1f} kg.',
                        dates_affected=[],
                        value=weight_change,
                        threshold=0.5,
                        recommendation='Verify calorie tracking accuracy. Check for hidden calories or portion size errors.'
                    ))

        return flags
