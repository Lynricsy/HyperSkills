"""Schemas and router for the user profile API. Ported from Pydantic v1."""

from typing import List, Optional

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field, RootModel, validator
from sqlalchemy.orm import Session


class UserBase(BaseModel):
    email: str = Field(..., description="login email")
    display_name: Optional[str] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @validator("email")
    def email_must_have_at(cls, v):
        assert "@" in v
        return v


class User(UserBase):
    id: int = Field(...)
    password_hash: str = Field(..., alias="passwordHash")
    internal_notes: Optional[str] = None


class Admin(User):
    permissions: List[str] = []


class UserList(RootModel[List[User]]):
    pass


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int):
    db: Session = ...  # injected elsewhere
    return db.get(UserRow, user_id)  # noqa: F821 - SQLAlchemy row object


@router.get("", response_model=UserList)
async def list_users() -> UserList:
    db: Session = ...
    return UserList(db.query(UserRow).all())  # noqa: F821


@router.post("", response_model=User)
async def create_user(payload: UserCreate) -> User:
    db: Session = ...
    row = UserRow(**payload.model_dump())  # noqa: F821
    db.add(row)
    return row


app = FastAPI()
app.include_router(router)
