#!/bin/bash
# Quick start script for DIET_APP

cd "$(dirname "$0")"

# Activate venv
source .venv/bin/activate

# Run Streamlit
streamlit run app/main.py
