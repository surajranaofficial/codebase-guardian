import json
import logging
import bedrock_agent
import github_integration

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main AWS Lambda handler function with enhanced features:
    - Severity scoring
    - Multi-language detection
    - Automated fix suggestions
    - Secrets detection
    - Code complexity metrics
    - GitHub PR integration

    :param event: The event data passed by AWS Lambda, typically from an API Gateway.
    :param context: The runtime information provided by AWS Lambda.
    :return: A dictionary containing the HTTP status code and a JSON body.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # The actual payload from the Git provider is in the 'body' of the event
        body = json.loads(event.get('body', '{}'))

        # Check if this is a GitHub webhook
        is_github_webhook = 'pull_request' in body or event.get('headers', {}).get('X-GitHub-Event')
        
        # Extract the diff from the payload
        code_diff = body.get('diff')
        
        # For GitHub webhooks, fetch diff from URL
        if is_github_webhook and not code_diff:
            pr_info = github_integration.parse_github_webhook(body)
            if pr_info:
                code_diff = github_integration.fetch_pr_diff(pr_info['diff_url'])
                logger.info(f"Fetched diff for PR #{pr_info['pr_number']}")

        if not code_diff:
            logger.warning("No 'diff' found in the request body.")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': "Request body must contain a 'diff' key or be a valid GitHub PR webhook."
                })
            }

        # Check if client wants structured response or simple text
        response_format = body.get('format', 'enhanced')  # 'enhanced' or 'simple'
        include_metrics = body.get('include_metrics', True)
        debug = body.get('debug', False)

        # Call the Bedrock agent to review the code with new features
        logger.info("Invoking Bedrock agent for enhanced code review...")
        
        if response_format == 'simple':
            # Backward compatible simple text response
            review_comment = bedrock_agent.review_code_changes(code_diff)
            response_data = {'review_comment': review_comment}
        else:
            # Enhanced structured response
            review_data = bedrock_agent.review_code_with_severity(code_diff, include_metrics, debug)
            response_data = review_data
            
            # Handle GitHub PR integration
            if is_github_webhook:
                integration_result = github_integration.handle_github_pr(body, review_data)
                response_data['github_integration'] = integration_result
                logger.info(f"GitHub integration: {integration_result.get('message')}")
        
        logger.info("Received review from Bedrock agent.")

        # Return the response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data, indent=2)
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': "Invalid JSON format in request body."
            })
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': "An internal server error occurred.",
                'details': str(e)
            })
        }
