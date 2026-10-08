"""Request/response models for registration, email-OTP verification and login
(`/api/auth/...`)."""

import re

from pydantic import BaseModel, EmailStr, Field, model_validator

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
PASSWORD_SPECIAL_CHARS = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:,.<>/?]")


def _validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not PASSWORD_SPECIAL_CHARS.search(password):
        raise ValueError("Password must contain at least one special character.")


class RegisterRequest(BaseModel):
    username: str = Field(..., description="3-30 chars, letters/digits/underscore only.")
    email: EmailStr = Field(..., description="Must be a valid, unique email address.")
    password: str = Field(..., description="Must meet the strong-password policy.")
    confirm_password: str = Field(..., description="Must match 'password'.")

    @model_validator(mode="after")
    def _validate(self) -> "RegisterRequest":
        if not USERNAME_PATTERN.match(self.username):
            raise ValueError(
                "Username must be 3-30 characters long and contain only letters, digits, or underscores."
            )
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match.")
        _validate_password_strength(self.password)
        return self


class RegisterResponse(BaseModel):
    message: str
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit code sent by email.")


class ResendOtpRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Either the account's username or email.")
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_verified: bool

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
