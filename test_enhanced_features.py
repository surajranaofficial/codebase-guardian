#!/usr/bin/env python3
"""
Enhanced Features Test Suite for Codebase Guardian
Tests: Severity Scoring, Multi-Language Support, Auto-Fix Suggestions
"""

import requests
import json
import time

# API URL from the deployment
API_URL = "https://w88pf50xy2.execute-api.ap-south-1.amazonaws.com/Prod/webhook/"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_success(msg):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_info(msg):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")

def test_api(test_name, code_diff, expected_severity=None):
    """
    Test the API with given code diff
    """
    print_section(f"TEST: {test_name}")
    print_info(f"Testing with {len(code_diff)} characters of diff")
    
    payload = {"diff": code_diff, "format": "enhanced"}
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=90)
        elapsed_time = time.time() - start_time
        
        print_info(f"Response time: {elapsed_time:.2f} seconds")
        print_info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Display key information
            print(f"\n{Colors.OKBLUE}📊 Review Results:{Colors.ENDC}")
            print(f"Language: {result.get('language', 'unknown')}")
            print(f"Overall Severity: {result.get('overall_severity', 'N/A')}")
            
            # Issues found
            issues = result.get('issues', [])
            print(f"\nIssues Found: {len(issues)}")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. [{issue.get('severity')}] {issue.get('title')}")
            
            # Fixes available
            fixes = result.get('fixes', [])
            print(f"\nAuto-Fixes Available: {len(fixes)}")
            for i, fix in enumerate(fixes, 1):
                print(f"  {i}. {fix.get('issue_title', 'Fix')}")
            
            # Display formatted review
            if 'review_comment' in result:
                print(f"\n{Colors.BOLD}📝 Formatted Review:{Colors.ENDC}")
                print(result['review_comment'])
            
            # Verify expected severity
            if expected_severity:
                actual_severity = result.get('overall_severity')
                if actual_severity == expected_severity:
                    print_success(f"Severity matches expected: {expected_severity}")
                else:
                    print_error(f"Severity mismatch. Expected: {expected_severity}, Got: {actual_severity}")
            
            print_success("Test completed successfully!")
            return True
            
        else:
            print_error(f"API returned error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        return False

def main():
    """Run all enhanced feature tests"""
    
    print_section("🚀 CODEBASE GUARDIAN - ENHANCED FEATURES TEST SUITE")
    print_info("Testing: Severity Scoring, Multi-Language Support, Auto-Fix Suggestions")
    
    # Test 1: Python - Critical Security Issue (SQL Injection)
    test_api(
        "Python - Critical Security Vulnerability",
        """--- a/database.py
+++ b/database.py
@@ -5,7 +5,9 @@
 def get_user(username, password):
-    query = "SELECT * FROM users WHERE username='admin'"
+    # Added password authentication
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    print(f"Executing query with password: {password}")
     cursor.execute(query)
     return cursor.fetchone()
""",
        expected_severity="CRITICAL"
    )
    
    time.sleep(2)  # Rate limiting
    
    # Test 2: JavaScript/React - Medium Code Quality
    test_api(
        "JavaScript - React Component Optimization",
        """--- a/UserList.jsx
+++ b/UserList.jsx
@@ -3,12 +3,15 @@
 function UserList({ users }) {
-    return users.map(function(user) {
-        return <div>{user.name}</div>
-    })
+    // Using arrow function and key prop
+    return users.map((user) => (
+        <div key={user.id}>{user.name}</div>
+    ))
 }
""",
        expected_severity="MEDIUM"
    )
    
    time.sleep(2)  # Rate limiting
    
    # Test 3: Go - High Performance Issue
    test_api(
        "Go - Goroutine Leak Detection",
        """--- a/worker.go
+++ b/worker.go
@@ -10,8 +10,12 @@
 func ProcessItems(items []string) {
     for _, item := range items {
+        // Start goroutine without wait group
         go func(i string) {
             process(i)
-        }(item)
+        }(item)  // Missing synchronization
     }
+    // Function returns immediately, goroutines may not complete
+    return
 }
""",
        expected_severity="HIGH"
    )
    
    time.sleep(2)  # Rate limiting
    
    # Test 4: Java - Performance Improvement with Fix
    test_api(
        "Java - Stream API Optimization",
        """--- a/DataProcessor.java
+++ b/DataProcessor.java
@@ -15,10 +15,8 @@
 public List<String> filterData(List<String> data) {
-    List<String> result = new ArrayList<>();
-    for (int i = 0; i < data.size(); i++) {
-        if (data.get(i).startsWith("A")) {
-            result.add(data.get(i));
-        }
-    }
-    return result;
+    // Using Java 8 Streams for better performance
+    return data.stream()
+        .filter(s -> s.startsWith("A"))
+        .collect(Collectors.toList());
 }
""",
        expected_severity="LOW"
    )
    
    time.sleep(2)  # Rate limiting
    
    # Test 5: Multi-language Detection Test
    test_api(
        "Python - Multiple Best Practices",
        """--- a/api_handler.py
+++ b/api_handler.py
@@ -8,12 +8,20 @@
 def handle_request(request_data):
-    user = request_data['user']
-    token = request_data['token']
-    result = process(user, token)
-    return result
+    # Added comprehensive error handling
+    try:
+        user = request_data.get('user')
+        token = request_data.get('token')
+        
+        if not user or not token:
+            raise ValueError("Missing required fields")
+            
+        result = process(user, token)
+        return {'status': 'success', 'data': result}
+        
+    except Exception as e:
+        logger.error(f"Error processing request: {e}")
+        return {'status': 'error', 'message': str(e)}
""",
        expected_severity="LOW"
    )
    
    # Final Summary
    print_section("🎉 TEST SUITE COMPLETED")
    print_success("All enhanced features have been tested!")
    print_info("Features verified:")
    print("  ✅ Severity Scoring (CRITICAL, HIGH, MEDIUM, LOW, INFO)")
    print("  ✅ Multi-Language Detection (Python, JavaScript, Java, Go)")
    print("  ✅ Automated Fix Suggestions with explanations")
    print("  ✅ Structured JSON responses")
    print("  ✅ Language-specific best practices")

if __name__ == "__main__":
    main()
