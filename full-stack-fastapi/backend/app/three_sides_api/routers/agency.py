from fastapi import APIRouter,Query, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import datetime
import random
import time
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import boto3





router = APIRouter()

# -------------------- STATUS API --------------------
@router.get("/status", tags=["agencies"])
async def agency_status():
    return {"message": "Agency API online"}


# -------------------- REQUEST MODEL --------------------
class AgencyRegistration(BaseModel):
    legal_name: Optional[str] = None   # NOT unique, optional
    trade_name: str = Field(..., description="Unique trade name")
    country: str
    business_address: str
    entity_type: str
    primary_category: str
    inventory_focus: Optional[List[str]] = []
    technical_need: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    bank_account: Optional[str] = None
    initial_deposit: Optional[float] = None
    contact_name: Optional[str] = None
    contact_designation: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_mobile: Optional[str] = None


class LoginRequest(BaseModel):
    trade_name: str = Field(..., description="Registered trade name of agency")


class OTPVerifyRequest(BaseModel):
    trade_name: str = Field(..., description="Registered trade name of agency")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

class EmailLoginRequest(BaseModel):
    email: EmailStr
    
class EmailOTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

 # -------------------- TREK PACKAGE MODEL --------------------   

class AgencyTrekPackageCreate(BaseModel):
    agency_id: str       
    trek_id: str
    price_rupee: float
    start_date: str
    end_date: str
    capacity: int



# -------------------- DYNAMODB CONNECTION --------------------
def get_dynamodb_resource():
    session = boto3.Session()
    return session.resource("dynamodb", region_name="ap-south-1")


# -------------------- REGISTER AGENCY --------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_agency(payload: AgencyRegistration):
    agency_id = str(uuid.uuid4())
    trade_name_key = payload.trade_name.strip().lower()

    item = {
        "trade_name_key": trade_name_key,  # 🔐 UNIQUE
        "agency_id": agency_id,
        "trade_name": payload.trade_name,
        "legal_name": payload.legal_name,
        "country": payload.country,
        "business_address": payload.business_address,
        "entity_type": payload.entity_type,
        "primary_category": payload.primary_category,
        "contact_email": payload.contact_email,
        "created_at": int(datetime.utcnow().timestamp())
    }

    try:
        table = get_dynamodb_resource().Table("TravelAppAgency")

        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(trade_name_key)"
        )

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=409,
                detail="Trade name already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Agency registered successfully",
        "user_id": agency_id
    }
# -------------------- GET AGENCY BY TRADE NAME --------------------
@router.get( "/{trade_name}",status_code=status.HTTP_200_OK,tags=["agencies"])
def get_agency_by_trade_name(trade_name: str):
    """
    Get agency details by trade_name (case-insensitive).
    """

    # Normalize (same logic as register)
    trade_name_key = trade_name.strip().lower()

    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table("TravelAppAgency")

        response = table.get_item(
            Key={
                "trade_name_key": trade_name_key
            }
        )

        if "Item" not in response:
            raise HTTPException(
                status_code=404,
                detail="Agency not found"
            )

        return {
            "message": "Agency fetched successfully",
            "data": response["Item"]
        }

    except ClientError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"DynamoDB error: {exc.response['Error']['Message']}"
        )

# -------------------- LOGIN WITH OTP --------------------

def generate_otp():
    return str(random.randint(100000, 999999))

def send_email_internal(to_email: str, subject: str, message: str):
    import smtplib, os
    from email.mime.text import MIMEText

    EMAIL_USER = "princepratapfreelancer@gmail.com"
    EMAIL_PASSWORD = "bnqg tmsx xfzr gney"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


@router.post("/login", tags=["auth"])
def login_with_otp(payload: LoginRequest):

    trade_name_key = payload.trade_name.strip().lower()

    agency_table = get_dynamodb_resource().Table("TravelAppAgency")
    otp_table = get_dynamodb_resource().Table("AgencyOTP")

    # 1️⃣ Get agency
    response = agency_table.get_item(
        Key={"trade_name_key": trade_name_key}
    )

    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Agency not found")

    agency = response["Item"]
    email = agency.get("contact_email")

    if not email:
        raise HTTPException(status_code=400, detail="Agency email not found")

    # 2️⃣ Generate OTP
    otp = generate_otp()
    expires_at = int(datetime.utcnow().timestamp()) + 300  # 5 min

    # 3️⃣ Save OTP
    otp_table.put_item(
        Item={
            "trade_name_key": trade_name_key,
            "otp": otp,
            "expires_at": expires_at
        }
    )

    # 4️⃣ Send Email
    send_email_internal(
        to_email=email,
        subject="Your Login OTP",
        message=f"Your OTP is {otp}. Valid for 5 minutes."
    )

    return {"message": "OTP sent to registered email"}

