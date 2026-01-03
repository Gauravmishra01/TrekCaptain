#!/usr/bin/env python3
"""Check SES sandbox status"""
import boto3
from botocore.exceptions import ClientError

client = boto3.client('ses', region_name='ap-south-1')

print("=" * 60)
print("AWS SES Account Status")
print("=" * 60)
print()

# Check if in production or sandbox
try:
    response = client.get_account_sending_enabled()
    print("✓ Account Status: PRODUCTION MODE")
    print(f"  Sending Enabled: {response['Enabled']}")
except ClientError as e:
    if 'AccessDenied' in str(e):
        print("Account Status: SANDBOX MODE (restricted)")
        print()
        print("SANDBOX MODE ISSUE:")
        print("━" * 60)
        print("You are in AWS SES Sandbox mode, which has restrictions:")
        print()
        print("1. Can ONLY send to verified email addresses")
        print("2. Can send max 200 emails per day")
        print("3. Can send max 1 email per second")
        print()
        print("SOLUTIONS:")
        print()
        print("Option A: Request Production Access (RECOMMENDED)")
        print("  1. Go to AWS SES console")
        print("  2. Click 'Send a Limit Increase Request'")
        print("  3. Select 'Production Access'")
        print("  4. AWS reviews within 24 hours")
        print()
        print("Option B: Verify Recipient Email in SES")
        print("  1. Go to AWS SES console → Email Addresses")
        print("  2. Verify each email you want to test")
        print("  3. Send only to verified emails")
        print()
        print("━" * 60)
    else:
        print(f"Error: {e}")

print()

# List all verified identities
identities = client.list_identities()
print("Verified Email Addresses in SES:")
if identities.get('Identities'):
    for email in identities['Identities']:
        if '@' in email:
            print(f"  ✓ {email}")
else:
    print("  (none)")
