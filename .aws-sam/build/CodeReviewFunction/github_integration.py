"""
GitHub Pull Request Integration Module
Handles automatic PR commenting and status checks
"""

import json
import logging
import os
from typing import Dict, Optional
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# GitHub API Configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')


def parse_github_webhook(event_body: Dict) -> Optional[Dict]:
    """
    Parse GitHub webhook payload to extract PR information.
    
    :param event_body: The webhook payload
    :return: Parsed PR data or None
    """
    try:
        # Check if it's a pull request event
        if 'pull_request' not in event_body:
            return None
        
        pr = event_body['pull_request']
        repo = event_body['repository']
        
        return {
            'pr_number': pr['number'],
            'repo_owner': repo['owner']['login'],
            'repo_name': repo['name'],
            'pr_url': pr['html_url'],
            'diff_url': pr['diff_url'],
            'head_sha': pr['head']['sha'],
            'base_ref': pr['base']['ref'],
            'head_ref': pr['head']['ref']
        }
    except Exception as e:
        logger.error(f"Error parsing GitHub webhook: {e}")
        return None


def fetch_pr_diff(diff_url: str) -> Optional[str]:
    """
    Fetch the diff content from GitHub PR.
    
    :param diff_url: URL to fetch the diff from
    :return: Diff content as string
    """
    try:
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        
        response = requests.get(diff_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching PR diff: {e}")
        return None


def post_pr_comment(repo_owner: str, repo_name: str, pr_number: int, comment_body: str) -> bool:
    """
    Post a comment on a GitHub Pull Request.
    
    :param repo_owner: Repository owner
    :param repo_name: Repository name
    :param pr_number: PR number
    :param comment_body: Comment markdown content
    :return: Success status
    """
    if not GITHUB_TOKEN:
        logger.warning("GitHub token not configured, cannot post comment")
        return False
    
    url = f"{GITHUB_API_BASE}/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'body': comment_body
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully posted comment on PR #{pr_number}")
        return True
    except Exception as e:
        logger.error(f"Error posting PR comment: {e}")
        return False


def create_check_run(repo_owner: str, repo_name: str, head_sha: str, 
                     review_result: Dict) -> bool:
    """
    Create a GitHub check run with the review results.
    
    :param repo_owner: Repository owner
    :param repo_name: Repository name
    :param head_sha: Commit SHA
    :param review_result: Review result dictionary
    :return: Success status
    """
    if not GITHUB_TOKEN:
        logger.warning("GitHub token not configured, cannot create check run")
        return False
    
    url = f"{GITHUB_API_BASE}/repos/{repo_owner}/{repo_name}/check-runs"
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    # Determine conclusion based on severity
    severity = review_result.get('overall_severity', 'INFO')
    secrets_found = len(review_result.get('secrets_detected', []))
    
    if severity == 'CRITICAL' or secrets_found > 0:
        conclusion = 'failure'
        summary = f"🚨 Critical issues found! Severity: {severity}"
    elif severity == 'HIGH':
        conclusion = 'failure'
        summary = f"⚠️ High severity issues found"
    elif severity == 'MEDIUM':
        conclusion = 'neutral'
        summary = f"📋 Medium severity issues to address"
    else:
        conclusion = 'success'
        summary = f"✅ Code review passed with minor suggestions"
    
    # Build detailed output
    output_lines = [summary, ""]
    
    if secrets_found > 0:
        output_lines.append(f"🔒 **{secrets_found} Hardcoded Secrets Detected!**")
        output_lines.append("")
    
    metrics = review_result.get('code_metrics', {})
    if metrics:
        output_lines.append("**Code Metrics:**")
        output_lines.append(f"- Complexity: {metrics.get('complexity_score', 0)}/100")
        output_lines.append(f"- Risk Level: {metrics.get('risk_level', 'UNKNOWN')}")
        output_lines.append("")
    
    issues = review_result.get('issues', [])
    if issues:
        output_lines.append(f"**Issues Found: {len(issues)}**")
        for issue in issues[:5]:  # Show first 5
            output_lines.append(f"- [{issue.get('severity')}] {issue.get('title')}")
    
    payload = {
        'name': 'Codebase Guardian Review',
        'head_sha': head_sha,
        'status': 'completed',
        'conclusion': conclusion,
        'output': {
            'title': 'AI Code Review Results',
            'summary': summary,
            'text': '\n'.join(output_lines)
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully created check run for {head_sha}")
        return True
    except Exception as e:
        logger.error(f"Error creating check run: {e}")
        return False


def format_pr_comment(review_result: Dict) -> str:
    """
    Format the review result as a GitHub PR comment.
    
    :param review_result: Review result dictionary
    :return: Formatted markdown comment
    """
    comment = review_result.get('review_comment', '')
    
    # Add footer with metadata
    footer = """

---

<details>
<summary>📊 Review Metadata</summary>

**Codebase Guardian** - AI-Powered Code Review Agent
- Model: Claude 3 Haiku (Amazon Bedrock)
- Features: Severity Scoring, Multi-Language Support, Auto-Fix Suggestions
- Secrets Detection: Enabled
- Complexity Analysis: Enabled

</details>
"""
    
    return comment + footer


def approve_or_request_changes(repo_owner: str, repo_name: str, pr_number: int,
                               review_result: Dict) -> bool:
    """
    Approve PR or request changes based on review severity.
    
    :param repo_owner: Repository owner
    :param repo_name: Repository name
    :param pr_number: PR number
    :param review_result: Review result dictionary
    :return: Success status
    """
    if not GITHUB_TOKEN:
        logger.warning("GitHub token not configured, cannot submit review")
        return False
    
    url = f"{GITHUB_API_BASE}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews"
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    severity = review_result.get('overall_severity', 'INFO')
    secrets_found = len(review_result.get('secrets_detected', []))
    
    # Determine review action
    if severity == 'CRITICAL' or secrets_found > 0:
        event = 'REQUEST_CHANGES'
        body = "🚨 Critical issues found. Please address before merging."
    elif severity == 'HIGH':
        event = 'REQUEST_CHANGES'
        body = "⚠️ High severity issues found. Please review and address."
    elif severity == 'MEDIUM':
        event = 'COMMENT'
        body = "📋 Some improvements suggested. Review recommended."
    else:
        event = 'APPROVE'
        body = "✅ Code looks good! Minor suggestions provided."
    
    payload = {
        'body': body,
        'event': event
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully submitted review: {event}")
        return True
    except Exception as e:
        logger.error(f"Error submitting review: {e}")
        return False


def handle_github_pr(event_body: Dict, review_result: Dict) -> Dict:
    """
    Complete GitHub PR integration workflow.
    
    :param event_body: GitHub webhook payload
    :param review_result: Code review result
    :return: Integration result
    """
    pr_info = parse_github_webhook(event_body)
    
    if not pr_info:
        return {
            'success': False,
            'message': 'Not a valid GitHub PR webhook'
        }
    
    results = {
        'pr_number': pr_info['pr_number'],
        'repo': f"{pr_info['repo_owner']}/{pr_info['repo_name']}",
        'actions': []
    }
    
    # Post comment
    comment_body = format_pr_comment(review_result)
    if post_pr_comment(pr_info['repo_owner'], pr_info['repo_name'], 
                       pr_info['pr_number'], comment_body):
        results['actions'].append('comment_posted')
    
    # Create check run
    if create_check_run(pr_info['repo_owner'], pr_info['repo_name'],
                       pr_info['head_sha'], review_result):
        results['actions'].append('check_run_created')
    
    # Submit review (approve/request changes)
    if approve_or_request_changes(pr_info['repo_owner'], pr_info['repo_name'],
                                  pr_info['pr_number'], review_result):
        results['actions'].append('review_submitted')
    
    results['success'] = len(results['actions']) > 0
    results['message'] = f"GitHub integration completed: {', '.join(results['actions'])}"
    
    return results
