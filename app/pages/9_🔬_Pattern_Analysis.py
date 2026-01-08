"""
Pattern Analysis Page - ML-powered behavioral pattern detection
"""
import streamlit as st
from datetime import date
from pathlib import Path
import pandas as pd

from core.storage import Storage
from core.ml.patterns import PatternDetectionEngine
from core.ml.holidays import PolishHolidayCalendar
from core.ml.visualizations import PatternVisualizationEngine

# Page config
st.set_page_config(page_title="Pattern Analysis", page_icon="🔬", layout="wide")

st.title("🔬 Pattern Analysis")
st.caption("ML-powered detection of behavioral patterns in your diet and training")

# Initialize
db_path = Path("data/diet_app.db")
storage = Storage(str(db_path))
pattern_engine = PatternDetectionEngine(storage)
holiday_calendar = PolishHolidayCalendar()
viz_engine = PatternVisualizationEngine(storage)

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Analysis Settings")

    days_to_analyze = st.slider(
        "Analysis Period (days)",
        min_value=30,
        max_value=180,
        value=90,
        step=15,
        help="More days = better pattern detection"
    )

    st.divider()

    st.caption("**Pattern Types:**")
    st.caption("📅 Day-of-Week")
    st.caption("🎉 Holidays")
    st.caption("🎊 Weekends")
    st.caption("📊 Long Weekends")

# Main content tabs
tab_viz, tab_overview, tab_weekend, tab_holidays, tab_dow, tab_calendar = st.tabs([
    "📈 Visualizations", "📊 Overview", "🎊 Weekend Pattern", "🎉 Holiday Pattern", "📅 Day-of-Week", "📆 Calendar"
])

# Tab 0: Visualizations
with tab_viz:
    st.header("📈 Pattern Visualizations")
    st.caption("Interactive charts showing your behavioral patterns")

    # Chart 1: Holiday Impact Timeline
    st.subheader("🎉 Weight & Calorie Timeline with Holidays")
    with st.spinner("Generating timeline..."):
        timeline_fig = viz_engine.create_holiday_impact_timeline(days=days_to_analyze * 2)
        if timeline_fig:
            st.plotly_chart(timeline_fig, use_container_width=True)
        else:
            st.info("Insufficient data for timeline visualization")

    st.divider()

    # Chart 2: Weekend vs Weekday Comparison
    st.subheader("🎊 Weekend vs Weekday Distribution")
    with st.spinner("Generating comparison chart..."):
        boxplot_fig = viz_engine.create_weekend_vs_weekday_boxplot(days=days_to_analyze)
        if boxplot_fig:
            st.plotly_chart(boxplot_fig, use_container_width=True)
        else:
            st.info("Insufficient data for comparison chart")

    st.divider()

    # Chart 3: Day-of-Week Heatmap
    st.subheader("📅 Day-of-Week Calorie Heatmap")
    with st.spinner("Generating heatmap..."):
        heatmap_fig = viz_engine.create_day_of_week_heatmap(days=days_to_analyze)
        if heatmap_fig:
            st.plotly_chart(heatmap_fig, use_container_width=True)
        else:
            st.info("Insufficient data for heatmap visualization")

    st.divider()

    # Chart 4 & 5: Pattern Strength and Radar
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Weekend Surplus Trend")
        with st.spinner("Analyzing pattern strength..."):
            strength_fig = viz_engine.create_pattern_strength_chart(days=days_to_analyze)
            if strength_fig:
                st.plotly_chart(strength_fig, use_container_width=True)
            else:
                st.info("Insufficient data for trend chart")

    with col2:
        st.subheader("🌐 Daily Pattern Radar")
        with st.spinner("Generating radar chart..."):
            radar_fig = viz_engine.create_daily_pattern_radar(days=days_to_analyze)
            if radar_fig:
                st.plotly_chart(radar_fig, use_container_width=True)
            else:
                st.info("Insufficient data for radar chart")

