#!/bin/bash

# === Config ===
API_URL="http://localhost:5110"
API_KEY="supersecretapikey123"
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

# Track failures
failures=0

# === Check Services ===
echo -e "\n🔍 Checking service availability..." | tee -a "$LOG_FILE"
check_service_availability

# === Test /health ===
echo -e "\n🔹 Checking /health endpoint..." | tee -a "$LOG_FILE"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
echo "📥 Health status code: $HEALTH_STATUS" | tee -a "$LOG_FILE"

if [[ "$HEALTH_STATUS" -eq 200 ]]; then
  echo "✅ Health check passed" | tee -a "$LOG_FILE"
else
  echo "❌ Health check failed with status $HEALTH_STATUS" | tee -a "$LOG_FILE"
  ((failures++))
fi

# === Test /embed ===
echo -e "\n🔹 Testing /embed endpoint..." | tee -a "$LOG_FILE"
echo "📤 Request:" | tee -a "$LOG_FILE"
echo '{"text": "Sample embedding test"}' | tee -a "$LOG_FILE"

# Use a temporary file to capture both status code and response
EMBED_RESPONSE=$(mktemp)
HTTP_STATUS=$(curl -s -w "%{http_code}" -X POST "$API_URL/embed" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"text": "Sample embedding test"}' \
  -m $HTTP_TIMEOUT \
  -o "$EMBED_RESPONSE")

echo "📥 Response (Status: $HTTP_STATUS):" | tee -a "$LOG_FILE"
cat "$EMBED_RESPONSE" | jq '.' | tee -a "$LOG_FILE" 2>&1

# Check status code
if check_status_code "$HTTP_STATUS" "/embed"; then
  # Verify embedding dimension
  VECTOR_DIM=$(cat "$EMBED_RESPONSE" | jq '.dim')
  echo "📏 Embedding dimension: $VECTOR_DIM" | tee -a "$LOG_FILE"

  if [[ "$VECTOR_DIM" -eq "$EXPECTED_VECTOR_DIM" ]]; then
    echo "✅ Embedding dimension matches expected value ($EXPECTED_VECTOR_DIM)" | tee -a "$LOG_FILE"
  else
    echo "❌ ERROR: Embedding dimension ($VECTOR_DIM) does not match expected value ($EXPECTED_VECTOR_DIM)" | tee -a "$LOG_FILE"
    ((failures++))
  fi
else
  echo "❌ Failed to get valid response from /embed endpoint" | tee -a "$LOG_FILE"
  ((failures++))
fi

# === Test /embed with invalid API key ===
echo -e "\n🔹 Testing /embed with invalid API key (negative test)..." | tee -a "$LOG_FILE"
INVALID_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/embed" \
  -H "Content-Type: application/json" \
  -H "x-api-key: invalid_key" \
  -d '{"text": "Sample embedding test"}' \
  -m $HTTP_TIMEOUT)

echo "📥 Status code with invalid API key: $INVALID_STATUS" | tee -a "$LOG_FILE"
if [[ "$INVALID_STATUS" -eq 401 ]]; then
  echo "✅ Security check passed: Unauthorized access correctly rejected" | tee -a "$LOG_FILE"
else
  echo "❌ Security check failed: Expected 401, got $INVALID_STATUS" | tee -a "$LOG_FILE"
  ((failures++))
fi

# === Test rate limiting ===
echo -e "\n🔹 Testing rate limiting (negative test)..." | tee -a "$LOG_FILE"
echo "📤 Sending multiple requests to trigger rate limit..." | tee -a "$LOG_FILE"

# Function to check if rate limiting is working
test_rate_limit() {
  local endpoint=$1
  local limit=$2
  local status_codes=()

  echo "Testing rate limiting on $endpoint (limit: $limit/minute)..." | tee -a "$LOG_FILE"

  # Send requests until we hit the rate limit or exceed max attempts
  for i in $(seq 1 $((limit+5))); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL$endpoint" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -d '{"text": "Rate limit test", "query": "Rate limit test"}' \
      -m $HTTP_TIMEOUT)

    status_codes+=($STATUS)
    echo -n "." # Progress indicator

    # If we get a 429, rate limiting is working
    if [[ "$STATUS" -eq 429 ]]; then
      echo -e "\n✅ Rate limiting working correctly: got 429 Too Many Requests after $i requests" | tee -a "$LOG_FILE"
      return 0
    fi

    # Small delay to avoid overwhelming the server
    sleep 0.1
  done

  echo -e "\n❌ Failed to trigger rate limit after $((limit+5)) requests" | tee -a "$LOG_FILE"
  echo "Status codes: ${status_codes[*]}" | tee -a "$LOG_FILE"
  return 1
}

