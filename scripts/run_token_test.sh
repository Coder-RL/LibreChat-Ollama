#!/bin/bash

cd "$(dirname "$0")/.."

source .venv/bin/activate

echo "▶ Running token count storage test..."
python tests/test_token_count_storage.py