import boto3
import json
import logging
import re
from typing import Dict, List, Tuple

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Bedrock client lazily (region decided per model)
bedrock_runtime = None

# --- Constants ---
# Default model (can be overridden if needed)
MODEL_ID = "openai.gpt-oss-120b-1:0"
ANTHROPIC_VERSION = "bedrock-2023-05-31"
MAX_TOKENS = 3000

# Robust JSON extraction for provider responses
def __extract_json_from_text(text: str):
    try:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        start = text.find('{')
        if start != -1:
            for end in range(len(text) - 1, start, -1):
                if text[end] == '}':
                    snippet = text[start:end+1]
                    try:
                        return json.loads(snippet)
                    except Exception:
                        continue
    except Exception:
        pass
    return None


# Severity levels
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITY_INFO = "INFO"

# Secrets detection patterns
SECRETS_PATTERNS = {
    'aws_access_key': r'(?i)(AWS|AKIA)[A-Z0-9]{16,}',
    'aws_secret_key': r'(?i)aws.{0,20}[\'"][0-9a-zA-Z/+]{40}[\'"]',
    'github_token': r'ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z]{22}_[0-9a-zA-Z]{59}',
    'generic_api_key': r'(?i)(api[_-]?key|apikey)[\'"\s]*[:=][\'"\s]*[0-9a-zA-Z]{20,}',
    'generic_secret': r'(?i)(secret|password|passwd|pwd)[\'"\s]*[:=][\'"\s]*[\'"][^\'"]{8,}[\'"]',
    'private_key': r'-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----',
    'jwt_token': r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
    'database_url': r'(?i)(mongodb|mysql|postgresql|postgres)://[^\s]+',
    'slack_token': r'xox[baprs]-[0-9]{10,12}-[0-9]{10,12}-[a-zA-Z0-9]{24,}',
    'stripe_key': r'(?i)(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}',
}

# Complexity thresholds
COMPLEXITY_LOW = 10
COMPLEXITY_MEDIUM = 20
COMPLEXITY_HIGH = 30

# Language detection patterns
LANGUAGE_PATTERNS = {
    'python': ['.py'],
    'javascript': ['.js', '.jsx', '.ts', '.tsx'],
    'java': ['.java'],
    'go': ['.go'],
    'rust': ['.rs'],
    'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
    'ruby': ['.rb'],
    'php': ['.php'],
    'swift': ['.swift'],
    'kotlin': ['.kt']
}

def detect_secrets(code_diff: str) -> List[Dict]:
    """
    Detect hardcoded secrets, API keys, passwords in code diff.
    
    :param code_diff: The code diff string
    :return: List of detected secrets with details
    """
    secrets_found = []
    
    # Extract only added lines (starting with +)
    added_lines = [line for line in code_diff.split('\n') if line.startswith('+') and not line.startswith('+++')]
    
    for line_num, line in enumerate(added_lines, 1):
        for secret_type, pattern in SECRETS_PATTERNS.items():
            matches = re.finditer(pattern, line)
            for match in matches:
                # Mask the secret value
                secret_value = match.group(0)
                masked_value = secret_value[:4] + '*' * (len(secret_value) - 8) + secret_value[-4:] if len(secret_value) > 8 else '***'
                
                secrets_found.append({
                    'type': secret_type,
                    'line_number': line_num,
                    'matched_value': masked_value,
                    'severity': SEVERITY_CRITICAL,
                    'recommendation': 'Remove hardcoded secret and use environment variables or secret management service'
                })
    
    return secrets_found