# Test rate limiting on /embed endpoint (10/minute)
if test_rate_limit "/embed" 10; then
  echo "✅ Rate limiting test passed for /embed" | tee -a "$LOG_FILE"
else
  echo "❌ Rate limiting test failed for /embed" | tee -a "$LOG_FILE"
  ((failures++))
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
  -H "x-api-key: $API_KEY" \
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

  if [[ "$RESULTS_COUNT" -eq 3 ]]; then
    echo "✅ Query returned expected number of results (3)" | tee -a "$LOG_FILE"
  else
    echo "❌ ERROR: Query returned $RESULTS_COUNT results, expected 3" | tee -a "$LOG_FILE"
    ((failures++))
  fi
else
  echo "❌ Failed to get valid response from /rag/query endpoint" | tee -a "$LOG_FILE"
  ((failures++))
fi

# Clean up temporary files
rm -f "$EMBED_RESPONSE" "$QUERY_RESPONSE"

# === Test token usage endpoint ===
echo -e "\n🔹 Testing /tokens/usage endpoint..." | tee -a "$LOG_FILE"
USAGE_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/tokens/usage" \
  -H "x-api-key: $API_KEY" \
  -m $HTTP_TIMEOUT)

USAGE_BODY=$(echo "$USAGE_RESPONSE" | head -n -1)
USAGE_STATUS=$(echo "$USAGE_RESPONSE" | tail -n1)

echo "📥 Status code: $USAGE_STATUS" | tee -a "$LOG_FILE"
if [[ "$USAGE_STATUS" -eq 200 ]]; then
  echo "✅ Token usage endpoint working" | tee -a "$LOG_FILE"
  echo "$USAGE_BODY" | jq '.' >> "$LOG_FILE"

  # Check if our token is in the response
  if echo "$USAGE_BODY" | jq -e '.tokens | length > 0' > /dev/null; then
    echo "✅ Token usage data returned" | tee -a "$LOG_FILE"
  else
    echo "❌ No token data returned" | tee -a "$LOG_FILE"
    ((failures++))
  fi
else
  echo "❌ Token usage endpoint failed with status $USAGE_STATUS" | tee -a "$LOG_FILE"
  ((failures++))
fi

# === Test security audit endpoint ===
echo -e "\n🔹 Testing /security/audit endpoint..." | tee -a "$LOG_FILE"
AUDIT_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/security/audit" \
  -H "x-api-key: $API_KEY" \
  -m $HTTP_TIMEOUT)

AUDIT_BODY=$(echo "$AUDIT_RESPONSE" | head -n -1)
AUDIT_STATUS=$(echo "$AUDIT_RESPONSE" | tail -n1)

echo "📥 Status code: $AUDIT_STATUS" | tee -a "$LOG_FILE"
if [[ "$AUDIT_STATUS" -eq 200 ]]; then
  echo "✅ Security audit endpoint working" | tee -a "$LOG_FILE"
  echo "$AUDIT_BODY" | jq '.' >> "$LOG_FILE"
else
  echo "❌ Security audit endpoint failed with status $AUDIT_STATUS" | tee -a "$LOG_FILE"
  ((failures++))
fi

# === Summary ===
echo -e "\n✅ Test completed at $(date)" | tee -a "$LOG_FILE"
if [[ "$failures" -eq 0 ]]; then
  echo "✅ ALL TESTS PASSED" | tee -a "$LOG_FILE"
  echo "✅ ALL TESTS PASSED"
else
  echo "❌ $failures TEST(S) FAILED" | tee -a "$LOG_FILE"
  echo "❌ $failures TEST(S) FAILED"
  exit 1
fi

# === Done ===
echo "📝 Results saved to $LOG_FILE"
