"""
Forecast page - Predictive weight loss trajectory
"""
import streamlit as st
from datetime import date, timedelta
import pandas as pd
import altair as alt

from core.storage import Storage
from core.forecast import ForecastEngine
from core.metrics import MetricsEngine

st.set_page_config(page_title="Forecast", page_icon="🔮", layout="wide")

st.title("🔮 Weight Forecast")
st.markdown("Predictive analytics for your weight loss journey based on current trends")

# Initialize
storage = Storage()
engine = ForecastEngine(storage, bmr_kcal=2000.0)
metrics = MetricsEngine(storage, bmr_kcal=2000.0)

# Check if data exists
if storage.count() < 7:
    st.warning("Need at least 7 days of data for forecasting. Go to **📝 Daily Entry** to add more data.")
    st.stop()

# Configuration
st.subheader("Forecast Configuration")

col1, col2, col3 = st.columns(3)

with col1:
    horizon_days = st.selectbox(
        "Forecast horizon",
        options=[7, 14, 30, 60, 90],
        index=2,  # Default: 30 days
        format_func=lambda x: f"{x} days ({x//7} weeks)"
    )

with col2:
    lookback_days = st.selectbox(
        "Historical data to use",
        options=[14, 30, 60, 90],
        index=1,  # Default: 30 days
        format_func=lambda x: f"Last {x} days"
    )

with col3:
    method = st.selectbox(
        "Forecast method",
        options=['auto', 'calorie_based', 'linear'],
        index=0,
        format_func=lambda x: {
            'auto': 'Auto (best available)',
            'calorie_based': 'Calorie-based',
            'linear': 'Linear trend'
        }[x]
    )

# Target weight (optional)
st.markdown("**Target Goal** (optional)")
col1, col2 = st.columns([2, 1])

with col1:
    use_target = st.checkbox("Set target weight goal")

target_weight = None
if use_target:
    with col2:
        # Get current weight to set reasonable bounds
        recent_df = metrics.get_metrics_dataframe(days=7)
        current_weight = recent_df['bs_weight_kg'].iloc[-1] if not recent_df.empty else 75.0

        target_weight = st.number_input(
            "Target weight (kg)",
            min_value=50.0,
            max_value=150.0,
            value=max(50.0, current_weight - 5.0),
            step=0.5
        )

st.divider()

