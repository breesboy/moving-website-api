import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, EmailStr

class UserCreateModel(BaseModel):
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    username: str = Field(max_length=25)
    email: str = Field(max_length=40)
    password: str = Field(min_length=8)

    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "email": "johndoe123@co.com",
                "password": "testpass123",
            }
        }
    }


class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    role : str
    is_verified: bool
    password_hash: str = Field(exclude=True)


# class UserBooksModel(UserModel):
#     books: List[Book]
#     reviews: List[ReviewModel]


class CurrentUser(BaseModel):
    uid: uuid.UUID
    email: str
    username: str
    first_name: str
    last_name: str
    role : str
    is_verified: bool



class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class EmailModel(BaseModel):
    addresses : List[str]

class EmailSchema(BaseModel):
    email: str
    name: str
    verification_link: str

class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    new_password: str
