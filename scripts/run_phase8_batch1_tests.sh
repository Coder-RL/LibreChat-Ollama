#!/bin/bash

# Project Directory: /Users/robertlee/GitHubProjects/ollama-inference-app/scripts

echo "📋 Running Phase 8 Batch 1 tests (Core Failures Handling)..."

# Run the test using unittest
cd /Users/robertlee/GitHubProjects/ollama-inference-app
python3 -m unittest tests.test_phase8_batch1_httpx

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All Phase 8 Batch 1 tests passed successfully!"
else
    echo "❌ Some Phase 8 Batch 1 tests failed. Check the logs above."
fi

exit $exit_code
