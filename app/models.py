import random
from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

def generate_id():
    """Generates a random 7-digit number (1,000,000 to 9,999,999)."""
    return random.randint(1000000, 9999999)

class User(SQLModel, table=True):
    # 7-digit ID, Primary Key
    id: Optional[int] = Field(default_factory=generate_id, primary_key=True)

    user_name: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=255)
    password: str = Field(max_length=30)
    address: str = Field(max_length=100)
    # Validation is handled in UI; this just sets DB schema limits
    contact_number: str = Field(max_length=10)

class ServiceRequest(SQLModel, table=True):
    # 7-digit ID, Primary Key
    id: Optional[int] = Field(default_factory=generate_id, primary_key=True)
    
    customer_id: int = Field(foreign_key="user.id", index=True)
    
    service_name: str
    status: str = Field(default="Pending")
    date_slot: str
    address: str
    vendor_name: str
    amount: int
    created_at: datetime = Field(default_factory=datetime.now)