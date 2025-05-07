#!/bin/bash
# Run all persona validation scripts
# This script runs both the Python and jq validation scripts

echo "🔍 Running comprehensive persona validation..."
echo "=================================================================================="

# Run the Python validation script
echo "🐍 Running Python validation..."
python3 scripts/validate_personas_v2.py
PYTHON_RESULT=$?

echo ""
echo "=================================================================================="

# Run the jq validation script
echo "🔧 Running jq validation..."
./scripts/verify_personas_jq.sh
JQ_RESULT=$?

echo ""
echo "=================================================================================="

# Print summary
if [ $PYTHON_RESULT -eq 0 ] && [ $JQ_RESULT -eq 0 ]; then
    echo "🎉 SUCCESS! All persona files passed both Python and jq validation."
    exit 0
else
    echo "⚠️ FAILURE! Some persona files failed validation."
    echo "   Python validation: $([ $PYTHON_RESULT -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
    echo "   jq validation: $([ $JQ_RESULT -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
    exit 1
fi