def calculate_code_metrics(code_diff: str) -> Dict:
    """
    Calculate various code metrics from the diff.
    
    :param code_diff: The code diff string
    :return: Dictionary with metrics
    """
    lines = code_diff.split('\n')
    
    # Count lines
    added_lines = [l for l in lines if l.startswith('+') and not l.startswith('+++')]
    removed_lines = [l for l in lines if l.startswith('-') and not l.startswith('---')]
    
    # Extract file names
    files_changed = set()
    for line in lines:
        if line.startswith('---') or line.startswith('+++'):
            match = re.search(r'[ab]/(.+?)(?:\s|$)', line)
            if match:
                files_changed.add(match.group(1))
    
    # Calculate complexity indicators
    complexity_indicators = 0
    complexity_patterns = [
        r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
        r'\btry\b', r'\bcatch\b', r'\bexcept\b', r'\bswitch\b', r'\bcase\b'
    ]
    
    code_content = '\n'.join(added_lines)
    for pattern in complexity_patterns:
        complexity_indicators += len(re.findall(pattern, code_content, re.IGNORECASE))
    
    # Estimate complexity score (0-100)
    complexity_score = min(100, complexity_indicators * 5)
    
    # Estimate review time (minutes)
    review_time_estimate = max(5, len(added_lines) // 10 + complexity_indicators * 2)
    
    # Risk assessment
    risk_score = 0
    if len(added_lines) > 100:
        risk_score += 2
    if complexity_indicators > COMPLEXITY_HIGH:
        risk_score += 3
    if len(files_changed) > 5:
        risk_score += 2
    
    risk_level = "LOW"
    if risk_score >= 7:
        risk_level = "CRITICAL"
    elif risk_score >= 5:
        risk_level = "HIGH"
    elif risk_score >= 3:
        risk_level = "MEDIUM"
    
    return {
        'lines_added': len(added_lines),
        'lines_removed': len(removed_lines),
        'files_changed': len(files_changed),
        'complexity_score': complexity_score,
        'cyclomatic_complexity': complexity_indicators,
        'estimated_review_time_minutes': review_time_estimate,
        'risk_level': risk_level,
        'maintainability_index': max(0, 100 - complexity_score)
    }


def detect_language(code_diff: str) -> str:
    """
    Detect the programming language from the diff.
    
    :param code_diff: The code diff string
    :return: Detected language name
    """
    # Extract file names from diff
    file_pattern = r'(?:---|\+\+\+)\s+[ab]/(.+?)(?:\s|$)'
    files = re.findall(file_pattern, code_diff)
    
    if not files:
        return 'unknown'
    
    # Check file extensions
    for file_path in files:
        for lang, extensions in LANGUAGE_PATTERNS.items():
            if any(file_path.endswith(ext) for ext in extensions):
                return lang
    
    return 'unknown'


def get_language_specific_prompt(language: str) -> str:
    """
    Get language-specific review instructions.
    
    :param language: Programming language name
    :return: Language-specific prompt additions
    """
    prompts = {
        'python': """
- Follow PEP 8 style guidelines
- Check for proper exception handling
- Look for use of list/dict comprehensions where appropriate
- Verify type hints are used
- Check for security issues like SQL injection, command injection
""",
        'javascript': """
- Check for proper use of const/let (avoid var)
- Look for async/await usage instead of callbacks
- Verify error handling with try-catch
- Check for XSS vulnerabilities
- Look for proper React hooks usage (if React)
""",
        'java': """
- Check for proper exception handling
- Look for memory leaks
- Verify proper use of streams and lambdas
- Check thread safety
- Look for SQL injection vulnerabilities
""",
        'go': """
- Check for proper error handling (never ignore errors)
- Look for goroutine leaks
- Verify defer statements are used correctly
- Check for race conditions
- Look for proper context usage
""",
        'unknown': """
- Check for common security vulnerabilities
- Look for performance issues
- Verify error handling
def _extract_json_loose(text: str):
    try:
        start = text.find('{')
        if start == -1:
            return None
        # Try from the end backwards to find a matching closing brace
        for end in range(len(text) - 1, start, -1):
            if text[end] == '}':
                snippet = text[start:end + 1]
                try:
                    return json.loads(snippet)
                except Exception:
                    continue
    except Exception:
        return None
    return None


def _extract_json_from_text(text: str):
    try:
        # Try fenced JSON
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        # Try first JSON object in text
        start = text.find('{')
        if start != -1:
            for end in range(len(text) - 1, start, -1):
                if text[end] == '}':
                    snippet = text[start:end+1]
                    try:
                        return json.loads(snippet)
                    except Exception:
                        continue
    except Exception:
        pass
    return None


- Check code clarity and maintainability
"""
    }
    
    return prompts.get(language, prompts['unknown'])


def review_code_changes(code_diff: str) -> str:
    """
    Reviews a code diff using a model from Amazon Bedrock.
    (Legacy function - kept for backward compatibility)
    
    :param code_diff: A string containing the code changes (diff format).
    :return: A string containing the AI-generated code review.
    """
    result = review_code_with_severity(code_diff)
    return result.get('review_comment', 'Error generating review')


def review_code_with_severity(code_diff: str, include_metrics: bool = True, debug: bool = False) -> Dict:
    """
    Reviews a code diff with severity scoring and auto-fix suggestions.
    
    :param code_diff: A string containing the code changes (diff format).
    :return: Dictionary containing review, severity, fixes, and metadata
    """
    # Ensure Bedrock client is initialized (region depends on model)
    global bedrock_runtime
    if bedrock_runtime is None:
        try:
            region = 'us-east-1' if MODEL_ID.startswith('openai.') else None
            bedrock_runtime = boto3.client('bedrock-runtime', region_name=region) if region else boto3.client('bedrock-runtime')
        except Exception as e:
            logger.error(f"Error initializing Bedrock client: {e}")
            bedrock_runtime = None
    if not bedrock_runtime:
        return {
            'error': 'Bedrock client is not initialized',
            'review_comment': 'Error: Bedrock client is not initialized. Check application logs.',
            'severity': SEVERITY_INFO,
            'issues': [],
            'fixes': []
        }

    # Detect language
    language = detect_language(code_diff)
    language_prompt = get_language_specific_prompt(language)
    
    # Detect secrets
    secrets = detect_secrets(code_diff)
    
    # Calculate metrics
    metrics = calculate_code_metrics(code_diff) if include_metrics else {}
    
    logger.info(f"Detected language: {language}, Secrets found: {len(secrets)}, Complexity: {metrics.get('complexity_score', 0)}")

    # Add secrets to prompt if found
    secrets_context = ""
    if secrets:
        secrets_context = f"\n**⚠️ CRITICAL: {len(secrets)} Hardcoded Secrets Detected:**\n"
        for secret in secrets:
            secrets_context += f"- {secret['type']}: {secret['matched_value']} (Line ~{secret['line_number']})\n"
    
    # Add metrics context
    metrics_context = ""
    if metrics:
        metrics_context = f"""
**Code Metrics:**
- Lines added: {metrics['lines_added']}
- Lines removed: {metrics['lines_removed']}
- Files changed: {metrics['files_changed']}
- Complexity score: {metrics['complexity_score']}/100
- Cyclomatic complexity: {metrics['cyclomatic_complexity']}
- Risk level: {metrics['risk_level']}
"""

    # --- Enhanced Prompt Engineering with Severity and Auto-Fix ---
    prompt = f"""
You are Codebase Guardian, an expert AI code reviewer with advanced analysis capabilities.

**Your Task:**
Analyze the following code changes and provide a structured, comprehensive review with:
1. Severity classification for each issue found
2. Automated fix suggestions with corrected code
3. Clear explanations and best practices

**Detected Language:** {language.upper()}
{secrets_context}
{metrics_context}

**Language-Specific Guidelines:**
{language_prompt}

**Review Structure (IMPORTANT - Follow this JSON format):**

{{
  "summary": "Brief overview of changes",
  "language": "{language}",
  "overall_severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "issues": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "security|performance|quality|style",
      "title": "Short issue title",
      "description": "Detailed explanation",
      "line_hint": "approximate line or section",
      "fix_available": true|false
    }}
  ],
  "fixes": [
    {{
      "issue_title": "Related issue title",
      "original_code": "problematic code snippet",
      "fixed_code": "corrected code snippet",
      "explanation": "Why this fix works"
    }}
  ],
  "positive_feedback": ["Things done well"],
  "recommendations": ["General improvement suggestions"]
}}

**Severity Levels:**
- CRITICAL: Security vulnerabilities, data loss risks, critical bugs
- HIGH: Performance issues, major bugs, important best practice violations
- MEDIUM: Code quality issues, moderate performance concerns, maintainability
- LOW: Style improvements, minor optimizations, suggestions
- INFO: Positive feedback, informational notes

**Code Diff to Review:**

<code_diff>
{code_diff}
</code_diff>

Respond ONLY with valid JSON following the structure above. Be thorough but concise.
"""

    # --- Bedrock API Request ---
    # Build request per provider
    if MODEL_ID.startswith('openai.'):
        request_body = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "max_tokens": min(MAX_TOKENS, 1024),
            "temperature": 0.3,
            "top_p": 0.9
        }
    else:
        request_body = {
            "anthropic_version": ANTHROPIC_VERSION,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
            "temperature": 0.3
        }

    try:
        logger.info(f"Invoking model {MODEL_ID} for {language} code review")
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            body=json.dumps(request_body),
            modelId=MODEL_ID,
            contentType='application/json',
            accept='application/json'
        )

        # Parse the response
        response_body = json.loads(response.get('body').read())
        if debug:
            return {
                'debug': True,
                'provider_request': request_body,
                'provider_response': response_body
            }
        review_text = ""
        if MODEL_ID.startswith('openai.'):
            # Prefer Chat Completions shape
            if isinstance(response_body.get('choices'), list) and response_body['choices']:
                try:
                    review_text = response_body['choices'][0]['message'].get('content', '')
                except Exception:
                    review_text = ''
            # Fallback to other OSS shapes
            if not review_text and isinstance(response_body.get('output'), list):
                try:
                    review_text = response_body['output'][0]['content'][0].get('text', '')
                except Exception:
                    review_text = ''
            if not review_text and isinstance(response_body.get('output'), dict):
                try:
                    msg = response_body['output'].get('message', {})
                    parts = msg.get('content', [])
                    if parts and isinstance(parts, list) and isinstance(parts[0], dict):
                        review_text = parts[0].get('text', '')
                except Exception:
                    review_text = ''
            if not review_text:
                review_text = response_body.get('output_text') or response_body.get('generated_text') or response_body.get('content', '')
        else:
            review_text = response_body['content'][0]['text']
        
        logger.info("Successfully received response from Bedrock")
        
        # Try to parse JSON response
        try:
            # Try to extract JSON from response text
            extracted = __extract_json_from_text(review_text)
            if extracted is not None:
                review_data = extracted
            else:
                try:
                    review_data = json.loads(review_text)
                except Exception:
                    review_data = {"summary": "Model returned non-JSON output", "overall_severity": "INFO", "issues": [], "fixes": []}
            
            # Add secrets and metrics to response
            review_data['secrets_detected'] = secrets
            review_data['code_metrics'] = metrics
            
            # Override severity if secrets found
            if secrets:
                review_data['overall_severity'] = SEVERITY_CRITICAL
            
            # Add the raw review text as well
            review_data['review_comment'] = format_review_output(review_data, secrets, metrics)
            review_data['raw_response'] = review_text
            
            logger.info(f"Parsed structured review with severity: {review_data.get('overall_severity', 'UNKNOWN')}")
            return review_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON response, returning as text: {e}")
            # Fallback to text response with secrets and metrics
            severity = SEVERITY_CRITICAL if secrets else SEVERITY_INFO
            return {
                'review_comment': review_text,
                'severity': severity,
                'overall_severity': severity,
                'language': language,
                'issues': [],
                'fixes': [],
                'secrets_detected': secrets,
                'code_metrics': metrics,
                'raw_response': review_text
            }

    except Exception as e:
        logger.error(f"Error invoking Bedrock model: {e}", exc_info=True)
        return {
            'error': str(e),
            'review_comment': f"Error: Could not get a review from the AI model. Details: {e}",
            'severity': SEVERITY_INFO,
            'issues': [],
            'fixes': []
        }


