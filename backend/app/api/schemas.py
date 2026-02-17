from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


# Rate Items
class RateItemCreate(BaseModel):
    category: str  # "labor", "materials", "other"
    name: str
    description: Optional[str] = None
    rate: Decimal
    unit: str = "hour"
    aliases: list[str] = []


class RateItemResponse(BaseModel):
    id: UUID
    category: str
    name: str
    description: Optional[str]
    rate: Decimal
    unit: str
    aliases: list[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Clients
class ClientCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Invoice Parsing
class ParseRequest(BaseModel):
    """Request to parse work description into invoice draft."""
    work_description: str
    client_id: Optional[UUID] = None


class ParsedLineItemResponse(BaseModel):
    item_key: str
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    line_total: Decimal
    rate_item_id: Optional[UUID]
    notes: Optional[str]
    matched: bool


class ParseResponse(BaseModel):
    """AI-parsed invoice draft for user review."""
    line_items: list[ParsedLineItemResponse]
    subtotal: Decimal
    tax_amount: Decimal
    tax_name: str
    secondary_tax_amount: Optional[Decimal]
    secondary_tax_name: Optional[str]
    total: Decimal
    client_name: Optional[str]
    work_date: Optional[str]
    notes: Optional[str]
    unmatched_items: list[str]


# Invoice
class InvoiceLineItemResponse(BaseModel):
    id: UUID
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str
    status: str
    client_name: Optional[str] = None
    work_date: Optional[datetime]
    invoice_date: datetime
    due_date: Optional[datetime]
    subtotal: Decimal
    tax_amount: Decimal
    secondary_tax_amount: Optional[Decimal]
    total: Decimal
    notes: Optional[str]
    line_items: list[InvoiceLineItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceCreateFromParse(BaseModel):
    """Create invoice from parsed draft."""
    work_description: str
    client_id: Optional[UUID] = None
    # User can override parsed values
    line_item_overrides: Optional[list[dict]] = None
    notes: Optional[str] = None


# User/Business Settings
class BusinessSettingsUpdate(BaseModel):
    business_name: Optional[str] = None
    business_address: Optional[str] = None
    business_phone: Optional[str] = None
    business_email: Optional[EmailStr] = None
    tax_rate: Optional[Decimal] = None
    tax_name: Optional[str] = None
    secondary_tax_rate: Optional[Decimal] = None
    secondary_tax_name: Optional[str] = None


class BusinessSettingsResponse(BaseModel):
    business_name: Optional[str]
    business_address: Optional[str]
    business_phone: Optional[str]
    business_email: Optional[str]
    tax_rate: Optional[Decimal]
    tax_name: Optional[str]
    secondary_tax_rate: Optional[Decimal]
    secondary_tax_name: Optional[str]

    class Config:
        from_attributes = True
