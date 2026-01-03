from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, Field, EmailStr
from typing import Tuple
import uuid
import os
import boto3
import jwt
import secrets
from datetime import datetime, timedelta

router = APIRouter()

# ================= CONFIG =================

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
JWT_SECRET = os.getenv("JWT_SECRET", "wsertyui")  # ⚠️ set in env
JWT_ALGO = "HS256"

# ================= DB =================

def get_dynamodb_resource():
    return boto3.resource("dynamodb", region_name=AWS_REGION)

# ================= STATUS =================

@router.get("/status", tags=["users"])
async def user_status():
    return {"message": "User API online"}

# ================= JWT =================

def create_token(user_id: str, verified: bool, minutes: int):
    payload = {
        "user_id": user_id,
        "verified": verified,
        "exp": datetime.utcnow() + timedelta(minutes=minutes)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

# ================= OTP =================

def generate_otp_and_expiration(
    length: int = 6,
    expires_in_minutes: int = 5
) -> Tuple[str, int]:

    otp_code = "".join(str(secrets.randbelow(10)) for _ in range(length))
    expires_at = int(
        (datetime.utcnow() + timedelta(minutes=expires_in_minutes)).timestamp()
    )
    return otp_code, expires_at

# ================= MODELS =================

class UserRegisterRequest(BaseModel):
    user_name: str = Field(..., alias="userName")
    user_number: str = Field(..., alias="phoneNumber")
    user_gender: str = Field(..., alias="gender")

    class Config:
        populate_by_name = True


class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(..., alias="phoneNumber")
    otp_code: str = Field(..., alias="otpCode")

    class Config:
        populate_by_name = True

# ================= REGISTER =================

@router.post("/register", status_code=status.HTTP_201_CREATED, tags=["users"])
def register_user(payload: UserRegisterRequest):

    user_id = str(uuid.uuid4())
    dynamodb = get_dynamodb_resource()

    users_table = dynamodb.Table("TravelAppUsers")
    otp_table = dynamodb.Table("OTPVerification")

    # Save user
    users_table.put_item(
        Item={
            "user_id": user_id,
            "user_name": payload.user_name,
            "phone_number": payload.user_number,
            "gender": payload.user_gender,
            "is_verified": False,
            "created_at": int(datetime.utcnow().timestamp())
        }
    )

    # Generate OTP
    otp, expiry = generate_otp_and_expiration()

    otp_table.put_item(
        Item={
            "phone_number": payload.user_number,
            "otp_code": otp,
            "expires_at": expiry,
            "user_id": user_id
        }
    )

    # SMS later (SNS / Twilio)
    print(f"[OTP SENT] {otp} -> {payload.user_number}")

    temp_token = create_token(user_id, verified=False, minutes=10)

    return {
        "message": "OTP sent to phone number",
        "token": temp_token
    }

# ================= VERIFY OTP =================

@router.post("/verify-otp", tags=["users"])
def verify_otp(
    payload: OTPVerifyRequest,
    authorization: str = Header(...)
):

    token = authorization.replace("Bearer ", "")
    decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])

    if decoded.get("verified"):
        raise HTTPException(status_code=400, detail="User already verified")

    user_id = decoded["user_id"]

    dynamodb = get_dynamodb_resource()
    users_table = dynamodb.Table("TravelAppUsers")
    otp_table = dynamodb.Table("OTPVerification")

    # ✅ FAST lookup by PK
    response = otp_table.get_item(
        Key={"phone_number": payload.phone_number}
    )

    if "Item" not in response:
        raise HTTPException(status_code=400, detail="OTP not found")

    otp_data = response["Item"]

    if payload.otp_code != otp_data["otp_code"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if int(datetime.utcnow().timestamp()) > otp_data["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    # Verify user
    users_table.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET is_verified = :v",
        ExpressionAttributeValues={":v": True}
    )

    # Delete OTP
    otp_table.delete_item(
        Key={"phone_number": otp_data["phone_number"]}
    )

    auth_token = create_token(
        user_id=user_id,
        verified=True,
        minutes=60 * 24 * 7  # 7 days
    )

    return {
        "message": "User verified successfully",
        "token": auth_token
    }
