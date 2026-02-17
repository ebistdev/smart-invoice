"""
Recurring Invoice Service.

Automatically generates invoices on a schedule for regular clients.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Invoice, InvoiceLineItem, Client, User, RateItem


class RecurrenceFrequency(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


def get_next_date(frequency: RecurrenceFrequency, from_date: datetime) -> datetime:
    """Calculate next invoice date based on frequency."""
    if frequency == RecurrenceFrequency.WEEKLY:
        return from_date + timedelta(weeks=1)
    elif frequency == RecurrenceFrequency.BIWEEKLY:
        return from_date + timedelta(weeks=2)
    elif frequency == RecurrenceFrequency.MONTHLY:
        # Add one month
        month = from_date.month + 1
        year = from_date.year
        if month > 12:
            month = 1
            year += 1
        day = min(from_date.day, 28)  # Safe for all months
        return from_date.replace(year=year, month=month, day=day)
    elif frequency == RecurrenceFrequency.QUARTERLY:
        month = from_date.month + 3
        year = from_date.year
        while month > 12:
            month -= 12
            year += 1
        day = min(from_date.day, 28)
        return from_date.replace(year=year, month=month, day=day)
    elif frequency == RecurrenceFrequency.YEARLY:
        return from_date.replace(year=from_date.year + 1)
    return from_date


async def create_recurring_invoice(
    db: AsyncSession,
    user_id: UUID,
    client_id: UUID,
    line_items: list[dict],  # [{"rate_item_id": UUID, "quantity": Decimal, "description": str}]
    frequency: RecurrenceFrequency,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    notes: Optional[str] = None
) -> dict:
    """
    Create a recurring invoice schedule.
    
    Returns the schedule configuration.
    """
    # For MVP, store as JSON in a simple table or file
    # In production, use a proper RecurringInvoice model
    
    schedule = {
        "user_id": str(user_id),
        "client_id": str(client_id),
        "line_items": line_items,
        "frequency": frequency.value,
        "start_date": (start_date or datetime.now()).isoformat(),
        "end_date": end_date.isoformat() if end_date else None,
        "next_invoice_date": (start_date or datetime.now()).isoformat(),
        "notes": notes,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    return schedule


async def generate_invoice_from_recurring(
    db: AsyncSession,
    schedule: dict,
    user: User
) -> Invoice:
    """Generate an invoice from a recurring schedule."""
    from app.services.invoice_builder import save_invoice, InvoiceData, InvoiceLineItemData
    
    # Get rate items for pricing
    rate_item_ids = [item["rate_item_id"] for item in schedule["line_items"]]
    result = await db.execute(
        select(RateItem).where(RateItem.id.in_(rate_item_ids))
    )
    rate_items = {str(r.id): r for r in result.scalars().all()}
    
    # Build line items with current prices from rate card
    line_items = []
    for item in schedule["line_items"]:
        rate_item = rate_items.get(item["rate_item_id"])
        if rate_item:
            line_items.append(InvoiceLineItemData(
                description=item.get("description") or rate_item.name,
                quantity=Decimal(str(item["quantity"])),
                unit=rate_item.unit,
                unit_price=rate_item.rate,  # ALWAYS from rate card
                rate_item_id=rate_item.id
            ))
    
    # Calculate totals
    subtotal = sum(item.line_total for item in line_items)
    tax_amount = (subtotal * (user.tax_rate or Decimal("0"))).quantize(Decimal("0.01"))
    secondary_tax = Decimal("0")
    if user.secondary_tax_rate:
        secondary_tax = (subtotal * user.secondary_tax_rate).quantize(Decimal("0.01"))
    total = subtotal + tax_amount + secondary_tax
    
    invoice_data = InvoiceData(
        line_items=line_items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        secondary_tax_amount=secondary_tax,
        total=total,
        notes=schedule.get("notes")
    )
    
    # Save invoice
    invoice = await save_invoice(
        db,
        UUID(schedule["user_id"]),
        invoice_data,
        original_input=f"Recurring invoice - {schedule['frequency']}",
        client_id=UUID(schedule["client_id"])
    )
    
    return invoice
