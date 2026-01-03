from fastapi import APIRouter
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import datetime
import random
from fastapi import APIRouter, HTTPException
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Attr


router = APIRouter(tags=["categories"])

# -------------------- STATUS API --------------------

@router.get("/status", tags=["admin"])  # mounted at /api/v1/admin/status
async def admin_status():
    return {"message": "Admin API online"}


# -------------------- REQUEST MODEL --------------------

class CategoryCreate(BaseModel):
    category_name: str = Field(..., example="Trekking")
    image_url: Optional[str] = None
    description: Optional[str] = None
    type: str = Field(..., example="TREK")   # TREK / AGENCY / ACTIVITY
    priority: Optional[int] = 1
    is_featured: Optional[bool] = False
    status: Optional[str] = "ACTIVE"






# -------------------- DYNAMODB CONNECTION --------------------
def get_dynamodb_resource():
    session = boto3.Session()
    return session.resource("dynamodb", region_name="ap-south-1")





@router.post("/categories")
def add_category(payload: CategoryCreate):
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table("Categories")

    # Duplicate check
    response = table.scan(
        FilterExpression=Attr("category_name").eq(payload.category_name)
    )

    if response.get("Items"):
        raise HTTPException(
            status_code=400,
            detail="Category already exists"
        )

    category_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    slug = payload.category_name.lower().replace(" ", "-")

    item = {
        "category_id": category_id,
        "category_name": payload.category_name,
        "slug": slug,
        "image_url": payload.image_url,
        "description": payload.description,
        "type": payload.type,
        "priority": payload.priority,
        "is_featured": payload.is_featured,
        "status": payload.status,
        "created_at": now,
        "updated_at": now
    }

    table.put_item(Item=item)

    return {
        "message": "Category added successfully",
        "category": item
    }


@router.get("/categories")
def get_all_categories():
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table("Categories")

    categories = []
    response = table.scan()
    categories.extend(response.get("Items", []))

    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        categories.extend(response.get("Items", []))

    return {
        "total": len(categories),
        "categories": categories
    }
