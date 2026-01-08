"""
Pattern Visualization Engine for DIET_APP
Creates interactive charts for behavioral pattern analysis.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from core.storage import Storage
from core.ml.temporal_features import TemporalFeatureEngine
from core.ml.holidays import PolishHolidayCalendar


class PatternVisualizationEngine:
    """
    Creates interactive visualizations for pattern analysis.
    Uses Plotly for rich, interactive charts.
    """

    def __init__(self, storage: Storage):
        """
        Initialize visualization engine.

        Args:
            storage: Data storage instance
        """
        self.storage = storage
        self.temporal = TemporalFeatureEngine()
        self.holiday_calendar = PolishHolidayCalendar()

        # Color scheme for consistency
        self.colors = {
            'workweek': '#4CAF50',  # Green
            'weekend': '#FF9800',    # Orange
            'holiday': '#F44336',    # Red
            'long_weekend': '#9C27B0',  # Purple
            'primary': '#2196F3',    # Blue
            'secondary': '#607D8B'   # Grey
        }

    def _get_enriched_data(self, days: int = 90) -> pd.DataFrame:
        """
        Get data enriched with temporal features.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame with temporal features
        """
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

    def create_day_of_week_heatmap(self, days: int = 90) -> Optional[go.Figure]:
        """
        Create heatmap showing calorie intake by day of week over time.

        Args:
            days: Number of days to analyze

        Returns:
            Plotly figure or None if insufficient data
        """
        df = self._get_enriched_data(days)

        if df.empty or 'cal_in_kcal' not in df.columns:
            return None

        # Filter to rows with calorie data
        df = df[df['cal_in_kcal'].notna()].copy()

        if len(df) < 7:
            return None

        # Create week number for grouping
        df['week'] = df['date'].dt.isocalendar().week
        df['year'] = df['date'].dt.year
        df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)

        # Pivot: rows = weeks, columns = day of week
        pivot = df.pivot_table(
            values='cal_in_kcal',
            index='year_week',
            columns='day_of_week',
            aggfunc='mean'
        )

        # Sort by week
        pivot = pivot.sort_index()

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[self.temporal.POLISH_DAYS[i] for i in range(7)],
            y=pivot.index,
            colorscale='RdYlGn_r',  # Red (high) to Green (low)
            text=np.round(pivot.values, 0),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="kcal")
        ))

        fig.update_layout(
            title="Calorie Intake Heatmap: Day of Week Over Time",
            xaxis_title="Day of Week",
            yaxis_title="Week",
            height=max(400, len(pivot) * 30),  # Scale height with weeks
            font=dict(size=12)
        )

        return fig

    def create_weekend_vs_weekday_boxplot(self, days: int = 90) -> Optional[go.Figure]:
        """
        Create box plot comparing weekend vs weekday calorie intake.

        Args:
            days: Number of days to analyze

        Returns:
            Plotly figure or None if insufficient data
        """
        df = self._get_enriched_data(days)

        if df.empty or 'cal_in_kcal' not in df.columns:
            return None

        # Filter to rows with calorie data
        df = df[df['cal_in_kcal'].notna()].copy()

        if len(df) < 10:
            return None

        # Separate weekend and weekday
        df['period_label'] = df.apply(
            lambda row: 'Holiday' if row['is_holiday'] else
                       ('Weekend' if row['is_weekend'] else 'Weekday'),
            axis=1
        )

        fig = go.Figure()

        # Add box plots for each period type
        for period, color in [
            ('Weekday', self.colors['workweek']),
            ('Weekend', self.colors['weekend']),
            ('Holiday', self.colors['holiday'])
        ]:
            period_data = df[df['period_label'] == period]['cal_in_kcal']
            if len(period_data) > 0:
                fig.add_trace(go.Box(
                    y=period_data,
                    name=period,
                    marker_color=color,
                    boxmean='sd'  # Show mean and standard deviation
                ))

        fig.update_layout(
            title="Calorie Intake Distribution: Weekday vs Weekend vs Holiday",
            yaxis_title="Calories (kcal)",
            showlegend=True,
            height=500
        )

        return fig

    def create_holiday_impact_timeline(self, days: int = 180) -> Optional[go.Figure]:
        """
        Create timeline showing weight/calories with holiday annotations.

        Args:
            days: Number of days to analyze

        Returns:
            Plotly figure or None if insufficient data
        """
        df = self._get_enriched_data(days)

        if df.empty:
            return None

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add weight trace
        if 'weight_kg' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['weight_kg'],
                    name='Weight',
                    line=dict(color=self.colors['primary'], width=2),
                    mode='lines+markers'
                ),
                secondary_y=False
            )

        # Add calorie trace
        if 'cal_in_kcal' in df.columns:
            cal_data = df[df['cal_in_kcal'].notna()]
            if not cal_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=cal_data['date'],
                        y=cal_data['cal_in_kcal'],
                        name='Calories IN',
                        line=dict(color=self.colors['secondary'], width=1, dash='dot'),
                        mode='lines+markers',
                        marker=dict(size=4)
                    ),
                    secondary_y=True
                )

        # Add holiday markers using shapes (more compatible than vline with dates)
        holidays = df[df['is_holiday']].copy()
        if not holidays.empty:
            for _, row in holidays.iterrows():
                holiday_date = row['date']
                fig.add_shape(
                    type="line",
                    x0=holiday_date,
                    x1=holiday_date,
                    y0=0,
                    y1=1,
                    yref="paper",
                    line=dict(color=self.colors['holiday'], width=2, dash="dash"),
                    opacity=0.5
                )

        # Highlight weekends with background color
        weekends = df[df['is_weekend']].copy()
        if not weekends.empty:
            # Group consecutive weekends
            weekend_dates = sorted(weekends['date'].unique())
            for weekend_date in weekend_dates:
                fig.add_shape(
                    type="rect",
                    x0=weekend_date,
                    x1=pd.Timestamp(weekend_date) + pd.Timedelta(days=1),
                    y0=0,
                    y1=1,
                    yref="paper",
                    fillcolor=self.colors['weekend'],
                    opacity=0.1,
                    layer="below",
                    line_width=0
                )

        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Weight (kg)", secondary_y=False)
        fig.update_yaxes(title_text="Calories (kcal)", secondary_y=True)

        fig.update_layout(
            title="Weight & Calorie Timeline with Holiday/Weekend Markers",
            hovermode="x unified",
            height=500
        )

        return fig

    def create_pattern_strength_chart(self, days: int = 90) -> Optional[go.Figure]:
        """
        Create chart showing evolution of weekend pattern over time.

        Args:
            days: Number of days to analyze

        Returns:
            Plotly figure or None if insufficient data
        """
        df = self._get_enriched_data(days)

        if df.empty or 'cal_in_kcal' not in df.columns:
            return None

        # Filter to rows with calorie data
        df = df[df['cal_in_kcal'].notna()].copy()

        if len(df) < 28:  # Need at least 4 weeks
            return None

        # Calculate rolling weekend vs weekday difference
        df = df.sort_values('date')
        df['week_num'] = ((df['date'] - df['date'].min()).dt.days // 7)

        # Group by week
        weekly_stats = []
        for week in sorted(df['week_num'].unique()):
            week_data = df[df['week_num'] == week]
            weekend_data = week_data[week_data['is_weekend']]
            weekday_data = week_data[week_data['is_workweek'] & ~week_data['is_holiday']]

            if len(weekend_data) > 0 and len(weekday_data) > 0:
                weekly_stats.append({
                    'week': week,
                    'weekend_avg': weekend_data['cal_in_kcal'].mean(),
                    'weekday_avg': weekday_data['cal_in_kcal'].mean(),
                    'difference': weekend_data['cal_in_kcal'].mean() - weekday_data['cal_in_kcal'].mean(),
                    'date': week_data['date'].min()
                })

        if not weekly_stats:
            return None

        stats_df = pd.DataFrame(weekly_stats)

        fig = go.Figure()

        # Add difference line
        fig.add_trace(go.Scatter(
            x=stats_df['date'],
            y=stats_df['difference'],
            name='Weekend Surplus',
            line=dict(color=self.colors['weekend'], width=3),
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(255, 152, 0, 0.2)'
        ))

        # Add zero line
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            annotation_text="No difference"
        )

        fig.update_layout(
            title="Weekend Calorie Surplus Trend (Weekly Average)",
            xaxis_title="Date",
            yaxis_title="Weekend - Weekday Difference (kcal)",
            hovermode="x unified",
            height=400
        )

        return fig

    def create_daily_pattern_radar(self, days: int = 90) -> Optional[go.Figure]:
        """
        Create radar chart showing average calories by day of week.

        Args:
            days: Number of days to analyze

        Returns:
            Plotly figure or None if insufficient data
        """
        df = self._get_enriched_data(days)

        if df.empty or 'cal_in_kcal' not in df.columns:
            return None

        # Filter to rows with calorie data
        df = df[df['cal_in_kcal'].notna()].copy()

        if len(df) < 14:
            return None

        # Calculate average by day of week
        dow_stats = df.groupby('day_of_week')['cal_in_kcal'].agg(['mean', 'count']).reset_index()

        # Filter days with at least 2 observations
        dow_stats = dow_stats[dow_stats['count'] >= 2]

        if len(dow_stats) < 5:
            return None

        # Add day names
        dow_stats['day_name'] = dow_stats['day_of_week'].map(
            lambda x: self.temporal.POLISH_DAYS[x]
        )

        # Create radar chart
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=dow_stats['mean'],
            theta=dow_stats['day_name'],
            fill='toself',
            fillcolor='rgba(33, 150, 243, 0.3)',
            line=dict(color=self.colors['primary'], width=2),
            name='Avg Calories'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[dow_stats['mean'].min() * 0.9, dow_stats['mean'].max() * 1.1]
                )
            ),
            title="Average Calorie Intake by Day of Week",
            height=500
        )

        return fig
