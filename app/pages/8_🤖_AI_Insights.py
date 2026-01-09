"""
AI Insights Page - LLM-powered analytics and Q&A
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import streamlit as st
from datetime import date
from pathlib import Path

from core.storage import Storage
from core.i18n import t, get_text

from core.llm.client import OllamaClient
from core.llm.narration import NarrationEngine
from core.llm.qa_engine import QAEngine
from core.llm.benchmark import LLMBenchmark

# Page config
st.set_page_config(page_title="AI Insights", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

st.title("🤖 AI Insights")
st.caption("Local LLM-powered analysis and Q&A (requires Ollama)")

# Initialize storage and LLM components
db_path = Path("data/diet_app.db")
storage = Storage(str(db_path))
ollama_client = OllamaClient()

# Sidebar settings
with st.sidebar:
    st.header("⚙️ LLM Settings")

    available_models = ollama_client.list_models()
    if available_models:
        selected_model = st.selectbox(
            "Model",
            available_models,
            index=0 if available_models else None
        )
        ollama_client.model = selected_model
    else:
        st.warning("⚠️ No Ollama models found")
        selected_model = "llama3.2:latest"
        ollama_client.model = selected_model

    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1,
                           help="Lower = more deterministic, Higher = more creative")

    bmr_kcal = st.number_input("BMR (kcal/day)", 1200, 3000, 2000, 50)
    target_weight = st.number_input("Target Weight (kg)", 50.0, 150.0, 75.0, 0.5)

    st.divider()

    # Ollama status
    if ollama_client.is_available():
        st.success(f"✅ Ollama Connected")
        st.caption(f"Model: {selected_model}")
    else:
        st.error("❌ Ollama Not Available")
        st.caption("Start Ollama to use AI features")
        st.info("Install: https://ollama.com")

# Main content tabs
tab_summary, tab_qa, tab_recommendations, tab_benchmark = st.tabs([
    "📊 Summary", "💬 Q&A", "📝 Recommendations", "⚡ Benchmark"
])

# Tab 1: Summary Narration
with tab_summary:
    st.header("📊 AI-Generated Summary")
    st.write("Get an AI-generated summary of your progress based on computed metrics.")

    col1, col2 = st.columns([2, 1])

    with col1:
        days_summary = st.slider("Analysis Period (days)", 7, 90, 30, key="summary_days")

    with col2:
        if st.button("🤖 Generate Summary", type="primary", use_container_width=True):
            if not ollama_client.is_available():
                st.error("Ollama is not available. Please start Ollama first.")
            else:
                narration_engine = NarrationEngine(
                    storage=storage,
                    ollama_client=ollama_client,
                    bmr_kcal=bmr_kcal,
                    target_weight_kg=target_weight
                )

                with st.spinner(f"Analyzing {days_summary} days of data..."):
                    result = narration_engine.generate_summary(
                        days=days_summary,
                        temperature=temperature
                    )

                if result.get('error'):
                    st.error(f"❌ Error: {result['error']}")
                elif result.get('summary'):
                    st.success("✅ Summary Generated")
                    st.markdown(result['summary'])

                    # Show metadata
                    with st.expander("ℹ️ Generation Info"):
                        st.caption(f"Model: {result.get('model', 'unknown')}")
                        st.caption(f"Duration: {result.get('duration_ms', 0)} ms")

                        if result.get('validation_warning'):
                            st.warning(f"⚠️ {result['validation_warning']}")

                    # Show facts used
                    with st.expander("📊 Data Used"):
                        facts = result.get('facts', {})
                        summary_stats = facts.get('summary', {})
                        st.json({
                            'entries': summary_stats.get('total_entries'),
                            'coverage': f"{summary_stats.get('coverage_percent', 0):.0f}%",
                            'kpis_computed': len(facts.get('kpis', [])),
                            'red_flags': len(facts.get('red_flags', []))
                        })

# Tab 2: Q&A
with tab_qa:
    st.header("💬 Ask Questions About Your Data")
    st.write("Ask natural language questions about your diet and training progress.")

    days_qa = st.slider("Data Period (days)", 7, 180, 90, key="qa_days")

    # Question examples
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What is my current weight trend?
        - How many calories am I eating on average?
        - Are there any problems with my data?
        - How is my performance over the last month?
        - What red flags should I be aware of?
        """)

    question = st.text_input("Your question:", placeholder="What is my weight trend?")

    if st.button("🔍 Ask", type="primary"):
        if not question:
            st.warning("Please enter a question.")
        elif not ollama_client.is_available():
            st.error("Ollama is not available.")
        else:
            qa_engine = QAEngine(
                storage=storage,
                ollama_client=ollama_client,
                bmr_kcal=bmr_kcal,
                target_weight_kg=target_weight
            )

            with st.spinner("Analyzing..."):
                result = qa_engine.ask(question, days=days_qa, temperature=temperature)

            if result.get('error'):
                st.warning(f"⚠️ {result['error']}")
                if result.get('answer'):  # Fallback answer
                    st.info(f"📊 Basic Answer: {result['answer']}")
            elif result.get('answer'):
                st.success("✅ Answer:")
                st.markdown(result['answer'])

                with st.expander("ℹ️ Info"):
                    st.caption(f"Model: {result.get('model', 'fallback')}")
                    if result.get('duration_ms'):
                        st.caption(f"Duration: {result['duration_ms']} ms")

