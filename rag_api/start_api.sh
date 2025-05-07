#!/bin/bash

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start the RAG API
echo "Starting RAG API on port 5110..."
uvicorn app.main:app --host 0.0.0.0 --port 5110 --reload
