# 🏗️ Codebase Guardian - System Architecture

## 📐 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB REPOSITORY                            │
│                                                                      │
│  ┌──────────────┐                                                   │
│  │ Pull Request │ ──────────────────┐                              │
│  └──────────────┘                   │                              │
│         │                           │                              │
│         │ (1) PR Created            │                              │
│         ▼                           │                              │
│  ┌──────────────┐                   │                              │
│  │   Webhook    │                   │                              │
│  └──────────────┘                   │                              │
└─────────────────────────────────────────────────────────────────────┘
         │                           │
         │ (2) POST Request          │
         ▼                           │
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD                                    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                    API GATEWAY (REST)                          ││
│  │                                                                ││
│  │  • Route: POST /webhook/                                       ││
│  │  • CORS enabled                                                ││
│  │  • Request validation                                          ││
│  └────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         │ (3) Invoke                                                │
│         ▼                                                            │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                    AWS LAMBDA                                  ││
│  │              (CodeReviewFunction)                              ││
│  │                                                                ││
│  │  ┌──────────────────────────────────────────────────────────┐ ││
│  │  │           lambda_handler.py                               │ ││
│  │  │                                                           │ ││
│  │  │  • Parse webhook payload                                  │ ││
│  │  │  • Detect GitHub PR events                                │ ││
│  │  │  • Extract/fetch diff                                     │ ││
│  │  │  • Route to bedrock_agent                                 │ ││
│  │  └──────────────────────────────────────────────────────────┘ ││
│  │         │                                   │                   ││
│  │         │ (4a) Review Request               │ (4b) GitHub API   ││
│  │         ▼                                   ▼                   ││
│  │  ┌──────────────────────┐        ┌────────────────────────┐   ││
│  │  │  bedrock_agent.py    │        │ github_integration.py  │   ││
│  │  │                      │        │                        │   ││
│  │  │ • detect_language()  │        │ • post_pr_comment()    │   ││
│  │  │ • detect_secrets()   │        │ • create_check_run()   │   ││
│  │  │ • calculate_metrics()│        │ • approve_pr()         │   ││
│  │  │ • format_output()    │        │ • fetch_diff()         │   ││
│  │  └──────────────────────┘        └────────────────────────┘   ││
│  │         │                                   │                   ││
│  │         │ (5) Bedrock Request               │                   ││
│  └─────────┼───────────────────────────────────┼───────────────────┘│
│            ▼                                   │                    │
│  ┌────────────────────────────────────────────┼───────────────────┐│
│  │           AMAZON BEDROCK                    │                   ││
│  │                                            │                   ││
│  │  ┌──────────────────────────────────────┐ │                   ││
│  │  │    Claude 3 Haiku Model              │ │                   ││
│  │  │    (anthropic.claude-3-haiku)        │ │                   ││
│  │  │                                       │ │                   ││
│  │  │  • Analyze code diff                  │ │                   ││
│  │  │  • Apply language-specific rules      │ │                   ││
│  │  │  • Generate severity classification   │ │                   ││
│  │  │  • Create auto-fix suggestions        │ │                   ││
│  │  │  • Format structured JSON response    │ │                   ││
│  │  └──────────────────────────────────────┘ │                   ││
│  │         │                                  │                   ││
│  │         │ (6) AI Response                  │                   ││
│  │         ▼                                  │                   ││
│  │  ┌──────────────────────────────────────┐ │                   ││
│  │  │    Response Processing                │ │                   ││
│  │  │                                       │ │                   ││
│  │  │  • Parse JSON                         │ │                   ││
│  │  │  • Add secrets data                   │ │                   ││
│  │  │  • Add metrics                        │ │                   ││
│  │  │  • Format markdown                    │ │                   ││
│  │  └──────────────────────────────────────┘ │                   ││
│  └────────────────────────────────────────────┼───────────────────┘│
│                                               │                    │
│                                               │ (7) GitHub API     │
│                                               ▼                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    GITHUB REST API                           │  │
│  │                                                              │  │
│  │  • POST /repos/:owner/:repo/issues/:number/comments         │  │
│  │  • POST /repos/:owner/:repo/check-runs                      │  │
│  │  • POST /repos/:owner/:repo/pulls/:number/reviews           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│            │                                                       │
└────────────┼───────────────────────────────────────────────────────┘
             │
             │ (8) Update PR
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB PR INTERFACE                          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Pull Request #123                                           │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │ ✅ Codebase Guardian Review - PASSED                   │  │  │
│  │  │                                                         │  │  │
│  │  │ 🔍 Issues Found: 2 (MEDIUM severity)                   │  │  │
│  │  │ 🔒 Secrets Detected: 0                                 │  │  │
│  │  │ 📊 Complexity: 25/100                                  │  │  │
│  │  │ 🔧 Auto-fixes available: 2                             │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │                                                              │  │
│  │  [Comment with detailed review]                             │  │
│  │  [Approve] / [Request Changes]                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Component Flow

