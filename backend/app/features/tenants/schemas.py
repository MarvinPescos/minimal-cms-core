from pydantic import BaseModel, Field, ConfigDict
from typing import Any
import uuid

from app.shared.utils.auth_validation import ValidatedPassword, ValidatedUsername


# === Tenant ===

class TenantCreate(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=150,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Machine name: lowercase, underscores_only"
    )

class TenantUpdate(BaseModel):
    name: str | None = Field(None,
        min_length=3,
        max_length=150,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Machine name: lowercase, underscores_only"
    )
    is_active: bool | None = None

class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool


# === TenantMembers === 

class StaffAccountCreate(BaseModel):
    username: ValidatedUsername = Field(..., description="Valid username")
    password: ValidatedPassword = Field(..., description="Valid password")
    role: str = Field(default="member", pattern=r"^(owner|member)$")

class StaffAccountUpdate(BaseModel):
    role: str | None = Field(None, pattern=r"^(owner|member)$")
    is_active: bool | None = Field(None, description="Change members/staff is_active")

class StaffAccountResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: str
    is_active: bool
     
    

    
