# AWS SES Setup Guide for Travel App OTP Verification

## Overview
This guide explains how to configure AWS Simple Email Service (SES) for sending OTP verification emails in the Travel App.

---

## Step 1: Verify Your Email Address in AWS SES

1. **Go to AWS SES Console**
   - Navigate to: https://console.aws.amazon.com/ses/
   - Make sure you're in the **ap-south-1** region (top right)

2. **Verify Email Address**
   - Click **Email Addresses** (left sidebar)
   - Click **Verify a New Email Address**
   - Enter: `no-reply@your-travel-app.com` (or any email you control)
   - AWS will send a verification link to that email
   - Click the link to verify

3. **Check Verification Status**
   - Once verified, the email will show as "Verified"
   - Status should be green with checkmark

---

## Step 2: Request Production Access (if needed)

By default, AWS SES accounts are in **Sandbox mode**, which limits:
- Can only send to verified email addresses
- Daily sending quota is 200 emails

For production, request removal from sandbox:
- Click **Email Sending Quota** (left sidebar)
- Click **Request a Sending Limit Increase**
- Select **Account Attributes** → **SES Sending Limits**
- Request production access

---

## Step 3: Configure Environment Variables

Update your `.env` file with your verified email:

```
SENDER_EMAIL=no-reply@your-travel-app.com
AWS_REGION=ap-south-1
```

---

## Step 4: AWS Credentials

The application will use one of these (in order of priority):

1. **AWS Credentials from CLI** (already configured from earlier):
   ```bash
   aws configure
   ```

2. **Environment Variables**:
   ```bash
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   ```

3. **~/.aws/credentials file** (recommended - what you already set up)

---

## Step 5: Test the Endpoint

### Register a User
```powershell
$registerBody = @{
    userName = "Prince Pratap"
    email = "princepratapfreelancer@gmail.com"
    phoneNumber = "7428839202"
    gender = "male"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/users/register" `
  -ContentType "application/json" `
  -Body $registerBody
```

### Expected Response
```json
{
    "message": "User registered successfully. Please check your email for verification code.",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_email": "princepratapfreelancer@gmail.com"
}
```

**Check your email inbox** - you should receive a verification email with the OTP code.

### Verify OTP
```powershell
$verifyBody = @{
    email = "princepratapfreelancer@gmail.com"
    otpCode = "123456"  # Use the 6-digit code from the email
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/users/verify-otp" `
  -ContentType "application/json" `
  -Body $verifyBody
```

### Expected Response
```json
{
    "message": "Email verified successfully. Your account is now active.",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_email": "princepratapfreelancer@gmail.com"
}
```

---

## Troubleshooting

### Error: "MessageRejected" or "Email address not verified"
**Solution**: Verify the sender email in AWS SES console (Step 1)

### Error: "AccessDenied"
**Solution**: Check your AWS credentials and ensure your IAM user has SES permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

### Email not received (Sandbox mode)
**Problem**: In sandbox mode, recipients must also have verified email addresses
**Solution**: 
- Verify recipient email in SES console, OR
- Request production access (Step 2)

### Check SES Sending Logs
```bash
# View sent emails (last 24 hours)
aws ses get-account-sending-enabled --region ap-south-1
```

---

## Production Checklist

- [ ] Email sender verified in SES console
- [ ] Production access requested (if needed)
- [ ] Environment variables configured (.env file)
- [ ] AWS credentials configured (~/.aws/credentials)
- [ ] Tested registration and OTP verification flow
- [ ] Email template customized for your brand
- [ ] Sender email set to official domain (e.g., noreply@yourdomain.com)

---

## API Documentation

### POST /api/v1/users/register
**Request**:
```json
{
    "userName": "John Doe",
    "email": "john@example.com",
    "phoneNumber": "9876543210",
    "gender": "male",
    "userImageOptional": "https://example.com/image.jpg"
}
```

**Response** (201 Created):
```json
{
    "message": "User registered successfully. Please check your email for verification code.",
    "user_id": "uuid",
    "user_email": "john@example.com"
}
```

### POST /api/v1/users/verify-otp
**Request**:
```json
{
    "email": "john@example.com",
    "otpCode": "123456"
}
```

**Response** (200 OK):
```json
{
    "message": "Email verified successfully. Your account is now active.",
    "user_id": "uuid",
    "user_email": "john@example.com"
}
```

---

## Next Steps

1. ✅ Verify email in AWS SES
2. ✅ Update .env file
3. ✅ Restart FastAPI server
4. ✅ Test registration endpoint
5. ✅ Check email inbox for OTP
6. ✅ Verify OTP
7. 🎉 User is now registered and verified!