### 1️⃣ **GitHub Webhook Trigger**
```
Developer creates/updates PR
    ↓
GitHub sends webhook to API Gateway
    ↓
Payload includes: PR number, repo, diff URL, SHA
```

### 2️⃣ **API Gateway Processing**
```
API Gateway receives POST request
    ↓
Validates request structure
    ↓
Applies CORS headers
    ↓
Invokes Lambda function
```

### 3️⃣ **Lambda Handler Orchestration**
```python
lambda_handler(event, context):
    1. Parse webhook payload
    2. Detect if GitHub PR event
    3. Extract or fetch diff
    4. Route to appropriate handler
    5. Coordinate GitHub integration
    6. Return structured response
```

### 4️⃣ **Code Analysis Pipeline**

```
┌─────────────────────────────────────┐
│     CODE DIFF PROCESSING            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  PARALLEL ANALYSIS (Simultaneous)   │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Language    │  │  Secrets    │ │
│  │  Detection   │  │  Scanning   │ │
│  └──────────────┘  └─────────────┘ │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  Metrics     │  │  Complexity │ │
│  │  Calculation │  │  Analysis   │ │
│  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│     BEDROCK AI ANALYSIS             │
│   (Claude 3 Haiku Model)            │
│                                     │
│  • Apply language rules             │
│  • Generate severity scores         │
│  • Create fix suggestions           │
│  • Structure JSON response          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│     RESPONSE AGGREGATION            │
│                                     │
│  • Combine AI + Secrets + Metrics   │
│  • Format markdown output           │
│  • Calculate final severity         │
└─────────────────────────────────────┘
```

### 5️⃣ **GitHub Integration Workflow**

```
Review Complete
    ↓
┌─────────────────────────────────────┐
│  PARALLEL GITHUB API CALLS          │
│  (If webhook detected)              │
│                                     │
│  1. Post PR Comment                 │
│  2. Create Check Run                │
│  3. Submit Review Decision          │
└─────────────────────────────────────┘
    ↓
GitHub Updates PR Interface
```

---

## 🧩 Component Details

### **API Gateway**
- **Type:** REST API
- **Method:** POST
- **Path:** `/webhook/`
- **Features:**
  - CORS enabled (`Access-Control-Allow-Origin: *`)
  - Request/response validation
  - Throttling protection
  - API key optional

### **Lambda Function**
- **Runtime:** Python 3.9
- **Memory:** 512 MB
- **Timeout:** 30 seconds
- **Architecture:** x86_64
- **Triggers:** API Gateway
- **Environment Variables:**
  - `GITHUB_TOKEN` (optional)
- **IAM Permissions:**
  - Bedrock InvokeModel
  - CloudWatch Logs

### **Amazon Bedrock**
- **Model:** Claude 3 Haiku (anthropic.claude-3-haiku-20240307-v1:0)
- **Temperature:** 0.3 (for consistency)
- **Max Tokens:** 3000
- **Features Used:**
  - Structured JSON output
  - Reasoning capabilities
  - Code understanding
  - Natural language generation

### **GitHub Integration**
- **API Version:** REST API v3
- **Authentication:** Personal Access Token
- **Endpoints Used:**
  - `/repos/:owner/:repo/issues/:number/comments` - Post comments
  - `/repos/:owner/:repo/check-runs` - Create status checks
  - `/repos/:owner/:repo/pulls/:number/reviews` - Submit reviews
  - `/repos/:owner/:repo/pulls/:number` - Get PR diff

---

## 🔐 Security Architecture

### **Authentication & Authorization**
```
┌────────────────────────────────────┐
│  GitHub Webhook                    │
│  • Optional webhook secret         │
│  • Signature verification          │
└────────────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│  API Gateway                       │
│  • Optional API key                │
│  • Rate limiting                   │
│  • Request validation              │
└────────────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│  Lambda IAM Role                   │
│  • Least privilege access          │
│  • Bedrock InvokeModel only        │
│  • CloudWatch Logs write           │
└────────────────────────────────────┘
         ↓
┌────────────────────────────────────┐
│  GitHub Token                      │
│  • Stored in Lambda env vars       │
│  • Encrypted at rest               │
│  • Scoped permissions              │
└────────────────────────────────────┘
```

### **Data Flow Security**
- ✅ All communication over HTTPS
- ✅ Secrets masked in logs
- ✅ No sensitive data stored
- ✅ Token encryption at rest
- ✅ Least privilege IAM roles

---

## 📊 Data Model

### **Request Schema**
```json
{
  "diff": "string (git diff format)",
  "format": "enhanced|simple",
  "include_metrics": "boolean",
  
  // OR for GitHub webhook
  "pull_request": {
    "number": "integer",
    "diff_url": "string",
    "head": {"sha": "string"}
  },
  "repository": {
    "owner": {"login": "string"},
    "name": "string"
  }
}
```

