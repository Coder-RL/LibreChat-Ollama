#!/bin/bash

# Project Directory: /Users/robertlee/GitHubProjects/ollama-inference-app/scripts

echo "📋 Checking if Ollama Inference App server is running..."

# Check if FastAPI server is live
health=$(curl -s http://localhost:8000/api/health)

if [[ "$health" == *"postgresql\":\"ok"* && "$health" == *"opensearch\":\"ok"* && "$health" == *"ollama\":\"ok"* ]]; then
    echo "✅ Application health check passed."
else
    echo "❌ ERROR: Application server is not responding correctly or dependencies are unhealthy."
    echo "Health response: $health"
    echo "Aborting tests."
    exit 1
fi

echo "🚀 Running Phase 8C Batch 5 tests..."

# Run the test using unittest with verbose output
cd /Users/robertlee/GitHubProjects/ollama-inference-app
python -m unittest tests/test_inference_controller_phase8c_batch5.py -v

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All Phase 8C Batch 5 tests passed successfully!"
else
    echo "❌ Some Phase 8C Batch 5 tests failed. Check the logs above."
fi

exit $exit_code