# Tab 1: Overview
with tab_overview:
    st.header("📊 Comprehensive Pattern Analysis")

    if st.button("🔍 Analyze Patterns", type="primary", use_container_width=True):
        with st.spinner(f"Analyzing {days_to_analyze} days of data..."):
            analysis = pattern_engine.get_comprehensive_analysis(days=days_to_analyze)

        # Temporal summary
        st.subheader("📈 Data Summary")
        summary = analysis.get('temporal_summary', {})

        if summary:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Days", summary.get('total_days', 0))
            with col2:
                st.metric("Weekdays", summary.get('weekday_days', 0))
            with col3:
                st.metric("Weekends", summary.get('weekend_days', 0))
            with col4:
                st.metric("Holidays", summary.get('holiday_days', 0))

            coverage = summary.get('coverage_pct', 0)
            # Clamp coverage to [0, 100] range for progress bar
            progress_value = min(coverage / 100, 1.0)
            st.progress(progress_value, text=f"Data Coverage: {coverage:.1f}%")

        st.divider()

        # Pattern summaries
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("🎊 Weekend Pattern")
            weekend = analysis.get('weekend_pattern', {})
            if weekend.get('detected'):
                st.success("✅ Pattern Detected")
                st.write(weekend.get('pattern_summary', ''))

                if 'calories' in weekend:
                    cal = weekend['calories']
                    diff = cal.get('difference', 0)
                    if abs(diff) > 50:
                        st.metric(
                            "Weekend vs Weekday",
                            f"{diff:+.0f} kcal",
                            f"{cal.get('difference_pct', 0):.1f}%"
                        )
            else:
                st.info("ℹ️ No significant pattern detected")

        with col2:
            st.subheader("🎉 Holiday Pattern")
            holiday = analysis.get('holiday_pattern', {})
            if holiday.get('detected'):
                st.success("✅ Pattern Detected")
                st.write(holiday.get('pattern_summary', ''))

                if 'calories' in holiday:
                    cal = holiday['calories']
                    diff = cal.get('difference', 0)
                    if abs(diff) > 50:
                        st.metric(
                            "Holiday vs Normal",
                            f"{diff:+.0f} kcal",
                            f"{cal.get('difference_pct', 0):.1f}%"
                        )
            else:
                st.info("ℹ️ No significant pattern detected")

        with col3:
            st.subheader("📅 Day-of-Week")
            dow = analysis.get('day_of_week_pattern', {})
            if dow.get('detected'):
                st.success("✅ Pattern Detected")
                st.write(dow.get('pattern_summary', ''))

                if 'best_day' in dow and 'worst_day' in dow:
                    best = dow['best_day']
                    worst = dow['worst_day']
                    st.write(f"**Best:** {best['name']}")
                    st.write(f"**Worst:** {worst['name']}")
            else:
                st.info("ℹ️ No significant pattern detected")

# Tab 2: Weekend Pattern
with tab_weekend:
    st.header("🎊 Weekend vs Weekday Analysis")

    if st.button("📊 Analyze Weekend Pattern", use_container_width=True):
        with st.spinner("Analyzing weekend behavior..."):
            result = pattern_engine.detect_weekend_pattern(days=days_to_analyze)

        if result.get('detected'):
            st.success("✅ Weekend pattern detected!")
            st.write(f"**Summary:** {result.get('pattern_summary', '')}")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Weekend Statistics")
                st.metric("Weekend Days", result.get('weekend_days', 0))

                if 'calories' in result:
                    cal = result['calories']
                    st.metric("Avg Calories", f"{cal['weekend_avg']:.0f} kcal")
                    st.metric("Std Dev", f"{cal['weekend_std']:.0f} kcal")

                if 'exercise' in result:
                    ex = result['exercise']
                    st.metric("Avg Exercise", f"{ex['weekend_avg']:.0f} kcal")

            with col2:
                st.subheader("📊 Weekday Statistics")
                st.metric("Weekday Days", result.get('weekday_days', 0))

                if 'calories' in result:
                    cal = result['calories']
                    st.metric("Avg Calories", f"{cal['weekday_avg']:.0f} kcal")
                    st.metric("Std Dev", f"{cal['weekday_std']:.0f} kcal")

                if 'exercise' in result:
                    ex = result['exercise']
                    st.metric("Avg Exercise", f"{ex['weekday_avg']:.0f} kcal")

            # Statistical significance
            if 'calories' in result and 'statistical_test' in result['calories']:
                st.divider()
                st.subheader("📈 Statistical Significance")
                test = result['calories']['statistical_test']

                if test.get('significant'):
                    st.success(f"✅ Statistically significant difference (p={test['p_value']:.4f})")
                else:
                    st.info(f"ℹ️ Difference not statistically significant (p={test['p_value']:.4f})")
        else:
            st.warning(f"⚠️ {result.get('reason', 'No pattern detected')}")

