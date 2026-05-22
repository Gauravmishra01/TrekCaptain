import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import select

from app.core import security
from app.core.config import settings
from app.api.deps import SessionDep
from app.models import AgencyRegistration, AgencyRegistrationPublic, Message
from app.utils import generate_login_otp_email, send_email

router = APIRouter(prefix="/agencies", tags=["agencies"])


class EmailLoginRequest(BaseModel):
    email: EmailStr


class EmailLoginResponse(Message):
    verification_token: str


class EmailOtpVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(alias="otpCode")
    verification_token: str = Field(alias="verificationToken")

    class Config:
        populate_by_name = True


class AgencyRegistrationRequest(BaseModel):
    legal_name: str | None = None
    trade_name: str | None = None
    country: str | None = None
    business_address: str | None = None
    entity_type: str | None = None
    primary_category: str | None = None
    inventory_focus: list[str] = []
    technical_need: str | None = None
    gstin: str | None = None
    pan: str | None = None
    bank_account: str | None = None
    initial_deposit: float | None = None
    contact_name: str | None = None
    contact_designation: str | None = None
    contact_email: EmailStr | None = None
    contact_mobile: str | None = None


def _generate_otp() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(6))


def _generate_verification_token(*, email: str, otp_code: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {"sub": email, "otp": otp_code, "exp": expires_at}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=security.ALGORITHM)


@router.post("/login-email", response_model=EmailLoginResponse)
def login_email(payload: EmailLoginRequest) -> EmailLoginResponse:
    otp_code = _generate_otp()
    verification_token = _generate_verification_token(email=payload.email, otp_code=otp_code)
    email_data = generate_login_otp_email(email_to=payload.email, otp_code=otp_code)
    send_email(
        email_to=payload.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return EmailLoginResponse(
        message="OTP sent to email address",
        verification_token=verification_token,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=AgencyRegistrationPublic)
def register_agency(*, session: SessionDep, payload: AgencyRegistrationRequest) -> Any:
    """
    Compatibility endpoint for the agency registration HTML form.

    The form posts a multi-step payload directly to /api/v1/agencies/register.
    Keep this route lightweight so the current frontend can complete submission
    without depending on the older DynamoDB-based onboarding flow.
    """

    db_agency = AgencyRegistration.model_validate(payload)
    session.add(db_agency)
    session.commit()
    session.refresh(db_agency)
    return db_agency


@router.get("/registrations", response_model=list[AgencyRegistrationPublic])
def read_agency_registrations(
    *, session: SessionDep, skip: int = 0, limit: int = 10
) -> Any:
    statement = (
        select(AgencyRegistration)
        .order_by(AgencyRegistration.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.post("/verify-email-otp", response_model=Message)
def verify_email_otp(payload: EmailOtpVerifyRequest) -> Message:
    try:
        decoded = jwt.decode(
            payload.verification_token,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        ) from exc

    if decoded.get("sub") != payload.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email mismatch")
    if decoded.get("otp") != payload.otp_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    return Message(message="OTP verified successfully")