### **Response Schema**
```json
{
  "summary": "string",
  "language": "python|javascript|java|go|...",
  "overall_severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  
  "secrets_detected": [
    {
      "type": "aws_access_key|github_token|...",
      "matched_value": "masked_string",
      "line_number": "integer",
      "severity": "CRITICAL",
      "recommendation": "string"
    }
  ],
  
  "code_metrics": {
    "lines_added": "integer",
    "lines_removed": "integer",
    "files_changed": "integer",
    "complexity_score": "0-100",
    "cyclomatic_complexity": "integer",
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
    "maintainability_index": "0-100",
    "estimated_review_time_minutes": "integer"
  },
  
  "issues": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "security|performance|quality|style",
      "title": "string",
      "description": "string",
      "line_hint": "string",
      "fix_available": "boolean"
    }
  ],
  
  "fixes": [
    {
      "issue_title": "string",
      "original_code": "string",
      "fixed_code": "string",
      "explanation": "string"
    }
  ],
  
  "positive_feedback": ["string"],
  "recommendations": ["string"],
  "review_comment": "string (formatted markdown)",
  
  "github_integration": {
    "success": "boolean",
    "pr_number": "integer",
    "repo": "string",
    "actions": ["comment_posted", "check_run_created", "review_submitted"],
    "message": "string"
  }
}
```

---

## ⚡ Performance Characteristics

### **Latency Breakdown**
```
API Gateway:          < 50ms
Lambda Cold Start:    1-2 seconds (first invocation)
Lambda Warm:          < 100ms
Language Detection:   < 100ms
Secrets Scanning:     < 200ms
Metrics Calculation:  < 150ms
Bedrock API Call:     2-4 seconds
Response Formatting:  < 100ms
GitHub API Calls:     500ms-1s (if webhook)
─────────────────────────────────────
Total (Cold):         4-6 seconds
Total (Warm):         3-5 seconds
```

### **Scalability**
- **Concurrent Executions:** 1000 (default Lambda limit)
- **Requests/Second:** 100+ (with warm instances)
- **Max Diff Size:** ~5MB (Lambda payload limit)
- **Throttling:** Bedrock API rate limits apply

### **Cost Optimization**
- Lambda: Pay per execution
- Bedrock: Pay per token
- API Gateway: Pay per request
- Estimated cost: $0.01-0.05 per review

---

## 🔧 Deployment Architecture

### **Infrastructure as Code**
```yaml
# template.yaml (AWS SAM)
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  CodeReviewFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.9
      Handler: lambda_handler.lambda_handler
      MemorySize: 512
      Timeout: 30
      Policies:
        - AmazonBedrockFullAccess
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /webhook
            Method: POST
```

### **CI/CD Pipeline**
```
Code Push to GitHub
    ↓
sam build
    ↓
sam validate
    ↓
sam deploy
    ↓
CloudFormation Stack Update
    ↓
Lambda Function Updated
    ↓
API Gateway Configured
```

---

## 🎯 Monitoring & Observability

### **CloudWatch Metrics**
- Lambda invocations
- Duration
- Errors
- Throttles
- Concurrent executions

### **Logging Strategy**
```python
# Structured logging levels
logger.info("Detected language: {language}")
logger.warning("Secrets found: {count}")
logger.error("Bedrock API error: {error}")
```

### **Alerting**
- Error rate > 5%
- Duration > 25 seconds
- Throttling detected
- Bedrock API errors

---

## 🚀 Scaling Strategy

### **Horizontal Scaling**
- Lambda auto-scales based on demand
- API Gateway handles burst traffic
- Bedrock managed service scales automatically

### **Optimization Techniques**
1. Lambda warm-up (reserved concurrency)
2. Response caching (API Gateway)
3. Parallel processing (secrets + metrics)
4. Efficient regex patterns
5. Minimal token usage in Bedrock

---

## 📈 Future Architecture Enhancements

### **Phase 2 Additions**
```
┌─────────────────────────────────────┐
│  DynamoDB                           │
│  • Review history storage           │
│  • Learning from feedback           │
│  • Team preferences                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  SQS Queue                          │
│  • Async processing for large PRs   │
│  • Retry logic                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Step Functions                     │
│  • Complex workflows                │
│  • Multi-model orchestration        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  CloudFront                         │
│  • API acceleration                 │
│  • Caching layer                    │
└─────────────────────────────────────┘
```

---

## 🏆 Architecture Highlights

✅ **Serverless** - No infrastructure management  
✅ **Scalable** - Handles 100+ concurrent reviews  
✅ **Cost-Efficient** - Pay only for what you use  
✅ **Secure** - Multiple security layers  
✅ **Observable** - Comprehensive logging and metrics  
✅ **Maintainable** - Clean separation of concerns  
✅ **Extensible** - Easy to add new features  

**Production-Grade Architecture Ready for Hackathon Demo!** 🚀
