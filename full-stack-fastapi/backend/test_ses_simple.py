#!/usr/bin/env python3
"""Quick test to verify SES email sending works"""

import boto3
import os
from botocore.exceptions import ClientError

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "princepratapfreelancer@gmail.com")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
RECIPIENT_EMAIL = "princepratapfreelancer@gmail.com"

print("=" * 60)
print("Testing AWS SES Email Sending")
print("=" * 60)
print(f"Sender: {SENDER_EMAIL}")
print(f"Recipient: {RECIPIENT_EMAIL}")
print(f"Region: {AWS_REGION}")
print()

try:
    ses_client = boto3.client("ses", region_name=AWS_REGION)
    
    # Check quota
    try:
        quota = ses_client.get_send_quota()
        print(f"✓ SES Connected")
        remaining = quota.get('Max24HourSend', 0) - quota.get('SentLast24Hour', 0)
        print(f"  Send quota: {remaining} remaining")
    except:
        print(f"✓ SES Connected (quota check skipped)")
    print()
    
    # Send test email
    print("Sending test email...")
    response = ses_client.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [RECIPIENT_EMAIL]},
        Message={
            "Subject": {"Data": "AWS SES Test", "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": "This is a test email from AWS SES", "Charset": "UTF-8"},
                "Html": {"Data": "<html><body><h1>AWS SES Test</h1><p>This email works!</p></body></html>", "Charset": "UTF-8"},
            },
        },
    )
    
    print(f"✓ Email sent successfully!")
    print(f"  Message ID: {response['MessageId']}")
    print()
    print("Check your email inbox at: princepratapfreelancer@gmail.com")
    
except ClientError as e:
    print(f"✗ Error: {e.response['Error']['Code']}")
    print(f"  Message: {e.response['Error']['Message']}")
    
    if e.response['Error']['Code'] == "MessageRejected":
        print()
        print("ISSUE: Sender email not verified in SES")
        print("ACTION: Verify the email in AWS SES console")
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
