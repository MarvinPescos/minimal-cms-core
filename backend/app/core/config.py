from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import re

class Settings(BaseSettings):

    # Database configuration
    DB_USER: str = Field(..., description="Database Username")
    DB_PASS: str = Field(..., min_length=1, description="Database password")
    DB_HOST: str = Field(..., description="Database host")
    DB_PORT: str = Field(..., pattern=r"\d+$", description="Database port")
    DB_NAME: str = Field(..., min_length=1, description="Database name")
    DB_URL: str = Field(..., description="Database URL")
    TEST_DB_URL: str = Field(..., description="Database URL for testing")

    ENVIRONMENT: str = Field(..., description="development or production")

    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anonymous key") 
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase role key for admin operations")
    SUPABASE_JWT_SECRET: str = Field(..., description="Supabase JWT secret for token verification")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings

