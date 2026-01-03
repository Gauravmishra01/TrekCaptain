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

    # -------------------- DYNAMODB CONNECTION --------------------
def get_dynamodb_resource():
    session = boto3.Session()
    return session.resource("dynamodb", region_name="ap-south-1")


#  Step 1-------------------- AGENCY REGISTRATION: BASIC DETAILS --------------------
class AgencyBasicDetails(BaseModel):
    trade_name: str
    logo_url: Optional[str] = None
    owner_name: str
    email: EmailStr
    mobile: str
    year_of_establishment: Optional[int] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None


@router.post("/register/basic", status_code=201)
def register_basic_details(payload: AgencyBasicDetails):
    agency_id = str(uuid.uuid4())

    item = {
        "agency_id": agency_id,
        "trade_name_key": payload.trade_name.lower(),
        "basic_details": payload.dict(),
        "onboarding_step": 1,
        "verification_status": "PENDING",
        "created_at": int(datetime.utcnow().timestamp())
    }

    table = get_dynamodb_resource().Table("TravelAppAgency")

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(trade_name_key)"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(409, "Agency already exists")
        raise HTTPException(500, str(e))

    return {
        "message": "Basic details saved",
        "agency_id": agency_id
    }

#  Step 2-------------------- AGENCY REGISTRATION: ADDRESS DETAILS --------------------
class AgencyAddress(BaseModel):
    registered_address: str
    operating_address: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str
    google_map_url: Optional[str] = None

@router.put("/register/{agency_id}/address")
def update_address(agency_id: str, payload: AgencyAddress):
    table = get_dynamodb_resource().Table("TravelAppAgency")

    table.update_item(
        Key={"agency_id": agency_id},
        UpdateExpression="""
            SET address_details = :addr,
                onboarding_step = :step
        """,
        ExpressionAttributeValues={
            ":addr": payload.dict(),
            ":step": 2
        }
    )

    return {"message": "Address details updated"}

#  Step 3-------------------- AGENCY REGISTRATION: KYC DETAILS --------------------

class AgencyKYC(BaseModel):
    aadhaar_url: Optional[str] = None
    pan_url: Optional[str] = None
    passport_or_voter_url: Optional[str] = None
    gst_number: Optional[str] = None
    gst_certificate_url: Optional[str] = None
    trade_license_url: Optional[str] = None
    company_registration_url: Optional[str] = None

@router.put("/register/{agency_id}/kyc")
def update_kyc(agency_id: str, payload: AgencyKYC):
    table = get_dynamodb_resource().Table("TravelAppAgency")

    table.update_item(
        Key={"agency_id": agency_id},
        UpdateExpression="""
            SET kyc_details = :kyc,
                onboarding_step = :step
        """,
        ExpressionAttributeValues={
            ":kyc": payload.dict(),
            ":step": 3
        }
    )

    return {"message": "KYC details updated"}

#  Step 4-------------------- AGENCY REGISTRATION: BANK DETAILS --------------------
class AgencyBankDetails(BaseModel):
    account_holder_name: str
    bank_name: str
    account_number: str
    ifsc_code: str
    cancelled_cheque_url: Optional[str] = None
    upi_id: Optional[str] = None

@router.put("/register/{agency_id}/bank")
def update_bank(agency_id: str, payload: AgencyBankDetails):
    table = get_dynamodb_resource().Table("TravelAppAgency")

    table.update_item(
        Key={"agency_id": agency_id},
        UpdateExpression="""
            SET bank_details = :bank,
                onboarding_step = :step
        """,
        ExpressionAttributeValues={
            ":bank": payload.dict(),
            ":step": 4
        }
    )

    return {"message": "Bank details updated"}

#  Step 5-------------------- AGENCY REGISTRATION: SERVICES DETAILS --------------------
class AgencyServices(BaseModel):
    services: List[str]
    regions: List[str]
    trek_locations: Optional[List[str]] = []
    experience_level: List[str]
    languages: List[str]

@router.put("/register/{agency_id}/services")
def update_services(agency_id: str, payload: AgencyServices):
    table = get_dynamodb_resource().Table("TravelAppAgency")

    table.update_item(
        Key={"agency_id": agency_id},
        UpdateExpression="""
            SET service_details = :services,
                onboarding_step = :step
        """,
        ExpressionAttributeValues={
            ":services": payload.dict(),
            ":step": 5
        }
    )

    return {"message": "Service details updated"}

#  Step 6-------------------- AGENCY REGISTRATION: ADMIN VERIFICATION --------------------

class AdminVerification(BaseModel):
    status: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    commission_percent: float = Field(..., ge=0, le=100)
    internal_notes: Optional[str] = None


@router.put("/admin/{agency_id}/verify", status_code=status.HTTP_200_OK)
def admin_verify_agency(
    agency_id: str,
    payload: AdminVerification
):
    table = get_dynamodb_resource().Table("TravelAppAgency")

    try:
        table.update_item(
            Key={"agency_id": agency_id},
            UpdateExpression="""
                SET verification_status = :status,
                    commission_percent = :commission,
                    internal_notes = :notes,
                    onboarding_completed = :completed,
                    verified_at = :verified_at
            """,
            ConditionExpression="attribute_exists(agency_id)",
            ExpressionAttributeValues={
                ":status": payload.status,
                ":commission": Decimal(str(payload.commission_percent)),
                ":notes": payload.internal_notes,
                ":completed": True,
                ":verified_at": int(datetime.utcnow().timestamp())
            }
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=404,
                detail="Agency not found"
            )
        raise HTTPException(
            status_code=500,
            detail="Failed to verify agency"
        )

    return {
        "message": f"Agency {payload.status.lower()} successfully",
        "agency_id": agency_id,
        "verification_status": payload.status
    }

# -------------------- FETCH AGENCY DETAILS --------------------
@router.get("/register/{agency_id}", status_code=status.HTTP_200_OK)
def get_agency_full_details(agency_id: str):
    table = get_dynamodb_resource().Table("TravelAppAgency")

    try:
        response = table.get_item(
            Key={"agency_id": agency_id}
        )
    except ClientError:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch agency details"
        )

    if "Item" not in response:
        raise HTTPException(
            status_code=404,
            detail="Agency not found"
        )

    return {
        "message": "Agency details fetched successfully",
        "data": response["Item"]
    }

