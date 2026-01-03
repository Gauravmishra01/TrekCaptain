from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import boto3
from botocore.exceptions import ClientError

router = APIRouter()


class UserResponse(BaseModel):
	user_id: str
	user_name: str
	user_email: EmailStr
	user_number: str
	user_gender: str
	user_image_optional: Optional[str] = None
	user_verify: bool
	created_at: int


def get_dynamodb_resource():
	session = boto3.Session()
	return session.resource("dynamodb", region_name="ap-south-1")


@router.get("/{user_id}", response_model=UserResponse, tags=["users"])
def get_user_by_id(user_id: str):
	"""Retrieve a user by `user_id` from the TravelAppUsers DynamoDB table.

	The endpoint accepts `user_id` as a path parameter and returns the stored
	user attributes as a `UserResponse` model. Raises 404 if not found.
	"""
	try:
		dynamodb = get_dynamodb_resource()
		users_table = dynamodb.Table("TravelAppUsers")

		resp = users_table.get_item(Key={"user_id": user_id})
		if "Item" not in resp:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

		item = resp["Item"]

		# Normalize/validate the item for the response model
		user = UserResponse(
			user_id=item.get("user_id"),
			user_name=item.get("user_name"),
			user_email=item.get("user_email"),
			user_number=item.get("user_number"),
			user_gender=item.get("user_gender"),
			user_image_optional=item.get("user_image_optional"),
			user_verify=item.get("user_verify", False),
			created_at=item.get("created_at", 0),
		)

		return user

	except ClientError as exc:
		raise HTTPException(status_code=500, detail=f"DynamoDB error: {exc.response.get('Error', {}).get('Message', str(exc))}")
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(status_code=500, detail=str(exc))

