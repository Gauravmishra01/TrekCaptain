# Travel App User Registration with AWS SES - Implementation Summary

## Overview
FastAPI user registration and OTP email verification using AWS DynamoDB and AWS SES.

---

## Architecture

### Database Tables
1. **TravelAppUsers** - Main user table
   - Partition Key: `user_id`
   - Attributes: user_name, user_email, user_number, user_gender, user_image_optional, user_verify, created_at

2. **OTPVerification** - OTP storage with TTL
   - Partition Key: `user_email`
   - Attributes: otp_code, expiration, user_id
   - TTL: Auto-deletes after 5 minutes

---

## API Endpoints

### 1. POST /api/v1/users/register
**Create new user and send OTP via email**

**Request Body**:
```json
{
    "userName": "Prince Pratap",
    "email": "princepratapfreelancer@gmail.com",
    "phoneNumber": "7428839202",
    "gender": "male",
    "userImageOptional": "https://example.com/image.jpg"
}
```

**Response (201 Created)**:
```json
{
    "message": "User registered successfully. Please check your email for verification code.",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_email": "princepratapfreelancer@gmail.com"
}
```

**Process**:
1. Generate unique `user_id` (UUID)
2. Set `user_verify = False`
3. Save user to `TravelAppUsers` table
4. Generate 6-digit OTP
5. Save OTP to `OTPVerification` table with 5-min expiration
6. Send email via AWS SES with OTP
7. Return 201 with user_id

---

### 2. POST /api/v1/users/verify-otp
**Verify OTP and activate user account**

**Request Body**:
```json
{
    "email": "princepratapfreelancer@gmail.com",
    "otpCode": "123456"
}
```

**Response (200 OK)**:
```json
{
    "message": "Email verified successfully. Your account is now active.",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_email": "princepratapfreelancer@gmail.com"
}
```

**Process**:
1. Retrieve OTP record from `OTPVerification` table
2. Validate OTP code matches stored value
3. Validate OTP hasn't expired
4. Update `user_verify = True` in `TravelAppUsers`
5. Delete OTP record from `OTPVerification`
6. Return 200 success

**Error Responses**:
- 400: No OTP found (user not registered)
- 400: Incorrect OTP code
- 400: OTP expired
- 500: Database/SES errors

---

## Implementation Details

### Part 1: Helper Functions

#### generate_otp_and_expiration()
```python
def generate_otp_and_expiration(length: int = 6) -> tuple[str, int]:
    """Generate 6-digit OTP and 5-minute expiration timestamp"""
    otp = "".join([str(secrets.randbelow(10)) for _ in range(length)])
    expiration = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())
    return otp, expiration
```

#### send_verification_email()
```python
def send_verification_email(recipient_email: str, otp_code: str) -> bool:
    """Send OTP email via AWS SES with HTML and plain-text body"""
    # Uses boto3 SES client
    # Handles ClientError exceptions
    # Returns bool indicating success
```

### Part 2: Pydantic Models

#### UserRegisterRequest
- `user_name` (required, str)
- `user_email` (required, EmailStr with alias "email")
- `user_number` (required, str)
- `user_gender` (required, str)
- `user_image_optional` (optional, str)

#### OTPVerifyRequest
- `user_email` (required, EmailStr)
- `otp_code` (required, str)

### Part 3: Configuration

```python
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "no-reply@your-travel-app.com")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
```

---

## Setup Instructions

### Step 1: Verify Email in AWS SES
1. Go to AWS SES Console (ap-south-1 region)
2. Email Addresses → Verify a New Email Address
3. Enter: `no-reply@your-travel-app.com`
4. Click link in verification email

### Step 2: Create .env File
```
SENDER_EMAIL=no-reply@your-travel-app.com
AWS_REGION=ap-south-1
```

### Step 3: Create DynamoDB Tables
```bash
cd backend
python setup_dynamodb.py
```

### Step 4: Start FastAPI Server
```bash
uvicorn app.three_sides_api.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 5: Test Endpoints
See examples in AWS_SES_SETUP.md

---

## Error Handling

### Registration Errors
- 500: Database connection failed
- 500: SES email sending failed (but OTP still saved)
- 422: Invalid request body (validation error)

### Verification Errors
- 400: No OTP found for email
- 400: Incorrect OTP code
- 400: OTP expired
- 500: Database update failed

---

## Security Features

✅ **Email Validation**: EmailStr ensures valid email format  
✅ **OTP Expiration**: 5-minute TTL on OTP records  
✅ **Auto-Delete**: DynamoDB TTL auto-deletes expired OTPs  
✅ **Unique IDs**: UUID ensures unique user_id  
✅ **Error Handling**: Proper HTTP status codes and messages  
✅ **Async Support**: Ready for async email queue (future enhancement)  

---

## Files Modified

1. `app/three_sides_api/routers/user.py`
   - Registration endpoint with SES integration
   - OTP verification endpoint
   - Helper functions for OTP generation and email sending

2. `.env`
   - AWS SES configuration

3. `.env.example`
   - Configuration template

4. `setup_dynamodb.py`
   - Creates both TravelAppUsers and OTPVerification tables

5. `app/three_sides_api/main.py`
   - Loads .env file with python-dotenv

---

## Testing with cURL

### Register User
```powershell
curl -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/users/register" `
  -ContentType "application/json" `
  -Body (@{userName='Prince';email='prince@example.com';phoneNumber='9876543210';gender='male'} | ConvertTo-Json)
```

### Verify OTP
```powershell
curl -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/users/verify-otp" `
  -ContentType "application/json" `
  -Body (@{email='prince@example.com';otpCode='123456'} | ConvertTo-Json)
```

---

## Interactive API Documentation

Visit: http://127.0.0.1:8000/docs (Swagger UI)

- Try out endpoints interactively
- See request/response schemas
- Test with real data

---

## Database Schema Examples

### TravelAppUsers (after registration)
```json
{
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_name": "Prince Pratap",
    "user_email": "prince@example.com",
    "user_number": "9876543210",
    "user_gender": "male",
    "user_image_optional": "https://example.com/image.jpg",
    "user_verify": false,
    "created_at": 1700605632
}
```

### OTPVerification (after registration)
```json
{
    "user_email": "prince@example.com",
    "otp_code": "123456",
    "expiration": 1700605932,
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### TravelAppUsers (after verification)
```json
{
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_name": "Prince Pratap",
    "user_email": "prince@example.com",
    "user_number": "9876543210",
    "user_gender": "male",
    "user_image_optional": "https://example.com/image.jpg",
    "user_verify": true,
    "created_at": 1700605632
}
```
(OTPVerification record automatically deleted after verification)

---

## Next Steps

- [ ] Implement password reset with OTP
- [ ] Add account login endpoint
- [ ] Implement JWT token generation
- [ ] Add role-based access control (User, Agency, Admin)
- [ ] Create agency and admin registration endpoints
- [ ] Set up email templates in SES
- [ ] Implement rate limiting for OTP resend
- [ ] Add audit logging for user actions
