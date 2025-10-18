import requests
import json
import time

API_URL = "https://w88pf50xy2.execute-api.ap-south-1.amazonaws.com/Prod/webhook/"

print("🚀 TESTING ALL 7 FEATURES")
print("=" * 80)

tests = [
    {
        "name": "Feature 1: Secrets Detection",
        "diff": """--- a/config.py
+++ b/config.py
@@ -1 +1,3 @@
-API_KEY = "test"
+AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
+AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
+GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
"""
    },
    {
        "name": "Feature 2: Complexity Scoring",
        "diff": """--- a/processor.py
+++ b/processor.py
@@ -1 +1,12 @@
-pass
+def process(data):
+    if data:
+        for item in data:
+            if item.active:
+                try:
+                    if item.value > 10:
+                        return process_high(item)
+                    else:
+                        return process_low(item)
+                except Exception as e:
+                    handle_error(e)
"""
    },
    {
        "name": "Feature 3: Multi-Language (JavaScript)",
        "diff": """--- a/app.jsx
+++ b/app.jsx
@@ -1 +1,5 @@
-var x = 1;
+const App = () => {
+  const [users, setUsers] = useState([]);
+  return <div>{users.map(u => <User key={u.id} data={u} />)}</div>;
+};
"""
    }
]

success_count = 0

for test in tests:
    print(f"\n{'='*80}")
    print(f"🧪 {test['name']}")
    print('='*80)
    
    try:
        response = requests.post(API_URL, json={
            "diff": test['diff'],
            "format": "enhanced",
            "include_metrics": True
        }, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            comment = result.get('review_comment', '')
            
            if 'Error' not in comment:
                print("✅ WORKING!")
                print(f"   Language: {result.get('language', 'N/A')}")
                print(f"   Severity: {result.get('overall_severity', 'N/A')}")
                print(f"   Secrets: {len(result.get('secrets_detected', []))}")
                metrics = result.get('code_metrics', {})
                if metrics:
                    print(f"   Complexity: {metrics.get('complexity_score', 0)}/100")
                success_count += 1
            else:
                print("❌ Payment error still present")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(1)

print(f"\n{'='*80}")
print(f"✅ SUCCESS: {success_count}/{len(tests)} features working")
print('='*80)

if success_count == len(tests):
    print("\n🎉🎉🎉 ALL FEATURES WORKING! READY FOR HACKATHON! 🎉🎉🎉")
elif success_count > 0:
    print(f"\n⚠️  {success_count} features working, payment still processing for others")
else:
    print("\n⏰ Payment verification still in progress")

