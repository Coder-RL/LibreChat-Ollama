#!/bin/bash
# Verify persona JSON files using jq
# This script checks that all persona files:
# 1. Have valid JSON syntax
# 2. Contain <system> tags (not <s> tags)
# 3. Have all required templates

# Set the personas directory
PERSONAS_DIR="app/personas"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is not installed. Please install it first."
    echo "   macOS: brew install jq"
    echo "   Ubuntu/Debian: apt-get install jq"
    exit 1
fi

# Count the number of persona files
NUM_FILES=$(find "$PERSONAS_DIR" -name "*.json" | wc -l)
echo "🔍 Verifying $NUM_FILES persona files in $PERSONAS_DIR using jq..."
echo "--------------------------------------------------------------------------------"

# Track validation results
VALID_COUNT=0
INVALID_COUNT=0

# Check each persona file
for FILE in "$PERSONAS_DIR"/*.json; do
    FILENAME=$(basename "$FILE")
    
    # Check if the file is valid JSON
    if ! jq empty "$FILE" 2>/dev/null; then
        echo "❌ $FILENAME — Invalid JSON syntax"
        INVALID_COUNT=$((INVALID_COUNT + 1))
        continue
    fi
    
    # Check if the file has templates
    if ! jq -e 'has("templates")' "$FILE" >/dev/null 2>&1; then
        echo "❌ $FILENAME — Missing 'templates' field"
        INVALID_COUNT=$((INVALID_COUNT + 1))
        continue
    fi
    
    # Check if the default template exists and contains <system> tags
    if ! jq -e '.templates.default' "$FILE" >/dev/null 2>&1; then
        echo "❌ $FILENAME — Missing 'default' template"
        INVALID_COUNT=$((INVALID_COUNT + 1))
        continue
    fi
    
    # Check if the default template contains <system> tags
    if ! jq -e '.templates.default | contains("<system>")' "$FILE" >/dev/null 2>&1; then
        echo "❌ $FILENAME — Default template does not contain <system> tags"
        INVALID_COUNT=$((INVALID_COUNT + 1))
        continue
    fi
    
    # Check if the default template contains <s> tags (should not)
    if jq -e '.templates.default | contains("<s>")' "$FILE" >/dev/null 2>&1; then
        echo "❌ $FILENAME — Default template contains deprecated <s> tags"
        INVALID_COUNT=$((INVALID_COUNT + 1))
        continue
    fi
    
    # Check if the code template exists
    if ! jq -e '.templates.code' "$FILE" >/dev/null 2>&1; then
        echo "❌ $FILENAME — Missing 'code' template"
        INVALID_COUNT=$((INVALID_COUNT + 1))
        continue
    fi
    
    # Check if the explanation template exists
    if ! jq -e '.templates.explanation' "$FILE" >/dev/null 2>&1; then
        echo "❌ $FILENAME — Missing 'explanation' template"
        INVALID_COUNT=$((INVALID_COUNT + 1))
        continue
    fi
    
    # All checks passed
    echo "✅ $FILENAME — Passed all jq validation checks"
    VALID_COUNT=$((VALID_COUNT + 1))
done

echo "--------------------------------------------------------------------------------"

# Print summary
if [ $INVALID_COUNT -eq 0 ]; then
    echo "🎉 Success! All $VALID_COUNT persona files passed jq validation."
    exit 0
else
    echo "⚠️ Found $INVALID_COUNT invalid persona files. Please fix the issues above."
    exit 1
fi
