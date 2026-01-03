from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
import uuid
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

router = APIRouter()


class TrekCreateRequest(BaseModel):
    trek_name: str
    location_city: str
    location_state: str
    duration_days: int
    low_price_rupee: float
    high_price_rupee: float
    difficulty_level: str
    description: str
    image: List[str] = Field(default_factory=list)


def get_dynamodb_resource():
    session = boto3.Session()
    return session.resource("dynamodb", region_name="ap-south-1")


@router.post("/add-trek", status_code=status.HTTP_201_CREATED, tags=["treks"])
def add_trek(payload: TrekCreateRequest):
    """Create a new trek record in the TravelTreks DynamoDB table.

    Generates a UUID `trek_id` (partition key). Converts float prices into
    `decimal.Decimal` (via string conversion) to avoid floating-point loss
    when writing to DynamoDB.
    """
    trek_id = str(uuid.uuid4())

    # Convert floats to Decimal safely (use str() to avoid binary float artifacts)
    try:
        low_price = Decimal(str(payload.low_price_rupee))
        high_price = Decimal(str(payload.high_price_rupee))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid price values: {exc}")

    item = {
        "trek_id": trek_id,
        "trek_name": payload.trek_name,
        "location_city": payload.location_city,
        "location_state": payload.location_state,
        "duration_days": payload.duration_days,
        "low_price_rupee": low_price,
        "high_price_rupee": high_price,
        "difficulty_level": payload.difficulty_level,
        "description": payload.description,
        "image": payload.image,
        "created_at": int(__import__("datetime").datetime.utcnow().timestamp()),
    }

    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table("TravelTreks")
        table.put_item(Item=item)
    except ClientError as exc:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {exc.response.get('Error', {}).get('Message', str(exc))}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"trek_id": trek_id}







def convert_decimal(obj):
    """Recursively convert Decimal to float for JSON response"""
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@router.get(
    "/treks",
    status_code=status.HTTP_200_OK,
    tags=["treks"]
)
def get_all_treks():
    """
    Fetch ALL treks from TravelTreks table (no pagination)
    """

    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table("TravelTreks")

        response = table.scan()
        items = response.get("Items", [])

        # Handle DynamoDB internal pagination automatically
        while "LastEvaluatedKey" in response:
            response = table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))

        items = convert_decimal(items)

        return {
            "count": len(items),
            "treks": items
        }

    except ClientError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"DynamoDB error: {exc.response.get('Error', {}).get('Message')}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )
