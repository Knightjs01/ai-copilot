import uuid

from pydantic import BaseModel, EmailStr, Field


class CandidateSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)


class CandidateLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CandidateTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CandidateMeResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_email_verified: bool
