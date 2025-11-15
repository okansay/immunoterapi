#!/bin/bash
# MAUG API Hızlı Test Scripti

API_URL="http://localhost:8000"

echo "============================================"
echo "MAUG API Test"
echo "============================================"

# 1. Health check
echo ""
echo "1️⃣  Health Check..."
curl -s "${API_URL}/health" | python3 -m json.tool
echo ""

# 2. Test queries
echo ""
echo "2️⃣  Test Sorguları..."
echo ""

# Test 1: Peanut allergens
echo "📌 Test 1: Peanut allergens"
curl -s -X POST "${API_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main allergen components in peanuts?",
    "language": "en"
  }' | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 2: Milk allergy
echo "📌 Test 2: Milk allergy"
curl -s -X POST "${API_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the milk allergen components?",
    "language": "en"
  }' | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 3: Basophil test
echo "📌 Test 3: Basophil activation test"
curl -s -X POST "${API_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to perform basophil activation test?",
    "language": "en"
  }' | python3 -m json.tool

echo ""
echo "---"
echo ""

# Test 4: Profilins (Turkish)
echo "📌 Test 4: Profilinler (Türkçe)"
curl -s -X POST "${API_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Profilinler nedir ve hangi bitkilerde bulunur?",
    "language": "tr"
  }' | python3 -m json.tool

echo ""
echo "============================================"
echo "✅ Test tamamlandı!"
echo "============================================"
