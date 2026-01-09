#!/bin/bash
# DIET_APP Stop Script
# Usage: bash stop.sh

echo "🛑 Stopping DIET_APP..."

# Kill streamlit process
if pkill -f "streamlit run app/main.py"; then
    echo "✅ DIET_APP stopped successfully!"
else
    echo "⚠️  DIET_APP was not running"
fi
