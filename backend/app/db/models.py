import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Business Info
    business_name = Column(String(255))
    business_address = Column(Text)
    business_phone = Column(String(50))
    business_email = Column(String(255))
    logo_url = Column(Text)
    
    # Tax Settings
    tax_rate = Column(Numeric(5, 4), default=Decimal("0.05"))  # e.g., 0.05 = 5%
    tax_name = Column(String(50), default="GST")
    secondary_tax_rate = Column(Numeric(5, 4))  # e.g., PST
    secondary_tax_name = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rate_items = relationship("RateItem", back_populates="user", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")


class RateItem(Base):
    """User's rate card - locked prices for services and materials."""
    __tablename__ = "rate_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    category = Column(String(50), nullable=False)  # "labor", "materials", "other"
    name = Column(String(255), nullable=False)  # "Troubleshooting", "30-amp breaker"
    description = Column(Text)
    rate = Column(Numeric(10, 2), nullable=False)  # Price
    unit = Column(String(50), default="hour")  # "hour", "each", "sqft", etc.
    
    # Aliases for AI matching
    aliases = Column(JSON, default=list)  # ["troubleshoot", "debug", "diagnose"]
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="rate_items")


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    notes = Column(Text)
    
    # Additional client info
    company = Column(String(255))
    contact_name = Column(String(255))  # If different from company name
    payment_terms = Column(Integer, default=30)  # Days until due
    default_rate_multiplier = Column(Numeric(5, 2), default=Decimal("1.00"))  # For special pricing
    
    # Stats (computed)
    total_invoiced = Column(Numeric(12, 2), default=Decimal("0"))
    total_paid = Column(Numeric(12, 2), default=Decimal("0"))
    invoice_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="clients")
    invoices = relationship("Invoice", back_populates="client")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"))
    
    invoice_number = Column(String(50), nullable=False)
    status = Column(String(20), default="draft")  # draft, sent, paid, overdue, cancelled
    
    # Original input (for auditing)
    original_input = Column(Text)
    
    # Template
    template = Column(String(50), default="modern")  # modern, classic, minimal, bold
    
    # Payment tracking
    amount_paid = Column(Numeric(12, 2), default=Decimal("0"))
    paid_at = Column(DateTime)
    payment_method = Column(String(50))  # cash, check, etransfer, credit_card, etc.
    payment_reference = Column(String(255))  # check number, transaction ID, etc.
    
    # Email tracking
    sent_at = Column(DateTime)
    sent_to = Column(String(255))
    last_reminder_at = Column(DateTime)
    reminder_count = Column(Integer, default=0)
    
    # Dates
    work_date = Column(DateTime)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    
    # Totals (computed from line items)
    subtotal = Column(Numeric(12, 2), default=Decimal("0"))
    tax_amount = Column(Numeric(12, 2), default=Decimal("0"))
    secondary_tax_amount = Column(Numeric(12, 2), default=Decimal("0"))
    total = Column(Numeric(12, 2), default=Decimal("0"))
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    rate_item_id = Column(UUID(as_uuid=True), ForeignKey("rate_items.id", ondelete="SET NULL"))
    
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(50), default="hour")
    unit_price = Column(Numeric(10, 2), nullable=False)  # Copied from rate_item at time of invoice
    line_total = Column(Numeric(12, 2), nullable=False)
    
    sort_order = Column(Integer, default=0)
    
    invoice = relationship("Invoice", back_populates="line_items")
