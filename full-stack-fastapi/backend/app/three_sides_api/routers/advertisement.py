import boto3
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl
from uuid import uuid4
from datetime import datetime
from botocore.exceptions import ClientError

router = APIRouter(
    prefix="/api/ads",
    tags=["Advertisement"]
)

# =======================
# Pydantic Schemas
# =======================

class AdvertisementCreate(BaseModel):
    ads_enabled: bool
    ads_image: HttpUrl
    banner_name: str
    banner_id: str
    agency_id: str
    package_id: str
    batch_id: str
    price_rupee: int


class AdvertisementResponse(BaseModel):
    success: bool
    message: str
    data: dict


# =======================
# DynamoDB Connection
# =======================

def get_ads_table():
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="ap-south-1"
    )
    return dynamodb.Table("advertisements")  # your table name


# =======================
# Add Advertisement API
# =======================

@router.post(
    "/add",
    response_model=AdvertisementResponse,
    status_code=status.HTTP_201_CREATED
)
def add_advertisement(payload: AdvertisementCreate):

    table = get_ads_table()

    # Check banner_id uniqueness
    try:
        response = table.get_item(
            Key={"banner_id": payload.banner_id}
        )
        if "Item" in response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Advertisement with this banner_id already exists"
            )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail="Error checking banner_id uniqueness"
        )

    ad_id = f"AD_{uuid4().hex[:8].upper()}"

    ad_item = {
        "banner_id": payload.banner_id,   # Partition Key
        "ad_id": ad_id,
        "ads_enabled": payload.ads_enabled,
        "ads_image": str(payload.ads_image),
        "banner_name": payload.banner_name,
        "agency_id": payload.agency_id,
        "package_id": payload.package_id,
        "batch_id": payload.batch_id,
        "price_rupee": payload.price_rupee,
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        table.put_item(Item=ad_item)
    except ClientError:
        raise HTTPException(
            status_code=500,
            detail="Failed to add advertisement"
        )

    return {
        "success": True,
        "message": "Advertisement added successfully",
        "data": {
            "ad_id": ad_id,
            "banner_id": payload.banner_id,
            "status": "ACTIVE" if payload.ads_enabled else "INACTIVE"
        }
    }

@router.delete(
    "/delete/{banner_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
def delete_advertisement(banner_id: str):

    table = get_ads_table()

    # Check if ad exists
    try:
        response = table.get_item(
            Key={"banner_id": banner_id}
        )
        if "Item" not in response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Advertisement not found"
            )
    except ClientError:
        raise HTTPException(
            status_code=500,
            detail="Error checking advertisement"
        )

    # Delete item
    try:
        table.delete_item(
            Key={"banner_id": banner_id}
        )
    except ClientError:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete advertisement"
        )

    return {
        "success": True,
        "message": "Advertisement deleted successfully",
        "data": {
            "banner_id": banner_id
        }
    }

# =======================
# Get All Advertisements
# =======================

@router.get(
    "/all",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
def get_all_advertisements():

    table = get_ads_table()

    try:
        response = table.scan()
        items = response.get("Items", [])

        return {
            "success": True,
            "message": "Advertisements fetched successfully",
            "data": items
        }

    except ClientError:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch advertisements"
        )
