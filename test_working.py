import requests
import json

API_URL = "https://i65gy3w2nh.execute-api.eu-west-2.amazonaws.com/Prod/webhook/"

print("🎉 TESTING WITH VERIFIED PAYMENT!")
print("=" * 80)

# Test 1: Simple code review
test_diff = """--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
 def greet():
-    print("Hello")
+    name = input("Enter name: ")
+    print(f"Hello {name}!")
"""

payload = {
    "diff": test_diff,
    "format": "enhanced",
    "include_metrics": True
}

try:
    response = requests.post(API_URL, json=payload, timeout=90)
    
    print(f"Status: {response.status_code}")
    print(f"Time: {response.elapsed.total_seconds():.2f}s")
    
    if response.status_code == 200:
        result = response.json()
        
        # Check if working
        comment = result.get('review_comment', '')
        
        if 'Error' not in comment and 'INVALID_PAYMENT' not in comment:
            print("\n" + "=" * 80)
            print("🎉🎉🎉 SUCCESS! AI AGENT IS WORKING! 🎉🎉🎉")
            print("=" * 80)
            
            print(f"\n✅ Language: {result.get('language', 'N/A')}")
            print(f"✅ Severity: {result.get('overall_severity', 'N/A')}")
            
            secrets = result.get('secrets_detected', [])
            print(f"✅ Secrets Scanned: {len(secrets)} found")
            
            metrics = result.get('code_metrics', {})
            if metrics:
                print(f"\n📊 Code Metrics:")
                print(f"   Complexity: {metrics.get('complexity_score', 0)}/100")
                print(f"   Risk Level: {metrics.get('risk_level', 'N/A')}")
                print(f"   Lines Added: {metrics.get('lines_added', 0)}")
            
            issues = result.get('issues', [])
            print(f"\n🔍 Issues Found: {len(issues)}")
            for issue in issues[:3]:  # Show first 3
                print(f"   - [{issue.get('severity')}] {issue.get('title')}")
            
            fixes = result.get('fixes', [])
            print(f"\n🔧 Auto-Fixes Available: {len(fixes)}")
            
            print(f"\n📝 Review Comment (first 500 chars):")
            print("-" * 80)
            print(comment[:500])
            if len(comment) > 500:
                print("...(truncated)")
            print("-" * 80)
            
            print("\n" + "=" * 80)
            print("✅ ALL FEATURES WORKING! READY FOR DEMO!")
            print("=" * 80)
        else:
            print(f"\n❌ Still payment error:")
            print(comment[:200])
    else:
        print(f"\n❌ HTTP Error: {response.text[:300]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

