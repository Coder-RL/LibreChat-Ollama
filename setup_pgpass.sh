#!/bin/bash

# Script to securely set up PostgreSQL password in .pgpass file
# This avoids storing passwords in environment files

# Check if password is provided as argument
if [ -z "$1" ]; then
  echo "Usage: $0 <your_postgres_password>"
  echo "Example: $0 my_secure_password"
  exit 1
fi

PASSWORD=$1

# Create or update .pgpass file
PGPASS_FILE=~/.pgpass
PGPASS_ENTRY="localhost:5432:ollama_ai_db:ollama_app:$PASSWORD"

# Check if .pgpass exists
if [ -f "$PGPASS_FILE" ]; then
  # Check if entry already exists
  if grep -q "localhost:5432:ollama_ai_db:ollama_app:" "$PGPASS_FILE"; then
    # Update existing entry
    sed -i.bak "s|localhost:5432:ollama_ai_db:ollama_app:.*|$PGPASS_ENTRY|" "$PGPASS_FILE"
    echo "✅ Updated existing entry in $PGPASS_FILE"
  else
    # Append new entry
    echo "$PGPASS_ENTRY" >> "$PGPASS_FILE"
    echo "✅ Added new entry to $PGPASS_FILE"
  fi
else
  # Create new file with entry
  echo "$PGPASS_ENTRY" > "$PGPASS_FILE"
  echo "✅ Created $PGPASS_FILE with entry"
fi

# Set correct permissions
chmod 600 "$PGPASS_FILE"
echo "✅ Set permissions to 600 on $PGPASS_FILE"

echo "🔐 PostgreSQL password securely configured in $PGPASS_FILE"
echo "🚀 You can now run LibreChat-Ollama with RAG without exposing passwords in config files"