# Generate forecast
try:
    with st.spinner("Generating forecast..."):
        forecasts, summary = engine.generate_forecast(
            horizon_days=horizon_days,
            lookback_days=lookback_days,
            target_weight_kg=target_weight,
            method=method
        )

    # Summary metrics
    st.subheader("Forecast Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Current Weight",
            f"{summary.start_weight_kg:.1f} kg"
        )

    with col2:
        st.metric(
            f"Weight in {horizon_days} days",
            f"{summary.end_weight_kg:.1f} kg",
            delta=f"{summary.total_change_kg:+.1f} kg"
        )

    with col3:
        st.metric(
            "Avg Rate",
            f"{summary.avg_rate_kg_per_week:+.2f} kg/week",
            help="Average rate of change per week"
        )

    with col4:
        confidence_pct = summary.confidence_level * 100
        st.metric(
            "Confidence",
            f"{confidence_pct:.0f}%",
            help="Forecast confidence based on data quality and consistency"
        )

    # Target date info
    if summary.target_date:
        st.success(f"📅 **Target of {target_weight:.1f} kg estimated on:** {summary.target_date.strftime('%B %d, %Y')} ({(summary.target_date - date.today()).days} days from now)")

    # Method info
    method_info = {
        'linear': '📉 Linear trend forecast based on recent weight changes',
        'calorie_based': '🍽️ Calorie-based forecast using your net calorie balance (more accurate)'
    }
    st.info(f"**Method:** {method_info.get(summary.method, 'Auto-selected based on available data')}")

    st.divider()

    # Forecast chart
    st.subheader("Weight Trajectory")

    # Prepare historical data
    hist_df = metrics.get_metrics_dataframe(days=lookback_days)
    hist_data = hist_df[['date', 'bs_weight_kg']].copy()
    hist_data['date'] = pd.to_datetime(hist_data['date'])
    hist_data['type'] = 'Historical'

    # Prepare forecast data
    forecast_data = pd.DataFrame([{
        'date': pd.to_datetime(f.date),
        'bs_weight_kg': f.predicted_weight_kg,
        'confidence_lower': f.confidence_lower_kg,
        'confidence_upper': f.confidence_upper_kg,
        'type': 'Forecast'
    } for f in forecasts])

    # Historical line
    hist_chart = alt.Chart(hist_data).mark_line(
        color='#1f77b4',
        strokeWidth=3
    ).encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('bs_weight_kg:Q', title='Weight (kg)', scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('bs_weight_kg:Q', title='Weight (kg)', format='.1f')
        ]
    )

    # Forecast line
    forecast_chart = alt.Chart(forecast_data).mark_line(
        color='#ff7f0e',
        strokeWidth=3,
        strokeDash=[5, 5]
    ).encode(
        x='date:T',
        y=alt.Y('bs_weight_kg:Q', title=''),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('bs_weight_kg:Q', title='Predicted (kg)', format='.1f')
        ]
    )

    # Confidence interval
    confidence_area = alt.Chart(forecast_data).mark_area(
        opacity=0.2,
        color='#ff7f0e'
    ).encode(
        x='date:T',
        y='confidence_lower:Q',
        y2='confidence_upper:Q',
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('confidence_lower:Q', title='Lower bound (kg)', format='.1f'),
            alt.Tooltip('confidence_upper:Q', title='Upper bound (kg)', format='.1f')
        ]
    )

    # Target line if provided
    layers = [hist_chart, confidence_area, forecast_chart]

    if target_weight:
        # Create target line spanning entire date range
        min_date = hist_data['date'].min()
        max_date = forecast_data['date'].max()

        target_data = pd.DataFrame({
            'date': [min_date, max_date],
            'target': [target_weight, target_weight]
        })

        target_line = alt.Chart(target_data).mark_line(
            color='#2ca02c',
            strokeWidth=2,
            strokeDash=[3, 3]
        ).encode(
            x='date:T',
            y=alt.Y('target:Q', title=''),
            tooltip=[alt.Tooltip('target:Q', title='Target (kg)', format='.1f')]
        )

        layers.insert(0, target_line)  # Add as background

    # Combine all layers
    combined_chart = alt.layer(*layers).resolve_scale(y='shared').properties(height=400)

    st.altair_chart(combined_chart, width='stretch')

    # Legend
    if target_weight:
        st.caption("🔵 Historical Weight | 🟠 Forecasted Weight (dashed) | 🟢 Target Goal (dashed) | 🟠 Shaded: 95% Confidence Interval")
    else:
        st.caption("🔵 Historical Weight | 🟠 Forecasted Weight (dashed) | 🟠 Shaded: 95% Confidence Interval")

    st.divider()

    # Forecast table
    st.subheader("Detailed Forecast")

    # Prepare table data
    table_data = []
    for f in forecasts[::7]:  # Show weekly data points
        table_data.append({
            'Date': f.date.strftime('%Y-%m-%d'),
            'Day': (f.date - date.today()).days,
            'Predicted Weight (kg)': f"{f.predicted_weight_kg:.1f}",
            'Confidence Range (kg)': f"{f.confidence_lower_kg:.1f} - {f.confidence_upper_kg:.1f}"
        })

    df_table = pd.DataFrame(table_data)

    st.dataframe(
        df_table,
        width='stretch',
        hide_index=True
    )

    st.divider()

    # Calorie calculator
    if target_weight:
        st.subheader("🎯 Target Calorie Calculator")

        st.markdown("Calculate the daily calories needed to reach your target weight:")

        col1, col2 = st.columns(2)

        with col1:
            target_days = st.number_input(
                "Days to reach target",
                min_value=7,
                max_value=365,
                value=min(90, max(7, horizon_days)),
                step=7
            )

        with col2:
            avg_sport = st.number_input(
                "Average sport calories/day",
                min_value=0.0,
                max_value=2000.0,
                value=300.0,
                step=50.0,
                help="Your average daily exercise calories"
            )

        # Calculate
        current_weight = summary.start_weight_kg
        cal_result = engine.calculate_target_calories(
            target_weight_kg=target_weight,
            target_days=target_days,
            current_weight_kg=current_weight,
            avg_sport_kcal=avg_sport
        )

        # Display results
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Required Daily Intake",
                f"{cal_result['required_intake_kcal']:.0f} kcal",
                help="Total calories to eat per day"
            )

        with col2:
            st.metric(
                "Daily NET Balance",
                f"{cal_result['daily_net_kcal']:+.0f} kcal",
                help="NET = Intake - BMR(2000) - Sport"
            )

        with col3:
            st.metric(
                "Weekly Rate",
                f"{cal_result['weekly_rate_kg']:+.2f} kg/week"
            )

        # Health check
        if cal_result['is_healthy']:
            st.success("✅ This is a healthy and sustainable rate of change (≤1 kg/week)")
        else:
            st.warning(f"⚠️ This rate ({abs(cal_result['weekly_rate_kg']):.1f} kg/week) may be too aggressive. Consider a longer timeframe.")

        # Additional info
        st.info(f"""
        **Summary:**
        - Change needed: {cal_result['total_change_kg']:+.1f} kg
        - Time frame: {target_days} days ({target_days//7} weeks)
        - With BMR of 2000 kcal/day and {avg_sport:.0f} kcal/day exercise
        - You need to eat {cal_result['required_intake_kcal']:.0f} kcal/day
        """)

except ValueError as e:
    st.error(f"Cannot generate forecast: {str(e)}")
    st.info("Need at least 7 days of data for reliable forecasting. Add more entries and try again.")
except Exception as e:
    st.error(f"Error generating forecast: {str(e)}")
    st.exception(e)

# Footer
st.divider()
st.caption("""
**About Forecasts:**
- Forecasts are predictions based on your current trends and may not account for future changes in behavior
- Confidence intervals show the range of likely outcomes (95% confidence)
- Calorie-based forecasts are more accurate when you track calories consistently
- Linear forecasts use recent weight trends for prediction
""")
