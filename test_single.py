#!/usr/bin/env python3
"""
Single Test - Quick verification
Usage: python test_single.py
"""

import requests
import json

API_URL = "https://w88pf50xy2.execute-api.ap-south-1.amazonaws.com/Prod/webhook/"

# Simple test diff
CODE_DIFF = """--- a/example.py
+++ b/example.py
@@ -1,3 +1,5 @@
 def greet(name):
-    return "Hello"
+    if name:
+        return f"Hello {name}"
+    return "Hello Guest"
"""

print("🧪 Testing Codebase Guardian API...")
print("=" * 60)

payload = {
    "diff": CODE_DIFF,
    "format": "enhanced",
    "include_metrics": True
}

try:
    print(f"\n📡 Sending request to: {API_URL}")
    print(f"📦 Payload size: {len(json.dumps(payload))} bytes")
    
    response = requests.post(API_URL, json=payload, timeout=30)
    
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"⏱️  Response Time: {response.elapsed.total_seconds():.2f}s")
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n" + "=" * 60)
        print("📊 REVIEW RESULTS")
        print("=" * 60)
        
        print(f"\n🌐 Language: {result.get('language', 'N/A')}")
        print(f"⚠️  Severity: {result.get('overall_severity', 'N/A')}")
        
        # Secrets
        secrets = result.get('secrets_detected', [])
        print(f"\n🔒 Secrets Found: {len(secrets)}")
        
        # Metrics
        metrics = result.get('code_metrics', {})
        if metrics:
            print(f"\n📈 Metrics:")
            print(f"   Lines Added: {metrics.get('lines_added', 0)}")
            print(f"   Complexity: {metrics.get('complexity_score', 0)}/100")
            print(f"   Risk Level: {metrics.get('risk_level', 'N/A')}")
        
        # Issues
        issues = result.get('issues', [])
        print(f"\n🔍 Issues: {len(issues)}")
        
        # Fixes
        fixes = result.get('fixes', [])
        print(f"🔧 Auto-Fixes: {len(fixes)}")
        
        # Full review
        if 'review_comment' in result:
            print("\n" + "=" * 60)
            print("📝 REVIEW COMMENT")
            print("=" * 60)
            print(result['review_comment'][:300] + "..." if len(result['review_comment']) > 300 else result['review_comment'])
        
        print("\n" + "=" * 60)
        print("✅ TEST PASSED!")
        print("=" * 60)
        
    else:
        print(f"\n❌ Error Response:")
        print(response.text)

except requests.exceptions.Timeout:
    print("\n⏰ Request timed out (>30s)")
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {e}")
except json.JSONDecodeError:
    print(f"\n❌ Invalid JSON response")
    print(response.text)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

print("\n")
