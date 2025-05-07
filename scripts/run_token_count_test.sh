#!/bin/bash

echo "🚀 Running Token Count Storage Test..."

# Run the test using Python
cd "$(dirname "$0")/.."
python tests/test_token_count_storage.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ Token Count Storage Test passed successfully!"
else
    echo "❌ Token Count Storage Test failed. Check the logs above."
fi

exit $exit_code