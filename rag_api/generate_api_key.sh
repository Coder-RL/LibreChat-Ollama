#!/bin/bash

# Script to generate a secure API key and update the .env file
# Usage: ./generate_api_key.sh [key_length]

# Default key length
KEY_LENGTH=${1:-32}

# Validate input
if ! [[ "$KEY_LENGTH" =~ ^[0-9]+$ ]] || [ "$KEY_LENGTH" -lt 16 ] || [ "$KEY_LENGTH" -gt 128 ]; then
    echo "❌ Error: Key length must be a number between 16 and 128"
    echo "Usage: $0 [key_length]"
    echo "Example: $0 32"
    exit 1
fi

# Generate a secure random API key
if command -v openssl &> /dev/null; then
    # Use OpenSSL if available (more secure)
    API_KEY=$(openssl rand -base64 $((KEY_LENGTH * 3/4)) | tr -d '/+=' | cut -c1-$KEY_LENGTH)
elif command -v dd &> /dev/null && [ -f /dev/urandom ]; then
    # Fallback to /dev/urandom
    API_KEY=$(dd if=/dev/urandom bs=1 count=$((KEY_LENGTH * 3/4)) 2>/dev/null | base64 | tr -d '/+=' | cut -c1-$KEY_LENGTH)
else
    # Last resort (less secure)
    API_KEY=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w $KEY_LENGTH | head -n 1)
fi

# Check if API key was generated
if [ -z "$API_KEY" ]; then
    echo "❌ Error: Failed to generate API key"
    exit 1
fi

# Update .env file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: $ENV_FILE not found"
    exit 1
fi

# Check if RAG_API_KEY already exists in .env
if grep -q "^RAG_API_KEY=" "$ENV_FILE"; then
    # Update existing key
    sed -i.bak "s/^RAG_API_KEY=.*/RAG_API_KEY=$API_KEY/" "$ENV_FILE"
    echo "✅ Updated existing RAG_API_KEY in $ENV_FILE"
else
    # Add new key
    echo "RAG_API_KEY=$API_KEY" >> "$ENV_FILE"
    echo "✅ Added new RAG_API_KEY to $ENV_FILE"
fi

# Update test script
TEST_SCRIPT="test_rag_api.sh"
if [ -f "$TEST_SCRIPT" ]; then
    sed -i.bak "s/^API_KEY=.*/API_KEY=\"$API_KEY\"/" "$TEST_SCRIPT"
    echo "✅ Updated API_KEY in $TEST_SCRIPT"
fi

# Clean up backup files
rm -f "$ENV_FILE.bak" "$TEST_SCRIPT.bak"

# Display the new key
echo "🔐 New API Key: $API_KEY"
echo "🔒 Keep this key secure and don't share it!"
echo "📝 The key has been saved to $ENV_FILE and updated in $TEST_SCRIPT"
