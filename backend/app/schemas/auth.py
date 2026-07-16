import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole

# Phone validation E.164 regex pattern
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")

# Password complexity: min 8 chars, 1 upper, 1 lower, 1 digit, 1 special char
PWD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(...)
    phone: str = Field(...)
    role: UserRole = Field(default=UserRole.Customer)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not PWD_REGEX.match(v):
            raise ValueError(
                "Password must be at least 8 characters long, contain "
                "at least one uppercase letter, one lowercase letter, "
                "one numeric digit, and one special character (@$!%*?&)."
            )
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        # Strip spacing and brackets for sanity checking
        clean_phone = v.replace(" ", "").replace("-", "")
        if not PHONE_REGEX.match(clean_phone):
            raise ValueError("Phone number must match standard international E.164 format.")
        return clean_phone

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
