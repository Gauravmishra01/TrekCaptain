from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import boto3

S3_BUCKET = "gowithdaddy-images"
S3_REGION = "ap-south-1"

s3_client = boto3.client(
    "s3",
    region_name=S3_REGION
)

router = APIRouter()


@router.post("/upload/image", tags=["uploads"])
async def upload_image_to_s3(file: UploadFile = File(...)):
    try:
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(status_code=400, detail="Invalid image type")

        file_ext = file.filename.split(".")[-1]
        file_key = f"treks/{uuid.uuid4()}.{file_ext}"

        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            file_key,
            ExtraArgs={
                "ContentType": file.content_type
                # ❌ ACL removed
            }
        )

        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file_key}"

        return {
            "message": "Image uploaded successfully",
            "image_url": file_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
