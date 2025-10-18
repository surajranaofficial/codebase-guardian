#!/bin/bash

# Quick Test Script for Codebase Guardian
# Usage: bash quick_test.sh

API_URL="https://i65gy3w2nh.execute-api.eu-west-2.amazonaws.com/Prod/webhook/"

echo "=================================="
echo "🧪 Codebase Guardian Quick Test"
echo "=================================="
echo ""

# Test 1: Simple Python Code Review
echo "Test 1: Basic Python Review..."
echo "-------------------------------"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "--- a/main.py\n+++ b/main.py\n@@ -1,3 +1,5 @@\n def hello():\n-    print(\"Hello\")\n+    name = input(\"Name: \")\n+    print(\"Hello \" + name)\n",
    "format": "enhanced"
  }' | python3 -m json.tool

echo ""
echo ""

# Test 2: Secrets Detection
echo "Test 2: Secrets Detection..."
echo "----------------------------"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "--- a/config.py\n+++ b/config.py\n@@ -1,2 +1,3 @@\n # Config\n-API_KEY = \"test\"\n+AWS_KEY = \"AKIAIOSFODNN7EXAMPLE\"\n+SECRET = \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\"\n",
    "format": "enhanced",
    "include_metrics": true
  }' | python3 -m json.tool

echo ""
echo ""
echo "✅ Tests Complete!"
