#!/bin/bash
# Comprehensive Test Suite for Codebase Guardian

API_URL="https://i65gy3w2nh.execute-api.eu-west-2.amazonaws.com/Prod/webhook/"

echo "🧪 COMPREHENSIVE TEST SUITE - Codebase Guardian"
echo "=================================================="
echo ""

test_count=0
pass_count=0
fail_count=0

# Function to run a test
run_test() {
    local test_name="$1"
    local payload_file="$2"
    
    test_count=$((test_count + 1))
    echo "Test #$test_count: $test_name"
    echo "-------------------------------------------"
    
    RESPONSE=$(curl -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -d @"$payload_file" \
      -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}")
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    TIME=$(echo "$RESPONSE" | grep "TIME:" | cut -d: -f2)
    JSON=$(echo "$RESPONSE" | sed '/HTTP_CODE:/,$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "$JSON" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    severity = data.get('overall_severity', 'N/A')
    language = data.get('language', 'unknown')
    issues = len(data.get('issues', []))
    fixes = len(data.get('fixes', []))
    secrets = len(data.get('secrets_detected', []))
    metrics = data.get('code_metrics', {})
    
    print(f'  ✅ Status: SUCCESS')
    print(f'  📝 Language: {language}')
    print(f'  ⚠️  Severity: {severity}')
    print(f'  🔍 Issues: {issues}')
    print(f'  🔧 Fixes: {fixes}')
    print(f'  �� Secrets: {secrets}')
    print(f'  📊 Complexity: {metrics.get(\"complexity_score\", 0)}/100')
    print(f'  ⏱️  Time: ${TIME}s')
    print()
    
    if issues > 0:
        print('  📋 Top Issues:')
        for i, issue in enumerate(data.get('issues', [])[:3], 1):
            print(f'     {i}. [{issue.get(\"severity\")}] {issue.get(\"title\")}')
    
    exit(0)
except Exception as e:
    print(f'  ❌ Parse Error: {e}')
    exit(1)
"
        if [ $? -eq 0 ]; then
            pass_count=$((pass_count + 1))
            echo "  ✓ PASSED"
        else
            fail_count=$((fail_count + 1))
            echo "  ✗ FAILED"
        fi
    else
        fail_count=$((fail_count + 1))
        echo "  ✗ FAILED (HTTP $HTTP_CODE)"
    fi
    
    echo ""
}

# Create test payloads
mkdir -p /tmp/codebase_tests

# Test 1: Basic Python
cat > /tmp/codebase_tests/test1.json << 'PAYLOAD'
{
  "diff": "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,4 @@\n def greet():\n-    print(\"Hello\")\n+    name = input(\"Enter name: \")\n+    print(f\"Hello {name}!\")",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Test 2: JavaScript eval
cat > /tmp/codebase_tests/test2.json << 'PAYLOAD'
{
  "diff": "--- a/script.js\n+++ b/script.js\n@@ -1,3 +1,5 @@\n function calculate(expr) {\n-    return 0;\n+    // WARNING: Using eval\n+    return eval(expr);\n }",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Test 3: SQL Injection
cat > /tmp/codebase_tests/test3.json << 'PAYLOAD'
{
  "diff": "--- a/database.py\n+++ b/database.py\n@@ -1,3 +1,5 @@\n def get_user(username):\n-    return None\n+    query = \"SELECT * FROM users WHERE name = '\" + username + \"'\"\n+    return execute_query(query)",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Test 4: Hardcoded Secret (using obfuscated test key)
cat > /tmp/codebase_tests/test4.json << 'PAYLOAD'
{
  "diff": "--- a/config.py\n+++ b/config.py\n@@ -1,2 +1,3 @@\n # Config\n-API_KEY = None\n+API_KEY = \"AKIA\" + \"IOSFODNN7EXAMPLE\"",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Test 5: Complex Algorithm
cat > /tmp/codebase_tests/test5.json << 'PAYLOAD'
{
  "diff": "--- a/algo.py\n+++ b/algo.py\n@@ -1,2 +1,12 @@\n def process(data):\n-    return data\n+    result = []\n+    for i in data:\n+        if i > 0:\n+            for j in range(i):\n+                if j % 2 == 0:\n+                    try:\n+                        result.append(j * 2)\n+                    except:\n+                        pass\n+    return result",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Test 6: Go Error Handling
cat > /tmp/codebase_tests/test6.json << 'PAYLOAD'
{
  "diff": "--- a/main.go\n+++ b/main.go\n@@ -1,3 +1,5 @@\n func readFile(path string) string {\n-    return \"\"\n+    data, _ := ioutil.ReadFile(path)\n+    return string(data)\n }",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Test 7: Java Memory
cat > /tmp/codebase_tests/test7.json << 'PAYLOAD'
{
  "diff": "--- a/Cache.java\n+++ b/Cache.java\n@@ -1,3 +1,7 @@\n public class Cache {\n-    private Map<String, Object> data = new HashMap<>();\n+    private static Map<String, Object> data = new HashMap<>();\n+    public void add(String key, Object value) {\n+        data.put(key, value);\n+    }\n }",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Test 8: Clean Code
cat > /tmp/codebase_tests/test8.json << 'PAYLOAD'
{
  "diff": "--- a/utils.py\n+++ b/utils.py\n@@ -1,2 +1,10 @@\n # Utils\n-pass\n+from typing import List\n+\n+def filter_positive(numbers: List[int]) -> List[int]:\n+    \"\"\"Filter positive numbers.\"\"\"\n+    return [n for n in numbers if n > 0]",
  "format": "enhanced",
  "include_metrics": true
}
PAYLOAD

# Run tests
run_test "Basic Python Input Function" "/tmp/codebase_tests/test1.json"
run_test "JavaScript eval() Security Risk" "/tmp/codebase_tests/test2.json"
run_test "SQL Injection Vulnerability" "/tmp/codebase_tests/test3.json"
run_test "Hardcoded API Key Detection" "/tmp/codebase_tests/test4.json"
run_test "Complex Nested Algorithm" "/tmp/codebase_tests/test5.json"
run_test "Go Error Handling" "/tmp/codebase_tests/test6.json"
run_test "Java Memory Leak Risk" "/tmp/codebase_tests/test7.json"
run_test "Well-Written Clean Code" "/tmp/codebase_tests/test8.json"

# Cleanup
rm -rf /tmp/codebase_tests

# Summary
echo "=================================================="
echo "📊 TEST SUMMARY"
echo "=================================================="
echo "Total Tests: $test_count"
echo "Passed: $pass_count"
echo "Failed: $fail_count"
echo ""

if [ $fail_count -eq 0 ]; then
    echo "✅ ALL TESTS PASSED! 🎉"
    exit 0
else
    echo "⚠️  Some tests failed."
    exit 1
fi
