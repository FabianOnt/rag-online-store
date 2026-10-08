from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., max_length=50, examples=["john@example.com"])
    password: str = Field(..., min_length=8, examples=["securepassword123"])

class LoginResponse(BaseModel):
    session_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])

class LogoutRequest(BaseModel):
    session_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])


class RAGQueryRequest(BaseModel):
    query: str
    chat_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])
    session_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])

class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[str] = []

class ReviewCreate(BaseModel):
    product_sku: str = Field(..., description="The unique SKU of the product")
    rating: int = Field(..., ge=0, le=5, description="Rating between 0 and 5")
    comment: Optional[str] = Field(None, description="Optional text review")


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    rating: int
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class ProductSearchRequest(BaseModel):
    product_name: str = ""


class ProductSearchItem(BaseModel):
    id: int
    sku: str
    name: str

    model_config = ConfigDict(from_attributes=True)



class CreateUserRequest(BaseModel):
    name: str = Field(..., max_length=100, examples=["John Doe"])
    email: EmailStr = Field(..., max_length=50, examples=["john@example.com"])
    password: str = Field(..., min_length=8, examples=["securepassword123"])


class CreateChatRequest(BaseModel):
    name: str = Field(..., max_length=100, examples=["Project Discussion"])
    session_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])


class CreateMessageTypeRequest(BaseModel):
    name: str = Field(..., max_length=20, examples=["text"])


class GetChatsRequest(BaseModel):
    session_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])


class GetMessagesRequest(BaseModel):
    chat_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])
    session_token: str = Field(..., max_length=255, examples=["a1b2c3d4e5f67890"])


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: int
    name: str
    token: str
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatItemResponse(BaseModel):
    name: str
    token: str
    created_at: datetime

class MessageItemResponse(BaseModel):
    message_type: str
    content: str
    created_at: datetime