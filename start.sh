#!/bin/bash
# DIET_APP Startup Script
# Usage: bash start.sh

cd "$(dirname "$0")"

echo "🚀 Starting DIET_APP..."

# Stop any running Streamlit apps first
pkill -f "streamlit run" 2>/dev/null && echo "🛑 Stopped other apps" || true
sleep 1

# Start the app in background
nohup .venv/bin/streamlit run app/main.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    > /tmp/diet_app.log 2>&1 &

# Wait for startup
echo "⏳ Waiting for app to start..."
sleep 3

# Check if it started successfully
if pgrep -f "streamlit run app/main.py" > /dev/null; then
    echo "✅ DIET_APP started successfully!"
    echo "📍 Access it at: http://localhost:8501"
    echo "📋 Logs: /tmp/diet_app.log"
else
    echo "❌ Failed to start DIET_APP"
    echo "Check logs: /tmp/diet_app.log"
    exit 1
fi
