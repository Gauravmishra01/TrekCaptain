# AWS SES Production Access Request Guide

## Step-by-Step Instructions

### Step 1: Open AWS SES Console
1. Go to: https://console.aws.amazon.com/ses/
2. Make sure region is **ap-south-1** (top right)

### Step 2: Request Production Access
1. In the left sidebar, look for **Account dashboard** or **Send limits**
2. You should see a message like: "Your account is in the Amazon SES sandbox"
3. Click **Request a sending limit increase** or **Send a limit increase request**

### Step 3: Fill the Request Form
You'll see a form with these fields:

**Scenario**: Select one of these:
- ✅ **Send promotional emails** (best for travel app)
- OR **Send marketing emails**
- OR **Transaction emails**

**Desired Daily Sending Quota**: 
- Enter: **10000** (or your expected daily volume)

**Describe your use case** (copy-paste this):
```
I'm building a Travel App platform with user registration and 
verification emails using AWS SES. The application sends OTP 
(one-time password) verification codes to user email addresses 
during registration.

The emails are transactional and essential for user account activation.
```

**Will you only send to recipients who have specifically requested your mail?**
- ✅ **Yes**

**How will you handle bounces and complaints?**
- Select: **I will monitor Amazon SES logs in CloudWatch**

### Step 4: Submit Request
- Click **Request Production Access** or **Submit**
- You'll see: "Your request has been submitted"

### Step 5: Wait for Approval
- ✅ AWS reviews within **24 hours** (often much faster)
- You'll receive an **email notification** when approved
- Check your email: **princepratapfreelancer@gmail.com**

### Step 6: Verify Approval
Once approved, run this command to confirm:

```powershell
aws ses get-account-sending-enabled --region ap-south-1
```

You should see:
```
{
    "Enabled": true
}
```

---

## What Happens After Approval?

✅ **Sandbox restrictions removed:**
- Can send to ANY email address
- Daily sending limit increased
- No need to verify individual recipient emails

✅ **Your app will work:**
```
User registers → OTP sent → User receives email → User verifies
```

---

## Troubleshooting

### Can't find "Request Production Access"?
1. Go to: https://console.aws.amazon.com/ses/
2. Click **Account dashboard** (left sidebar)
3. Look for **Send quota** section
4. Click **Edit your Send quota**

### No email notification received?
1. Check Spam folder
2. Wait up to 24 hours for AWS to review
3. Check AWS console for status updates

### Request was denied?
Common reasons:
- Incomplete use case description
- Suspicious activity
- New AWS account

Contact AWS support if denied: https://console.aws.amazon.com/support/

---

## Timeline

| Time | Status |
|------|--------|
| Now | Request submitted |
| 5 mins - 24 hours | AWS reviewing |
| After approval | Email confirmation |
| Immediately | Sandbox restrictions removed |

---

## Next Steps After Approval

1. ✅ Approval email received
2. ✅ Test registration with new email: `princepratap2025@gmail.com`
3. ✅ Verify you receive the OTP email
4. ✅ Complete the full registration flow

---

## Need Help?

**AWS SES Documentation:**
https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html

**AWS Support:**
https://console.aws.amazon.com/support/
