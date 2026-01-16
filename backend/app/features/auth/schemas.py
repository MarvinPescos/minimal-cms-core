from pydantic import BaseModel, BeforeValidator, Field, EmailStr
from typing import Annotated
import uuid


# === Reusable validators ===
import re

def validate_username(v: str) -> str:
    """Validate username: 3-30 chars, alphanumeric and underscores only."""
    v = v.strip()
    if len(v) < 3:
        raise ValueError("Username must be at least 3 characters")
    if len(v) > 30:
        raise ValueError("Username must be at most 30 characters")
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
        raise ValueError("Username must start with a letter and contain only letters, numbers, and underscores")
    return v

def validate_password(v: str) -> str:
    """Validate password: min 8 chars, must include uppercase, lowercase, and digit."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r'[A-Z]', v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r'\d', v):
        raise ValueError("Password must contain at least one digit")
    return v

ValidatedUsername = Annotated[str, BeforeValidator(validate_username)]
ValidatedPassword = Annotated[str, BeforeValidator(validate_password)]

class SignUpRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email for this user")
    password: ValidatedPassword = Field(...,  description="Valid password")
    username: ValidatedUsername = Field(..., description="Valid username")

class SignUpResponse(BaseModel):
    message: str = Field(..., description="Message containing what to do next.")
    user_id: uuid.UUID = Field(..., description="Contains the user id the response")
    email: EmailStr = Field(..., description="Email of this user/response")
    requires_email_confirmation: bool = Field(..., description="session will be None until the user verifies their email")
    
class SignInRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email for this user")
    password: ValidatedPassword = Field(...,  description="Valid password")

class SignInResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token for API authentication")
    refresh_token: str = Field(..., description="Token used to obtain a new access token")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict = Field(..., description="User information from Supabase")

class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to resend verification to")

class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message")

class UserProfileResponse(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    email: str = Field(..., description="User's email address")
    username: ValidatedUsername = Field(..., description="User's display name")
    is_verified: bool = Field(..., description="Whether the user's email is verified")
    metadata: dict = Field(default_factory=dict, description="Additional user metadata")

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, user):
        """Convert User model to response schema."""
        return cls(
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            is_verified=user.is_email_verified,
            metadata=user.user_metadata or {}
        )
