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
from boto3.dynamodb.conditions import Attr
from fastapi import Query


router = APIRouter()

# -------------------- STATUS API --------------------
@router.get("/status", tags=["agencies"])
async def agency_status():
    return {"message": "Agency API online"}

# -------------------- DYNAMODB CONNECTION --------------------
def get_dynamodb_resource():
    session = boto3.Session()
    return session.resource("dynamodb", region_name="ap-south-1")

# -------------------- AGENCY TREK PACKAGE CREATION --------------------
class PackageItineraryDay(BaseModel):
    day: int
    title: str
    description: str
class CategoryTag(BaseModel): 
    category_id: str 
    category_name: str



class AgencyTrekPackageCreate(BaseModel):
    agency_id: str
    trek_id: str
    packege_name: str
    base_price_rupee: float
    description: str

    why_choose_this_trek: List[str]
    whats_included: List[str]
    whats_not_included: List[str]
    cancellation_policy: str

    total_days: int
    total_nights: int

    itinerary: List[PackageItineraryDay]
    category: List[CategoryTag] = None


#-------------------- CREATE AGENCY TREK PACKAGE --------------------
@router.post(
    "/agency/trek-package",
    status_code=status.HTTP_201_CREATED,
    tags=["agency-trek-packages"]
)
def create_agency_trek_package(payload: AgencyTrekPackageCreate):

    table = get_dynamodb_resource().Table("AgencyTrekPackages")
    package_id = str(uuid.uuid4())

    try:
        table.put_item(
            Item={
                "agency_id": payload.agency_id,
                "package_id": package_id,
                "trek_id": payload.trek_id,

                "base_price_rupee": Decimal(str(payload.base_price_rupee)),
                "description": payload.description,

                "why_choose_this_trek": payload.why_choose_this_trek,
                "whats_included": payload.whats_included,
                "whats_not_included": payload.whats_not_included,
                "cancellation_policy": payload.cancellation_policy,

                "total_days": payload.total_days,
                "total_nights": payload.total_nights,

                "itinerary": [day.dict() for day in payload.itinerary],
                   # ✅ SEARCH & FILTER FRIENDLY
                "category_ids": [cat.category_id for cat in payload.category] if payload.category else [],
                "category_names": [cat.category_name for cat in payload.category] if payload.category else [],
                "status": "ACTIVE",
                "created_at": int(time.time())
            }
        )

        return {
            "message": "Agency trek package created successfully",
            "package_id": package_id
        }

    except ClientError as e:
        raise HTTPException(500, e.response["Error"]["Message"])


    #-------------------- AGENCY TREK PACKAGE BATCH CREATION --------------------

class TrekPackageBatchCreate(BaseModel):
    agency_id: str
    package_id: str

    month: str
    batch_label: str

    start_date: str
    end_date: str

    price_rupee: float
    capacity: int

#-------------------- ADD BATCH TO AGENCY TREK PACKAGE --------------------

@router.post(
    "/agency/trek-package/batch",
    status_code=status.HTTP_201_CREATED,
    tags=["agency-trek-packages"]
)
def add_batch_to_package(payload: TrekPackageBatchCreate):

    table = get_dynamodb_resource().Table("AgencyTrekPackageBatches")
    batch_id = str(uuid.uuid4())

    try:
        table.put_item(
            Item={
                "package_id": payload.package_id,   # PK
                "batch_id": batch_id,               # SK
                "agency_id": payload.agency_id,

                "month": payload.month,
                "batch_label": payload.batch_label,

                "start_date": payload.start_date,
                "end_date": payload.end_date,


                "price_rupee": Decimal(str(payload.price_rupee)),
                "capacity": payload.capacity,
                "available_seats": payload.capacity,   # 👈 IMPORTANT

                "status": "OPEN",
                "created_at": int(time.time())
            }
        )

        return {
            "message": "Batch added successfully",
            "batch_id": batch_id,
            "available_seats": payload.capacity
        }

    except ClientError as e:
        raise HTTPException(500, e.response["Error"]["Message"])


#-------------------- GET AGENCY TREK PACKAGE FULL DETAILS --------------------
@router.get(
    "/agency/trek-package/{package_id}",
    status_code=status.HTTP_200_OK,
    tags=["agency-trek-packages"]
)
def get_agency_trek_package_full_details(package_id: str):

    dynamodb = get_dynamodb_resource()

    package_table = dynamodb.Table("AgencyTrekPackages")
    batch_table = dynamodb.Table("AgencyTrekPackageBatches")
    agency_table = dynamodb.Table("TravelAppAgency")

    # 1️⃣ Get package
    package_response = package_table.scan(
        FilterExpression="package_id = :pid",
        ExpressionAttributeValues={":pid": package_id}
    )

    if not package_response.get("Items"):
        raise HTTPException(status_code=404, detail="Package not found")

    package = package_response["Items"][0]
    agency_id = package["agency_id"]

    # 2️⃣ Get agency basic details (✅ FIXED)
    agency_response = agency_table.get_item(
        Key={"agency_id": agency_id}
    )

    agency_item = agency_response.get("Item", {})
    basic = agency_item.get("basic_details", {})   # 👈 IMPORTANT FIX

    # 3️⃣ Get batches
    batch_response = batch_table.scan(
        FilterExpression="package_id = :pid",
        ExpressionAttributeValues={":pid": package_id}
    )

    batches = batch_response.get("Items", [])

    # 4️⃣ Decimal → float
    def convert_decimal(obj):
        if isinstance(obj, list):
            return [convert_decimal(i) for i in obj]
        if isinstance(obj, dict):
            return {k: convert_decimal(v) for k, v in obj.items()}
        if isinstance(obj, Decimal):
            return float(obj)
        return obj

    return {
        "message": "Trek package full details fetched successfully",

        # ✅ AgencyBasicDetails (NOW CORRECT)
        "agency": convert_decimal({
            "trade_name": basic.get("trade_name"),
            "logo_url": basic.get("logo_url"),
            "owner_name": basic.get("owner_name"),
            "email": basic.get("email"),
            "mobile": basic.get("mobile"),
            "year_of_establishment": basic.get("year_of_establishment"),
            "website": basic.get("website"),
            "instagram": basic.get("instagram"),
            "facebook": basic.get("facebook"),
        }),

        "package": convert_decimal(package),
        "batches": convert_decimal(batches)
    }

#-------------------- GET Package by Category ID  --------------------

@router.get(
    "/agency/trek-packages/by-category",
    status_code=status.HTTP_200_OK,
    tags=["agency-trek-packages"]
)
def get_packages_by_category(
    category_id: str = Query(..., description="Category ID to filter packages")
):
    """
    Find agency trek packages by category_id
    """

    try:
        table = get_dynamodb_resource().Table("AgencyTrekPackages")

        response = table.scan(
            FilterExpression=Attr("category_ids").contains(category_id)
        )

        items = response.get("Items", [])

        # Decimal → float
        def convert_decimal(obj):
            if isinstance(obj, list):
                return [convert_decimal(i) for i in obj]
            if isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            if isinstance(obj, Decimal):
                return float(obj)
            return obj

        items = convert_decimal(items)

        return {
            "count": len(items),
            "packages": items
        }

    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=e.response["Error"]["Message"]
        )