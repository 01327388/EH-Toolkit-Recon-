import re

from pydantic import BaseModel, EmailStr, field_validator

_COMPANY_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&'\-]{0,119}$")


def validate_password_strength(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters.")
    return password


class RegisterForm(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class NewPasswordForm(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginForm(BaseModel):
    email: EmailStr
    password: str


class SearchQuery(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def clean_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Enter at least 2 characters to search.")
        if not _COMPANY_NAME_RE.match(v):
            raise ValueError(
                "Search must be a plain company name (letters, numbers, spaces, and . , & ' - only)."
            )
        return v


class NoteForm(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def clean_body(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Note cannot be empty.")
        if len(v) > 4000:
            raise ValueError("Note is too long (4000 characters max).")
        return v


class HideResultForm(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Please give a brief reason.")
        if len(v) > 500:
            raise ValueError("Reason is too long (500 characters max).")
        return v
