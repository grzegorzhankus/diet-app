# DIET_APP 🏋️

**CFO-grade diet and training tracker** with ML-powered pattern analysis.

![Version](https://img.shields.io/badge/version-0.10.0-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Tests](https://img.shields.io/badge/tests-170%20passing-green)

## Features

### Core Functionality
- ✅ **Daily Entry Tracking** - Weight, body fat %, calories in/out, exercise, notes
- ✅ **Edit/Delete Entries** - Full CRUD operations with history management
- ✅ **Comprehensive Metrics** - Body composition, rolling averages, net balance
- ✅ **KPI Dashboard** - 12+ key performance indicators with trends
- ✅ **Red Flag Detection** - 9 automated warning systems for diet/training issues

### Analytics & ML
- ✅ **Pattern Recognition** - ML-powered detection of weekend/holiday behavior patterns
- ✅ **Polish Holiday Calendar** - Integrated with Corpus Christi, Easter, etc.
- ✅ **Statistical Validation** - T-tests for pattern significance (p < 0.05)
- ✅ **Temporal Analysis** - Day-of-week, weekend vs weekday comparisons

### Visualizations
- 📈 **Interactive Charts** - 5 Plotly visualizations (heatmaps, box plots, timelines)
- 📊 **Day-of-Week Heatmap** - Spot calorie patterns across weeks
- 🎊 **Weekend vs Weekday Analysis** - Distribution comparison with statistical tests
- 🎉 **Holiday Impact Timeline** - Weight & calorie trends with holiday markers
- 🌐 **Pattern Radar Chart** - Polar view of daily patterns

### Forecasting & Predictions
- 🔮 **Weight Forecasting** - 30-day predictions with confidence intervals
- 📉 **Linear & Calorie-Based Models** - Automatic method selection
- 🎯 **Target Weight Calculator** - Reverse-engineer required daily calories

### Export & LLM
- 📤 **Excel/CSV/PDF Export** - Professional reports with charts
- 🤖 **AI Insights** (Optional) - Ollama integration for natural language analysis
- 💬 **Q&A Engine** - Ask questions about your data

### Data Management
- 📥 **Excel Import** - Bulk import from existing tracking spreadsheets
- 🗄️ **SQLite Storage** - Fast, reliable, offline-first
- ✅ **170 Tests** - Comprehensive test coverage

## Tech Stack

- **Frontend**: Streamlit 1.28+
- **Data**: Pandas, NumPy
- **ML**: Scipy (statistical tests), Pattern recognition algorithms
- **Viz**: Plotly 5.18+ (interactive charts)
- **Storage**: SQLite with Pydantic schemas
- **Testing**: Pytest (170 tests)
- **Optional**: Ollama (local LLM)

## Installation

### Local Setup

```bash
# Clone repository
git clone <your-repo-url>
cd DIET_APP

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app/main.py
```

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Click "New app"
4. Select your repository
5. Set main file: `app/main.py`
6. Click "Deploy"

**Note**: Each user will have their own isolated SQLite database.

## Usage

### Quick Start

1. **Add Daily Entry** - Record weight, body fat, calories
2. **View Dashboard** - See trends and visualizations
3. **Check KPIs** - Monitor 12+ performance indicators
4. **Analyze Patterns** - Discover weekend/holiday eating patterns
5. **Forecast** - Predict weight trajectory
6. **Export** - Generate Excel/PDF reports

### Pattern Analysis

Navigate to **🔬 Pattern Analysis** to discover:
- When do you overeat? (weekends, holidays)
- Which day is your best/worst?
- Are patterns statistically significant?
- How consistent are you?

### Key Pages

- **📝 Daily Entry** - Add/edit measurements
- **📊 History** - View all entries
- **📈 Dashboard** - Charts and trends
- **📊 KPIs** - Performance indicators
- **🚩 Red Flags** - Warning detection
- **🔮 Forecast** - Weight predictions
- **🔬 Pattern Analysis** - ML insights
- **📤 Export** - Download reports

## Configuration

### Customize BMR & Goals

Edit in sidebar of relevant pages:
- BMR (Basal Metabolic Rate): 2000 kcal default
- Target weight: Set your goal
- Analysis period: 7-180 days

### Database Location

Default: `data/diet_app.db`

Change in code if needed (search for `db_path`).

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ml_patterns.py

# Run with coverage
pytest --cov=core --cov=app
```

**Current Status**: 170 tests passing ✅

## Architecture

```
DIET_APP/
├── app/
│   ├── main.py                    # Main entry point
│   └── pages/                     # Streamlit pages
│       ├── 1_📝_Daily_Entry.py
│       ├── 2_📊_History.py
│       ├── 3_📈_Dashboard.py
│       ├── 4_📊_KPIs.py
│       ├── 5_🚩_Red_Flags.py
│       ├── 6_🔮_Forecast.py
│       ├── 7_📤_Export.py
│       ├── 8_🤖_AI_Insights.py
│       └── 9_🔬_Pattern_Analysis.py
├── core/
│   ├── storage.py                 # SQLite operations
│   ├── schemas.py                 # Pydantic models
│   ├── metrics.py                 # Metrics calculation
│   ├── kpis.py                    # KPI engine
│   ├── red_flags.py               # Warning detection
│   ├── forecast.py                # Prediction engine
│   ├── export.py                  # Excel/CSV export
│   ├── pdf_export.py              # PDF generation
│   ├── importer.py                # Excel import
│   ├── llm/                       # LLM integration
│   └── ml/                        # ML modules
│       ├── patterns.py            # Pattern detection
│       ├── holidays.py            # Polish calendar
│       ├── temporal_features.py   # Feature engineering
│       └── visualizations.py      # Plotly charts
├── tests/                         # 170 tests
├── data/                          # SQLite database
├── configs/                       # Configuration files
└── docs/                          # Documentation

```

## Blocks Completed

- ✅ **Block 1**: SQLite Storage & CRUD
- ✅ **Block 2**: Metrics Calculation Engine
- ✅ **Block 3**: KPI Engine (12+ indicators)
- ✅ **Block 4**: Red Flag Detection (9 rules)
- ✅ **Block 5**: Forecasting Engine
- ✅ **Block 6**: Excel Export
- ✅ **Block 7**: CSV Export
- ✅ **Block 8**: PDF Export
- ✅ **Block 9**: LLM Integration (Ollama)
- ✅ **Block 10**: Pattern Recognition & ML
- ✅ **Block 11**: Pattern Visualizations

## License

MIT License - feel free to use for personal projects.

## Contributing

This is a personal project, but suggestions welcome via issues.

## Support

For questions or issues, please open a GitHub issue.

---

**Made with ❤️ and Claude Code**
