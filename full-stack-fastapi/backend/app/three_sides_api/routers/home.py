import boto3
from fastapi import APIRouter, HTTPException, status
from botocore.exceptions import ClientError

router = APIRouter(
    prefix="/api/home",
    tags=["Home"]
)


# =======================
# DynamoDB Connection
# =======================

def get_ads_table():
    dynamodb = boto3.resource("dynamodb",region_name="ap-south-1" )
    return dynamodb.Table("advertisements")

def get_categories_table():
    dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
    return dynamodb.Table("Categories")


# =======================
# Home Page API
# =======================

@router.get("", status_code=status.HTTP_200_OK)
def home_page():

    ads_table = get_ads_table()
    categories_table = get_categories_table()

    try:
        # ---- Fetch Ads ----
        ads_response = ads_table.scan()
        ads_items = ads_response.get("Items", [])

        active_ads = [
            {
                "banner_id": ad.get("banner_id"),
                "banner_name": ad.get("banner_name"),
                "ads_image": ad.get("ads_image"),
                "agency_id": ad.get("agency_id"),
                "package_id": ad.get("package_id"),
                "price_rupee": ad.get("price_rupee")
            }
            for ad in ads_items
            if ad.get("ads_enabled") is True
        ]

        # ---- Fetch Categories ----
        categories_response = categories_table.scan()
        categories_items = categories_response.get("Items", [])

        active_categories = [
            {
                "category_id": cat.get("category_id"),
                "category_name": cat.get("category_name"),
                "image_url": cat.get("image_url")
            }
            for cat in categories_items
            if cat.get("is_featured") is True
        ]

        return {
            "success": True,
            "message": "Home page data fetched successfully",
            "data": {
                "categories": active_categories,
                "ads": active_ads
            }
        }

    except Exception as e:
        print("HOME API ERROR:", str(e))  # 👈 ADD THIS
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )