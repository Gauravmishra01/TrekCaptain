from fastapi import APIRouter
from .agencyRegistration import router as registration_router
from .agencyPackage import router as package_router

router = APIRouter()
router.include_router(registration_router)
router.include_router(package_router)