#!/usr/bin/env python3
"""
Test script to diagnose AWS SES email sending issues.
Run this to see what's happening with your SES configuration.
"""

import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime

# Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "no-reply@your-travel-app.com")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
RECIPIENT_EMAIL = input("Enter recipient email to test: ").strip()

print("=" * 70)
print("AWS SES Email Sending Diagnostics")
print("=" * 70)
print(f"Sender Email: {SENDER_EMAIL}")
print(f"Recipient Email: {RECIPIENT_EMAIL}")
print(f"AWS Region: {AWS_REGION}")
print()

# Step 1: Check if we can connect to SES
print("Step 1: Connecting to AWS SES...")
try:
    ses_client = boto3.client("ses", region_name=AWS_REGION)
    print("✓ Connected to AWS SES")
except Exception as e:
    print(f"✗ Failed to connect to SES: {e}")
    exit(1)

# Step 2: Get send quota
print("\nStep 2: Checking SES send quota...")
try:
    response = ses_client.get_send_quota()
    print(f"✓ Send Quota:")
    print(f"  - Max send rate: {response['MaxSendRate']} emails/second")
    print(f"  - Max daily quota: {response['Max24HourSend']} emails/day")
    print(f"  - Sent in last 24h: {response['SentLast24Hour']} emails")
    print(f"  - Remaining quota: {response['Max24HourSend'] - response['SentLast24Hour']} emails")
except ClientError as e:
    print(f"✗ SES Error: {e.response['Error']['Code']}: {e.response['Error']['Message']}")
    if e.response['Error']['Code'] == "MessageRejected":
        print("  → Sender email not verified in SES")
    exit(1)

# Step 3: Try sending a test email
print("\nStep 3: Attempting to send test email...")
try:
    subject = "AWS SES Test - Your Travel App Verification Code"
    
    text_body = f"""
Test Email - AWS SES Diagnostic

If you receive this email, AWS SES is configured correctly!

Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sender: {SENDER_EMAIL}
Recipient: {RECIPIENT_EMAIL}
Region: {AWS_REGION}

Best regards,
AWS SES Test Script
"""
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>AWS SES Test Email</h2>
    <p>If you receive this email, AWS SES is configured correctly!</p>
    <p><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Sender:</strong> {SENDER_EMAIL}</p>
    <p><strong>Recipient:</strong> {RECIPIENT_EMAIL}</p>
    <p><strong>Region:</strong> {AWS_REGION}</p>
    <hr>
    <p>AWS SES Test Script</p>
</body>
</html>
"""
    
    response = ses_client.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [RECIPIENT_EMAIL]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": text_body, "Charset": "UTF-8"},
                "Html": {"Data": html_body, "Charset": "UTF-8"},
            },
        },
    )
    
    print(f"✓ Email sent successfully!")
    print(f"  - Message ID: {response['MessageId']}")
    print()
    print("📧 Check your email inbox for the test message.")
    print()
    
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']
    print(f"✗ Failed to send email")
    print(f"  - Error Code: {error_code}")
    print(f"  - Error Message: {error_message}")
    print()
    
    # Provide helpful guidance based on error
    if error_code == "MessageRejected":
        print("🔍 TROUBLESHOOTING:")
        print("  1. Verify sender email in AWS SES console:")
        print("     https://console.aws.amazon.com/ses/")
        print("  2. Update .env file with verified email:")
        print(f"     SENDER_EMAIL=verified-email@example.com")
        print()
    elif error_code == "AccessDenied":
        print("🔍 TROUBLESHOOTING:")
        print("  1. Check AWS credentials are configured:")
        print("     aws configure")
        print("  2. Your IAM user needs SES permissions")
        print()
    elif error_code == "InvalidParameterValue":
        print("🔍 TROUBLESHOOTING:")
        print("  1. Check recipient email format is valid")
        print("  2. If in Sandbox mode, verify recipient email")
        print()
    
    exit(1)

except Exception as e:
    print(f"✗ Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

print("=" * 70)
print("Diagnostic Complete!")
print("=" * 70)
print()
print("NEXT STEPS:")
print("1. Check your inbox for the test email")
print("2. If email received → Your SES is working! Check SPAM folder")
print("3. If email NOT received → Check troubleshooting above")
print()
print("For FastAPI registration:")
print("- Make sure .env file has SENDER_EMAIL and AWS_REGION")
print("- Server must be running: uvicorn app.three_sides_api.main:app")
print("- Test endpoint: POST http://127.0.0.1:8000/api/v1/users/register")