# -------------------- VERIFY OTP --------------------
@router.post("/verify-otp", tags=["auth"])
def verify_otp(payload: OTPVerifyRequest):

    trade_name_key = payload.trade_name.strip().lower()

    otp_table = get_dynamodb_resource().Table("AgencyOTP")

    response = otp_table.get_item(
        Key={"trade_name_key": trade_name_key}
    )

    if "Item" not in response:
        raise HTTPException(status_code=400, detail="OTP not found")

    record = response["Item"]

    if record["otp"] != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if int(datetime.utcnow().timestamp()) > record["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    # 🔥 Delete OTP after success
    otp_table.delete_item(
        Key={"trade_name_key": trade_name_key}
    )

    return {
        "message": "Login successful",
        "trade_name": payload.trade_name
    }

# -------------------- LOGIN WITH EMAIL --------------------

@router.post("/login-email", tags=["auth"])
def login_with_email(payload: EmailLoginRequest):

    email = payload.email.lower().strip()

    agency_table = get_dynamodb_resource().Table("TravelAppAgency")
    otp_table = get_dynamodb_resource().Table("AgencyOTP")

    # 🔍 Find agency by email (SCAN because email is not PK)
    response = agency_table.scan(
        FilterExpression="contact_email = :email",
        ExpressionAttributeValues={
            ":email": email
        }
    )

    if not response.get("Items"):
        raise HTTPException(status_code=404, detail="Agency not found")

    agency = response["Items"][0]
    trade_name_key = agency["trade_name_key"]

    # 🔐 Generate OTP
    otp = generate_otp()
    expires_at = int(datetime.utcnow().timestamp()) + 300  # 5 min

    # 💾 Save OTP
    otp_table.put_item(
        Item={
            "login_key": email,   # PK
            "otp": otp,
            "expires_at": expires_at,
            "trade_name_key": trade_name_key
        }
    )

    # 📧 Send Email
    send_email_internal(
        to_email=email,
        subject="Your Login OTP",
        message=f"Your OTP is {otp}. Valid for 5 minutes."
    )

    return {
        "message": "OTP sent to agency email"
    }

@router.post("/verify-email-otp", tags=["auth"])
def verify_email_otp(payload: EmailOTPVerifyRequest):

    email = payload.email.lower().strip()
    otp_table = get_dynamodb_resource().Table("AgencyOTP")

    response = otp_table.get_item(
        Key={"login_key": email}
    )

    if "Item" not in response:
        raise HTTPException(status_code=400, detail="OTP not found")

    record = response["Item"]

    if record["otp"] != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if int(datetime.utcnow().timestamp()) > record["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    # 🧹 Delete OTP after success
    otp_table.delete_item(
        Key={"login_key": email}
    )

    return {
        "message": "Login successful",
        "trade_name_key": record["trade_name_key"]
    }

# -------------------- ADD TREK PACKAGE --------------------
@router.post(
    "/agency/trek-package",
    status_code=status.HTTP_201_CREATED,
    tags=["agency-trek-packages"]
)
def add_trek_package_to_agency(payload: AgencyTrekPackageCreate):
    try:
        table = get_dynamodb_resource().Table("AgencyTrekPackages")

        package_id = str(uuid.uuid4())

        table.put_item(
            Item={
                "agency_id": payload.agency_id,   # 👈 from body
                "package_id": package_id,
                "trek_id": payload.trek_id,
                "price_rupee": Decimal(str(payload.price_rupee)),
                "start_date": payload.start_date,
                "end_date": payload.end_date,
                "capacity": payload.capacity,
                "status": "active",
                "created_at": int(time.time())
            }
        )

        return {
            "message": "Trek package added successfully",
            "package_id": package_id,
            "agency_id": payload.agency_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# -------------------- GET TREK PACKAGES FOR AGENCY --------------------


def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@router.get(
    "/agency/trek-packages",
    status_code=status.HTTP_200_OK,
    tags=["agency-trek-packages"]
)
def get_agency_trek_packages(
    agency_id: str = Query(..., description="Agency ID")
):
    try:
        table = get_dynamodb_resource().Table("AgencyTrekPackages")

        response = table.query(
            KeyConditionExpression=Key("agency_id").eq(agency_id)
        )

        items = convert_decimal(response.get("Items", []))

        return {
            "agency_id": agency_id,
            "count": len(items),
            "trek_packages": items
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- GET AGENCIES FOR A TREK --------------------



@router.get(
    "/trek/agencies",
    status_code=status.HTTP_200_OK,
    tags=["trek-agencies"]
)
def get_agencies_by_trek(
    trek_id: str = Query(..., description="Trek ID")
):
    try:
        table = get_dynamodb_resource().Table("AgencyTrekPackages")

        response = table.query(
            IndexName="trek_id-index",   # 👈 GSI
            KeyConditionExpression=Key("trek_id").eq(trek_id)
        )

        items = convert_decimal(response.get("Items", []))

        return {
            "trek_id": trek_id,
            "count": len(items),
            "agencies": items
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
