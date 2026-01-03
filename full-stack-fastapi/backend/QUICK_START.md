# Quick Start Guide - Travel App User Registration with AWS SES

## 5-Minute Setup

### 1. Verify Email in AWS SES (2 minutes)
- Open: https://console.aws.amazon.com/ses/
- Region: **ap-south-1** (top right)
- **Email Addresses** → **Verify a New Email Address**
- Enter: `no-reply@your-travel-app.com`
- Check your email for verification link and click it

### 2. Create .env File (1 minute)
Create file: `backend/.env`
```
SENDER_EMAIL=no-reply@your-travel-app.com
AWS_REGION=ap-south-1
```

### 3. Create DynamoDB Tables (1 minute)
```powershell
cd backend
python setup_dynamodb.py
```

### 4. Start Server (1 minute)
```powershell
uvicorn app.three_sides_api.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Test Registration & Verification

### Step 1: Register User
```powershell
$body = @{
    userName = "Prince Pratap"
    email = "princepratapfreelancer@gmail.com"
    phoneNumber = "7428839202"
    gender = "male"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/users/register" `
  -ContentType "application/json" `
  -Body $body
```

**Response**:
```json
{
    "message": "User registered successfully. Please check your email for verification code.",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_email": "princepratapfreelancer@gmail.com"
}
```

### Step 2: Check Email
- Open your inbox at `princepratapfreelancer@gmail.com`
- Look for email from `no-reply@your-travel-app.com`
- Copy the 6-digit OTP code

### Step 3: Verify OTP
Replace `XXXXXX` with the OTP from your email:
```powershell
$body = @{
    email = "princepratapfreelancer@gmail.com"
    otpCode = "XXXXXX"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/users/verify-otp" `
  -ContentType "application/json" `
  -Body $body
```

**Response**:
```json
{
    "message": "Email verified successfully. Your account is now active.",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_email": "princepratapfreelancer@gmail.com"
}
```

---

## Done! 🎉

Your user is now registered and verified in DynamoDB!

**Check the data:**
```powershell
aws dynamodb scan --table-name TravelAppUsers --region ap-south-1
```

---

## API Documentation

**Interactive Docs**: http://127.0.0.1:8000/docs

---

## Troubleshooting

### ❌ "MessageRejected" Error
**Problem**: Email not verified in SES
**Solution**: Go to AWS SES console and verify `no-reply@your-travel-app.com`

### ❌ Email Not Received
**Problem**: SES is in Sandbox mode
**Solution**: 
1. Verify recipient email in SES, OR
2. Request production access in SES console

### ❌ Connection to DynamoDB Failed
**Problem**: AWS credentials not configured
**Solution**: Check `~/.aws/credentials` file has your AWS keys

---

## Files Created/Modified

✅ `app/three_sides_api/routers/user.py` - Registration & OTP endpoints  
✅ `.env` - AWS SES config  
✅ `.env.example` - Config template  
✅ `setup_dynamodb.py` - Database setup  
✅ `app/three_sides_api/main.py` - Load .env  

---

## Next Steps

- Implement login with JWT
- Add password reset
- Create Agency registration
- Create Admin dashboard

See `USER_REGISTRATION_GUIDE.md` for full documentation.
