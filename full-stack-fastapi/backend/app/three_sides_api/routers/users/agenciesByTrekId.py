from fastapi import APIRouter, HTTPException
from typing import List
import boto3
from boto3.dynamodb.conditions import Key

router = APIRouter()

def get_dynamodb():
    return boto3.resource("dynamodb", region_name="ap-south-1")






@router.get("/treks/{trekId}/agencies", tags=["treks"])
def get_agencies_by_trek(trekId: str):
    """
    Returns list of agencies with:
    - trade_name, logo_url (from TravelAppAgency.basic_details)
    - package_id, price_rupee (from AgencyTrekPackages)
    """
    try:
        dynamodb = get_dynamodb()

        package_table = dynamodb.Table("AgencyTrekPackages")
        agency_table_name = "TravelAppAgency"

        # 1️⃣ Fetch packages for trek
        response = package_table.query(
            IndexName="trek_id-index",
            KeyConditionExpression=Key("trek_id").eq(trekId)
        )

        packages = response.get("Items", [])
        if not packages:
            return {
                "trekId": trekId,
                "totalAgencies": 0,
                "agencies": []
            }

        # 2️⃣ Fetch agency details (batch)
        agency_ids = list({pkg["agency_id"] for pkg in packages})
        keys = [{"agency_id": aid} for aid in agency_ids]

        batch_response = dynamodb.batch_get_item(
            RequestItems={
                agency_table_name: {
                    "Keys": keys,
                    "ProjectionExpression": "agency_id, basic_details"
                }
            }
        )

        agency_items = batch_response["Responses"].get(agency_table_name, [])
        agency_map = {
            a["agency_id"]: a.get("basic_details", {})
            for a in agency_items
        }

        # 3️⃣ Merge package + agency data (✅ FIXED)
        result = []
        for pkg in packages:
            basic = agency_map.get(pkg["agency_id"], {})
            price = pkg.get("price_rupee")

            result.append({
                "agency_id": pkg["agency_id"],
                "trade_name": basic.get("trade_name"),
                "logo_url": basic.get("logo_url"),
                "package_id": pkg.get("package_id"),
                "price_rupee": int(price) if price is not None else None
            })

        return {
            "trekId": trekId,
            "totalAgencies": len(result),
            "agencies": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))