# Tab 3: Holiday Pattern
with tab_holidays:
    st.header("🎉 Polish Holiday Analysis")

    if st.button("📊 Analyze Holiday Pattern", use_container_width=True):
        with st.spinner("Analyzing holiday behavior..."):
            result = pattern_engine.detect_holiday_pattern(days=days_to_analyze * 2)

        if result.get('detected'):
            st.success("✅ Holiday pattern detected!")
            st.write(f"**Summary:** {result.get('pattern_summary', '')}")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Holiday Days", result.get('holiday_days_count', 0))
                if 'long_weekends' in result:
                    st.metric("Long Weekend Days", result['long_weekends']['days_count'])

            with col2:
                st.metric("Normal Days", result.get('non_holiday_days_count', 0))

            # Holidays observed
            if result.get('holidays_observed'):
                st.divider()
                st.subheader("🎉 Holidays in Period")
                for holiday in result['holidays_observed']:
                    st.write(f"• {holiday}")

            # Calorie comparison
            if 'calories' in result:
                st.divider()
                st.subheader("📊 Calorie Comparison")
                cal = result['calories']

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Holiday Avg", f"{cal['holiday_avg']:.0f} kcal")
                with col2:
                    st.metric("Normal Avg", f"{cal['normal_avg']:.0f} kcal")
                with col3:
                    diff = cal['difference']
                    st.metric("Difference", f"{diff:+.0f} kcal", f"{cal['difference_pct']:+.1f}%")
        else:
            st.warning(f"⚠️ {result.get('reason', 'No pattern detected')}")

# Tab 4: Day-of-Week
with tab_dow:
    st.header("📅 Day-of-Week Pattern Analysis")

    if st.button("📊 Analyze Day-of-Week Pattern", use_container_width=True):
        with st.spinner("Analyzing daily patterns..."):
            result = pattern_engine.detect_day_of_week_pattern(days=days_to_analyze)

        if result.get('detected'):
            st.success("✅ Day-of-week patterns detected!")
            st.write(f"**Summary:** {result.get('pattern_summary', '')}")

            # Best and worst days
            if 'best_day' in result and 'worst_day' in result:
                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "🟢 Best Day",
                        result['best_day']['name'],
                        f"{result['best_day']['avg_calories']:.0f} kcal avg"
                    )

                with col2:
                    st.metric(
                        "🔴 Worst Day",
                        result['worst_day']['name'],
                        f"{result['worst_day']['avg_calories']:.0f} kcal avg"
                    )

            # Day-by-day breakdown
            if 'days_by_dow' in result:
                st.divider()
                st.subheader("📊 Daily Breakdown")

                # Create DataFrame for display
                dow_data = []
                for dow, stats in result['days_by_dow'].items():
                    row = {
                        'Day': stats.get('day_name', ''),
                        'Count': stats.get('count', 0)
                    }
                    if 'calories' in stats:
                        row['Avg Calories'] = f"{stats['calories']['mean']:.0f}"
                        row['Min'] = f"{stats['calories']['min']:.0f}"
                        row['Max'] = f"{stats['calories']['max']:.0f}"
                    if 'exercise' in stats:
                        row['Avg Exercise'] = f"{stats['exercise']['mean']:.0f}"
                    dow_data.append(row)

                if dow_data:
                    df = pd.DataFrame(dow_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"⚠️ {result.get('reason', 'No pattern detected')}")

# Tab 5: Holiday Calendar
with tab_calendar:
    st.header("📆 Polish Holiday Calendar")
    st.write("Reference calendar of Polish national holidays for pattern analysis")

    year = st.selectbox("Year", list(range(2020, 2031)), index=6)  # Default 2026

    holidays = holiday_calendar.get_holidays(year)

    st.subheader(f"🎉 {year} Polish National Holidays")

    # Group by month
    holidays_by_month = {}
    for holiday_date, name in sorted(holidays.items()):
        month = holiday_date.strftime("%B")
        if month not in holidays_by_month:
            holidays_by_month[month] = []
        holidays_by_month[month].append((holiday_date, name))

    # Display in columns
    cols = st.columns(3)
    month_list = list(holidays_by_month.items())

    for idx, (month, month_holidays) in enumerate(month_list):
        with cols[idx % 3]:
            st.markdown(f"**{month}**")
            for holiday_date, name in month_holidays:
                st.write(f"{holiday_date.strftime('%d')} - {name}")
            st.write("")  # Spacing

# Footer
st.divider()
st.info("""
**💡 Pattern Insights:**
- **Weekend overeating** is common - use this data to plan better
- **Polish holidays** often coincide with increased calorie intake
- **Day-of-week patterns** can help you identify your best and worst days
- **Statistical significance** tells you if patterns are real or random variation
""")

st.caption("Patterns are detected using statistical analysis (t-tests, descriptive statistics)")
