from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import field_validator
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_name: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=255, index=True)  
    password: str = Field(max_length=30)

    address: str = Field(max_length=100)
    contact_number: str = Field(max_length=10, min_length=10)

class ServiceRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="user.id", index=True)
    
    service_name: str
    status: str = Field(default="Pending") # Default status
    date_slot: str
    address: str
    vendor_name: str
    amount: int
    created_at: datetime = Field(default_factory=datetime.now)