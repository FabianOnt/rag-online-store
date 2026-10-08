from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr

class CategoryCreate(BaseModel):
    name: str

class ProductCreate(BaseModel):
    name: str
    price: Decimal
    category_name: str
    units: int = 0
    discount: Decimal = Decimal("0.00")

class DocumentUploadResponse(BaseModel):
    file_name: str
    chunks_created: int
    product_sku: str | None

class MessageTypeCreate(BaseModel):
    name: str

class GetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., max_length=50, examples=["john@example.com"])