# Tab 3: Recommendations
with tab_recommendations:
    st.header("📝 AI Recommendations")
    st.write("Get focused recommendations for improvement.")

    focus_area = st.selectbox(
        "Focus Area",
        ["general", "weight", "calories", "consistency"],
        format_func=lambda x: x.capitalize()
    )

    days_rec = st.slider("Analysis Period (days)", 7, 90, 30, key="rec_days")

    if st.button("📝 Get Recommendations", type="primary"):
        if not ollama_client.is_available():
            st.error("Ollama is not available.")
        else:
            narration_engine = NarrationEngine(
                storage=storage,
                ollama_client=ollama_client,
                bmr_kcal=bmr_kcal,
                target_weight_kg=target_weight
            )

            with st.spinner("Generating recommendations..."):
                result = narration_engine.generate_recommendation(
                    focus=focus_area,
                    days=days_rec,
                    temperature=temperature
                )

            if result.get('error'):
                st.error(f"❌ {result['error']}")
            elif result.get('recommendation'):
                st.success(f"✅ {focus_area.capitalize()} Recommendations:")
                st.markdown(result['recommendation'])

# Tab 4: Benchmark
with tab_benchmark:
    st.header("⚡ LLM Performance Benchmark")
    st.write("Test your local LLM performance.")

    if st.button("🚀 Run Benchmark Suite", type="primary"):
        if not ollama_client.is_available():
            st.error("Ollama is not available.")
        else:
            benchmark = LLMBenchmark(ollama_client=ollama_client, storage=storage)

            with st.spinner("Running benchmarks... (this may take a minute)"):
                results = benchmark.benchmark_suite()

            if results.get('ollama_available'):
                st.success("✅ Benchmark Complete")

                # Summary metrics
                summary = results.get('summary', {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Tokens/sec", f"{summary.get('avg_tokens_per_second', 0):.1f}")
                with col2:
                    st.metric("Max Tokens/sec", f"{summary.get('max_tokens_per_second', 0):.1f}")
                with col3:
                    st.metric("Avg Latency", f"{summary.get('avg_latency_ms', 0):.0f} ms")

                # Detailed results
                with st.expander("📊 Detailed Results"):
                    st.json(results['benchmarks'])

                # Save results
                if st.button("💾 Save Results"):
                    save_path = Path("exports") / f"benchmark_{date.today().isoformat()}.json"
                    benchmark.export_results(save_path)
                    st.success(f"Saved to {save_path}")
            else:
                st.error(f"❌ {results.get('error', 'Benchmark failed')}")

# Footer info
st.divider()
st.caption("""
**⚠️ Important Notes:**
- All LLM processing happens **locally** on your machine
- No data is sent to external servers
- LLM responses are based ONLY on your computed metrics
- Responses may vary between runs (adjust temperature for consistency)
- This is an optional feature - all core analytics work without AI
""")
