from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

# -------------------- ROUTER --------------------
router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)

# -------------------- DYNAMODB --------------------
def get_categories_table():
    dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
    return dynamodb.Table("Categories")

# -------------------- MODELS --------------------
class CategoryCreate(BaseModel):
    category_name: str = Field(..., min_length=2, max_length=50)
    image_url: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    type: str = Field(..., example="TREK")  # TREK / AGENCY / ACTIVITY
    priority: int = 1
    is_featured: bool = False
    status: str = "ACTIVE"

class CategoryResponse(BaseModel):
    category_id: str
    category_name: str
    slug: str
    image_url: Optional[str]
    description: Optional[str]
    type: str
    priority: int
    is_featured: bool
    status: str
    created_at: str
    updated_at: str

# -------------------- STATUS API --------------------
@router.get("/status", tags=["admin"])
async def admin_status():
    return {"status": "OK", "message": "Category API is live"}

# -------------------- CREATE CATEGORY --------------------
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryResponse
)
def create_category(payload: CategoryCreate):

    table = get_categories_table()

    # Normalize name & slug
    category_name = payload.category_name.strip()
    slug = category_name.lower().replace(" ", "-")

    # Check duplicate slug
    try:
        response = table.scan(
            FilterExpression=Attr("slug").eq(slug) & Attr("status").eq("ACTIVE")
        )
        if response.get("Items"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists"
            )
    except ClientError as e:
        raise HTTPException(500, e.response["Error"]["Message"])

    now = datetime.utcnow().isoformat()
    item = {
        "category_id": str(uuid.uuid4()),
        "category_name": category_name,
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

    try:
        table.put_item(Item=item)
    except ClientError as e:
        raise HTTPException(500, e.response["Error"]["Message"])

    return item

# -------------------- GET ALL CATEGORIES --------------------
@router.get("", response_model=List[CategoryResponse])
def get_categories(
    status_filter: Optional[str] = "ACTIVE",
    limit: int = 50
):
    table = get_categories_table()
    items = []

    try:
        response = table.scan(
            FilterExpression=Attr("status").eq(status_filter),
            Limit=limit
        )
        items.extend(response.get("Items", []))

        while "LastEvaluatedKey" in response and len(items) < limit:
            response = table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"],
                Limit=limit
            )
            items.extend(response.get("Items", []))

    except ClientError as e:
        raise HTTPException(500, e.response["Error"]["Message"])

    return items[:limit]

# -------------------- SOFT DELETE CATEGORY --------------------
@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(category_id: str):

    table = get_categories_table()

    try:
        table.update_item(
            Key={"category_id": category_id},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": "INACTIVE",
                ":u": datetime.utcnow().isoformat()
            }
        )
    except ClientError as e:
        raise HTTPException(500, e.response["Error"]["Message"])

    return {"message": "Category deleted successfully"}
