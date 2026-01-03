from fastapi import APIRouter, HTTPException, Query
from typing import List, Any
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

router = APIRouter()


def get_dynamodb_resource():
    session = boto3.Session()
    return session.resource("dynamodb", region_name="ap-south-1")


@router.get("/search-treks", tags=["search"])
def search_treks(
    query: str = Query(..., description="Search by trek name or location (state/base camp)")
) -> List[Any]:
    """
    Search treks by trek_name OR location.state OR location.base_camp
    """
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table("TravelTreks")

        # FilterExpression
        filter_expr = (
            Attr("trek_name").contains(query) |
            Attr("location.state").contains(query) |
            Attr("location.base_camp").contains(query)
        )

        response = table.scan(FilterExpression=filter_expr)
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=filter_expr,
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))

        return items

    except ClientError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"DynamoDB error: {exc.response.get('Error', {}).get('Message')}"
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
