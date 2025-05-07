#!/bin/bash

# === Config ===
API_URL="http://localhost:5110"
LOG_FILE="rag_test.log"
EXPECTED_VECTOR_DIM=3072
HTTP_TIMEOUT=10

# === Helper Functions ===
check_status_code() {
  local status_code=$1
  local endpoint=$2
  
  if [[ $status_code -ge 500 ]]; then
    echo "❌ ERROR: Server error (5xx) detected for $endpoint - Status code: $status_code" | tee -a "$LOG_FILE"
    echo "⚠️ Aborting tests due to server error" | tee -a "$LOG_FILE"
    exit 1
  elif [[ $status_code -ge 400 ]]; then
    echo "❌ ERROR: Client error (4xx) detected for $endpoint - Status code: $status_code" | tee -a "$LOG_FILE"
    return 1
  elif [[ $status_code -ne 200 ]]; then
    echo "⚠️ WARNING: Unexpected status code for $endpoint - Status code: $status_code" | tee -a "$LOG_FILE"
    return 1
  fi
  
  return 0
}

check_service_availability() {
  # Check if Ollama is running
  if ! curl -s --connect-timeout 5 "http://localhost:11434/api/version" > /dev/null; then
    echo "❌ ERROR: Ollama service is not available at http://localhost:11434" | tee -a "$LOG_FILE"
    echo "⚠️ Aborting tests - Ollama must be running" | tee -a "$LOG_FILE"
    exit 1
  fi
  
  # Check if RAG API is running
  if ! curl -s --connect-timeout 5 "$API_URL/health" > /dev/null; then
    echo "❌ ERROR: RAG API service is not available at $API_URL" | tee -a "$LOG_FILE"
    echo "⚠️ Aborting tests - RAG API must be running" | tee -a "$LOG_FILE"
    exit 1
  fi
  
  echo "✅ All required services are available" | tee -a "$LOG_FILE"
}

# === Setup Log Header ===
echo "🧪 RAG API Test Run — $(date)" | tee -a "$LOG_FILE"
echo "===============================" | tee -a "$LOG_FILE"

# === Check Services ===
echo -e "\n🔍 Checking service availability..." | tee -a "$LOG_FILE"
check_service_availability

# === Test /embed ===
echo -e "\n🔹 Testing /embed endpoint..." | tee -a "$LOG_FILE"
echo "📤 Request:" | tee -a "$LOG_FILE"
echo '{"text": "Sample embedding test"}' | tee -a "$LOG_FILE"

# Use a temporary file to capture both status code and response
EMBED_RESPONSE=$(mktemp)
HTTP_STATUS=$(curl -s -w "%{http_code}" -X POST "$API_URL/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "Sample embedding test"}' \
  -m $HTTP_TIMEOUT \
  -o "$EMBED_RESPONSE")

echo "📥 Response (Status: $HTTP_STATUS):" | tee -a "$LOG_FILE"
cat "$EMBED_RESPONSE" | jq '.' | tee -a "$LOG_FILE" 2>&1

# Check status code
if check_status_code "$HTTP_STATUS" "/embed"; then
  # Verify embedding dimension
  VECTOR_DIM=$(cat "$EMBED_RESPONSE" | jq '.embedding | length')
  echo "📏 Embedding dimension: $VECTOR_DIM" | tee -a "$LOG_FILE"
  
  if [[ "$VECTOR_DIM" -eq "$EXPECTED_VECTOR_DIM" ]]; then
    echo "✅ Embedding dimension matches expected value ($EXPECTED_VECTOR_DIM)" | tee -a "$LOG_FILE"
  else
    echo "❌ ERROR: Embedding dimension ($VECTOR_DIM) does not match expected value ($EXPECTED_VECTOR_DIM)" | tee -a "$LOG_FILE"
  fi
else
  echo "❌ Failed to get valid response from /embed endpoint" | tee -a "$LOG_FILE"
fi

# === Test /rag/query ===
echo -e "\n🔹 Testing /rag/query endpoint..." | tee -a "$LOG_FILE"
echo "📤 Request:" | tee -a "$LOG_FILE"
echo '{
  "query": "What is vector search?",
  "top_k": 3
}' | tee -a "$LOG_FILE"

# Use a temporary file to capture both status code and response
QUERY_RESPONSE=$(mktemp)
HTTP_STATUS=$(curl -s -w "%{http_code}" -X POST "$API_URL/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is vector search?",
    "top_k": 3
  }' \
  -m $HTTP_TIMEOUT \
  -o "$QUERY_RESPONSE")

echo "📥 Response (Status: $HTTP_STATUS):" | tee -a "$LOG_FILE"
cat "$QUERY_RESPONSE" | jq '.' | tee -a "$LOG_FILE" 2>&1

# Check status code
if check_status_code "$HTTP_STATUS" "/rag/query"; then
  # Check if results are present
  RESULTS_COUNT=$(cat "$QUERY_RESPONSE" | jq '.results | length')
  echo "📊 Results count: $RESULTS_COUNT" | tee -a "$LOG_FILE"
  
  if [[ "$RESULTS_COUNT" -gt 0 ]]; then
    echo "✅ Query returned results" | tee -a "$LOG_FILE"
  else
    echo "⚠️ WARNING: Query returned no results. This may be normal if no documents have been indexed." | tee -a "$LOG_FILE"
  fi
else
  echo "❌ Failed to get valid response from /rag/query endpoint" | tee -a "$LOG_FILE"
fi

# Clean up temporary files
rm -f "$EMBED_RESPONSE" "$QUERY_RESPONSE"

# === Footer ===
echo -e "\n✅ Test completed at $(date)\n\n" | tee -a "$LOG_FILE"

# === Done ===
echo "📝 Results saved to $LOG_FILE"