def format_review_output(review_data: Dict, secrets: List[Dict] = None, metrics: Dict = None) -> str:
    """
    Format the structured review data into a readable markdown string.
    
    :param review_data: Structured review data dictionary
    :return: Formatted markdown string
    """
    output = []
    
    # Header with severity badge
    severity = review_data.get('overall_severity', 'INFO')
    severity_emoji = {
        'CRITICAL': '🚨',
        'HIGH': '⚠️',
        'MEDIUM': '📋',
        'LOW': '💡',
        'INFO': 'ℹ️'
    }
    
    output.append(f"# {severity_emoji.get(severity, 'ℹ️')} Code Review by Codebase Guardian")
    output.append(f"\n**Overall Severity:** `{severity}`")
    output.append(f"**Language Detected:** `{review_data.get('language', 'unknown')}`\n")
    
    # Code Metrics Dashboard
    if metrics:
        output.append("## 📊 Code Metrics Dashboard\n")
        output.append(f"| Metric | Value |")
        output.append(f"|--------|-------|")
        output.append(f"| Lines Added | {metrics['lines_added']} |")
        output.append(f"| Lines Removed | {metrics['lines_removed']} |")
        output.append(f"| Files Changed | {metrics['files_changed']} |")
        output.append(f"| Complexity Score | {metrics['complexity_score']}/100 |")
        output.append(f"| Cyclomatic Complexity | {metrics['cyclomatic_complexity']} |")
        output.append(f"| Maintainability Index | {metrics['maintainability_index']}/100 |")
        output.append(f"| Risk Level | `{metrics['risk_level']}` |")
        output.append(f"| Estimated Review Time | ~{metrics['estimated_review_time_minutes']} minutes |\n")
    
    # Secrets Detection
    if secrets:
        output.append("## 🚨 CRITICAL: Hardcoded Secrets Detected\n")
        output.append("**⚠️ ACTION REQUIRED: Remove these secrets immediately!**\n")
        for i, secret in enumerate(secrets, 1):
            output.append(f"### Secret #{i}: {secret['type'].replace('_', ' ').title()}")
            output.append(f"**Matched Value:** `{secret['matched_value']}`")
            output.append(f"**Location:** Line ~{secret['line_number']}")
            output.append(f"**Severity:** `{secret['severity']}`")
            output.append(f"**Recommendation:** {secret['recommendation']}\n")
    
    # Summary
    if 'summary' in review_data:
        output.append(f"## 📝 Summary\n{review_data['summary']}\n")
    
    # Issues
    issues = review_data.get('issues', [])
    if issues:
        output.append("## 🔍 Issues Found\n")
        for i, issue in enumerate(issues, 1):
            severity_icon = severity_emoji.get(issue.get('severity', 'INFO'), '•')
            output.append(f"### {severity_icon} Issue #{i}: {issue.get('title', 'Untitled')}")
            output.append(f"**Severity:** `{issue.get('severity', 'INFO')}` | **Category:** `{issue.get('category', 'general')}`")
            output.append(f"\n{issue.get('description', 'No description')}\n")
            if 'line_hint' in issue:
                output.append(f"*Location hint: {issue['line_hint']}*\n")
    
    # Automated Fixes
    fixes = review_data.get('fixes', [])
    if fixes:
        output.append("## 🔧 Automated Fix Suggestions\n")
        for i, fix in enumerate(fixes, 1):
            output.append(f"### Fix #{i}: {fix.get('issue_title', 'Fix')}\n")
            
            if 'original_code' in fix:
                output.append("**Original Code:**")
                output.append(f"```\n{fix['original_code']}\n```\n")
            
            if 'fixed_code' in fix:
                output.append("**Fixed Code:**")
                output.append(f"```\n{fix['fixed_code']}\n```\n")
            
            if 'explanation' in fix:
                output.append(f"**Explanation:** {fix['explanation']}\n")
    
    # Positive Feedback
    positive = review_data.get('positive_feedback', [])
    if positive:
        output.append("## ✅ What's Good\n")
        for item in positive:
            output.append(f"- {item}")
        output.append("")
    
    # Recommendations
    recommendations = review_data.get('recommendations', [])
    if recommendations:
        output.append("## 💡 Recommendations\n")
        for rec in recommendations:
            output.append(f"- {rec}")
        output.append("")
    
    return "\n".join(output)
