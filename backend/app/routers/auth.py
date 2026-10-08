"""Registration (with email OTP confirmation) and login endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.core.config import OTP_EXPIRE_MINUTES
from backend.app.core.database import get_db
from app.email_utils import generate_otp, send_otp_email
from app.models import User
from app.schemas_auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResendOtpRequest,
    UserOut,
    VerifyOtpRequest,
)
from backend.app.core.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _issue_otp(user: User) -> str:
    otp_code = generate_otp()
    user.otp_code = otp_code
    user.otp_expires_at = _utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    return otp_code


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    existing = db.query(User).filter(or_(User.username == req.username, User.email == req.email)).first()
    if existing is not None:
        conflict = "username" if existing.username == req.username else "email"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"That {conflict} is already taken.")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        is_verified=False,
    )
    otp_code = _issue_otp(user)
    db.add(user)
    db.commit()

    try:
        await send_otp_email(req.email, otp_code, OTP_EXPIRE_MINUTES)
    except Exception as exc:  # noqa: BLE001 - don't fail registration over a flaky SMTP send
        print(f"[auth] Failed to send OTP email to {req.email}: {exc}")
        return RegisterResponse(
            message="Registered, but we couldn't send the verification email. Use 'resend code' to try again.",
            email=req.email,
        )

    return RegisterResponse(message="Registered. Check your email for the verification code.", email=req.email)


@router.post("/verify-otp", response_model=MessageResponse)
def verify_otp(req: VerifyOtpRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = db.query(User).filter(User.email == req.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account with that email.")
    if user.is_verified:
        return MessageResponse(message="Email already verified.")

    if user.otp_code != req.otp_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code.")
    if user.otp_expires_at is None or _utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired.")

    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()

    return MessageResponse(message="Email verified successfully. You can now log in.")


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(req: ResendOtpRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = db.query(User).filter(User.email == req.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account with that email.")
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already verified.")

    otp_code = _issue_otp(user)
    db.commit()

    try:
        await send_otp_email(req.email, otp_code, OTP_EXPIRE_MINUTES)
    except Exception as exc:  # noqa: BLE001 - surface as a 502, but don't crash the process
        print(f"[auth] Failed to resend OTP email to {req.email}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the verification email right now. Please try again shortly.",
        ) from exc

    return MessageResponse(message="A new verification code has been sent to your email.")


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = (
        db.query(User)
        .filter(or_(User.username == req.username_or_email, User.email == req.username_or_email))
        .first()
    )
    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username/email or password.")
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your account first.",
        )

    access_token = create_access_token(subject=str(user.id))
    return LoginResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
