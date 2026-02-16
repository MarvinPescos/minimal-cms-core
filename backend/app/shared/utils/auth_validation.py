from pydantic import BeforeValidator
from typing import Annotated
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