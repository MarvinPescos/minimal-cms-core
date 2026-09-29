from pydantic import BaseModel, Field, EmailStr
import uuid

from app.shared.utils.auth_validation import ValidatedPassword, ValidatedUsername

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
