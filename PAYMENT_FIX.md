# 💳 AWS Payment Method Setup Guide

## Issue
```
AccessDeniedException: Model access is denied due to INVALID_PAYMENT_INSTRUMENT
```

## Quick Fix (5 minutes)

### Step 1: Add Payment Method
1. Go to: https://console.aws.amazon.com/billing/home#/paymentmethods
2. Click "Add a payment method"
3. Enter valid credit/debit card details
4. Save payment method

### Step 2: Verify Account
- Wait 5-15 minutes for verification
- AWS will make a small test charge (refunded)
- You'll receive email confirmation

### Step 3: Test Again
```bash
python3 test_enhanced_features.py
```

## Alternative: Use Free Models

### Amazon Nova (Free Tier Available)
Nova Lite and Micro models are free for certain usage:

**Update `src/bedrock_agent.py`:**
```python
# Change this line:
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

# To this:
MODEL_ID = "amazon.nova-lite-v1:0"
```

Then redeploy:
```bash
sam build && sam deploy
```

## Check Current Status
```bash
# Check AWS account status
aws sts get-caller-identity

# Check available models
aws bedrock list-foundation-models --region ap-south-1

# Try direct Bedrock invocation
aws bedrock-runtime invoke-model \
  --model-id amazon.nova-lite-v1:0 \
  --body '{"messages":[{"role":"user","content":[{"text":"test"}]}],"inferenceConfig":{"maxTokens":100}}' \
  --region us-east-1 \
  output.json
```

## Support
If issues persist:
1. Contact AWS Support
2. Check https://status.aws.amazon.com/
3. Verify region availability
4. Try different AWS region (us-east-1)

## For Hackathon Demo
If payment can't be added immediately, use:
1. **Mock responses** - Demo with pre-recorded responses
2. **Local testing** - Test code logic without Bedrock
3. **Alternative models** - Try Nova Lite/Micro
4. **Video recording** - Record working demo when it works

The code is ready! Just need payment method active. 🚀
