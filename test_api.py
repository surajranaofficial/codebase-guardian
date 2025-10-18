import requests
import json

# API URL from the deployment output
API_URL = "https://w88pf50xy2.execute-api.ap-south-1.amazonaws.com/Prod/webhook/"

# The same diff we want to send for review
CODE_DIFF = """--- a/main.py
+++ b/main.py
@@ -1,4 +1,5 @@
 def get_greeting(name):
-    return "Hello " + name
+    if name:
+        return "Hello " + name
+    return "Hello there"
"""

# The JSON payload to send
PAYLOAD = {
    "diff": CODE_DIFF
}

def test_code_review_api():
    """Sends a test request to the deployed Code Review API."""
    print(f"Sending POST request to: {API_URL}")
    print("Payload:")
    print(json.dumps(PAYLOAD, indent=2))

    try:
        response = requests.post(API_URL, json=PAYLOAD, timeout=60)

        print(f"\n--- Response ---")
        print(f"Status Code: {response.status_code}")

        # Try to parse and print the JSON response body
        try:
            response_json = response.json()
            print("Response JSON:")
            # Pretty-print the JSON
            print(json.dumps(response_json, indent=2))

            # Specifically print the review comment if it exists
            if 'review_comment' in response_json:
                print("\n--- AI Review Comment ---")
                print(response_json['review_comment'])

        except json.JSONDecodeError:
            print("Response Body (not valid JSON):")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    test_code_review_api()

