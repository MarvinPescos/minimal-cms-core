from pydantic import BaseModel, Field
from fastapi import Depends, HTTPException,  status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.repository import UserRepository
from app.infrastructure.database import get_db
from app.infrastructure.security.jwt_handler import verify_jwt_token
from app.shared.errors import UnauthorizedError
from app.infrastructure.observability import log

# security scheme for swagger
security_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Enter your Supabase JWT token",
)

# Schema 
class AuthenticatedUser(BaseModel):
    """
        Represents an authenticated user in the system
        Domain model (not an API scheme)
    """

    user_id: str = Field(..., description="Local database user ID")
    email: str | None = Field(None, description="User email")
    is_active: bool = Field(False, description="If account is active")
    role: str = Field(default="user", description="User role")
    raw_payload: dict = Field(..., description="Raw JWT payload")

    def has_role(self, role: str) -> bool:
        """ Check if user has specific role """
        return self.role == role

    # I don't need this yet, but keeping it just in case.
    # def is_admin(self) -> bool:
    #     """ Check if user is admin"""
    #     return self.role == "admin" or self.role == "service_role"

    class Config:
        extra="forbid"
        schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "user@example.com",
                "role": "user",
                "raw_payload": {}
            }
        }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme) ,
    session: AsyncSession = Depends(get_db)
) -> AuthenticatedUser:
    """
        FastAPI dependency: get User from token and ensure they exist in db
    """
    try:
        token = credentials.credentials

        # verify
        payload = verify_jwt_token(token)

        # Sync user from Supabase (creates if doesn't exist)
        user_repo = UserRepository(session)
        supabase_user_id = payload.get("sub")
        email = payload.get("email")
        user_db = await user_repo.sync_from_supabase(supabase_user_id, email)

        role = payload.get("role", "user")

        log.debug(f"Authenticated user: {user_db.id}")

        return AuthenticatedUser(
            user_id=str(user_db.id),
            email=user_db.email,
            is_active=user_db.is_active,
            role=role,
            raw_payload=payload,
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


def require_auth(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    """
        Simplified dependency alias for requiring authentication
    """   
    return user

# PS: I don't need this, so I'll just comment it out in case someone needs it.

# def require_admin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
#     """
#         Require admin role.
#     """
#     if not user.is_admin():
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Admin access required"
#         )
#     return user

 