#!/bin/bash
# Quick Test Command for Codebase Guardian

echo "🚀 Testing Codebase Guardian AI Agent"
echo "======================================"
echo ""

RESPONSE=$(curl -X POST "https://i65gy3w2nh.execute-api.eu-west-2.amazonaws.com/Prod/webhook/" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,4 @@\n def greet():\n-    print(\"Hello\")\n+    name = input(\"Enter name: \")\n+    print(f\"Hello {name}!\")",
    "format": "enhanced",
    "include_metrics": true
  }' \
  -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}")

# Extract HTTP code and time
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
TIME=$(echo "$RESPONSE" | grep "TIME:" | cut -d: -f2)

# Extract JSON (everything before HTTP_CODE line)
JSON=$(echo "$RESPONSE" | sed '/HTTP_CODE:/,$d')

echo "$JSON" | python3 -c "
import sys, json

data = json.load(sys.stdin)
print('✅ Status: SUCCESS')
print(f'📝 Language: {data.get(\"language\", \"unknown\")}')
print(f'⚠️  Severity: {data.get(\"overall_severity\", \"N/A\")}')
print(f'🔍 Issues: {len(data.get(\"issues\", []))}')
print(f'🔧 Fixes: {len(data.get(\"fixes\", []))}')
print(f'🔒 Secrets: {len(data.get(\"secrets_detected\", []))}')
print()

metrics = data.get('code_metrics', {})
if metrics:
    print('📊 Code Metrics:')
    print(f'   Lines Added: {metrics.get(\"lines_added\", 0)}')
    print(f'   Complexity: {metrics.get(\"complexity_score\", 0)}/100')
    print(f'   Risk: {metrics.get(\"risk_level\", \"N/A\")}')
    print()

issues = data.get('issues', [])
if issues:
    print('🔍 Issues Found:')
    for i, issue in enumerate(issues[:3], 1):
        print(f'   {i}. [{issue.get(\"severity\")}] {issue.get(\"title\")}')
"

echo ""
echo "⏱️  Response Time: ${TIME}s | HTTP: ${HTTP_CODE}"
echo "======================================"
echo "✅ Test Complete!"
