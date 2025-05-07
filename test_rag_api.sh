#!/bin/bash

echo "🔍 Testing RAG API on port 5110..."

echo "🧪 Step 1: /embed"
curl -s -X POST http://localhost:5110/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Sample embedding test"}' | jq

echo "🧪 Step 2: /rag/query"
curl -s -X POST http://localhost:5110/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is vector search?",
    "top_k": 3
  }' | jq
