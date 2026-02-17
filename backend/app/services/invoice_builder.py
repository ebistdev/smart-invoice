"""
Invoice Builder - Compute totals from parsed items + rate card.

SAFETY: Prices come ONLY from the user's rate card.
The AI parser provides items and quantities - this module does the math.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RateItem, Invoice, InvoiceLineItem, Client, User
from app.services.ai_parser import ParsedInvoice


class InvoiceLineItemData:
    """Line item with computed pricing."""
    def __init__(
        self,
        description: str,
        quantity: Decimal,
        unit: str,
        unit_price: Decimal,
        rate_item_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        matched: bool = True
    ):
        self.description = description
        self.quantity = quantity
        self.unit = unit
        self.unit_price = unit_price
        self.line_total = quantity * unit_price
        self.rate_item_id = rate_item_id
        self.notes = notes
        self.matched = matched


class InvoiceData:
    """Complete invoice with computed totals."""
    def __init__(
        self,
        line_items: list[InvoiceLineItemData],
        subtotal: Decimal,
        tax_amount: Decimal,
        secondary_tax_amount: Decimal,
        total: Decimal,
        client_name: Optional[str] = None,
        work_date: Optional[str] = None,
        notes: Optional[str] = None,
        unmatched_items: list[str] = None
    ):
        self.line_items = line_items
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.secondary_tax_amount = secondary_tax_amount
        self.total = total
        self.client_name = client_name
        self.work_date = work_date
        self.notes = notes
        self.unmatched_items = unmatched_items or []


async def build_invoice_from_parsed(
    db: AsyncSession,
    user_id: UUID,
    parsed: ParsedInvoice
) -> InvoiceData:
    """
    Build invoice with pricing from user's rate card.
    
    SAFETY: All prices come from rate_items table, not AI.
    """
    # Get user's rate items
    result = await db.execute(
        select(RateItem).where(
            RateItem.user_id == user_id,
            RateItem.is_active == True
        )
    )
    rate_items = {
        f"{r.category}.{r.name.lower()}": r 
        for r in result.scalars().all()
    }
    
    # Get user's tax settings
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    
    line_items = []
    unmatched = list(parsed.unmatched_items)
    
    for parsed_item in parsed.line_items:
        rate_item = rate_items.get(parsed_item.item_key)
        
        if rate_item:
            # PRICE FROM RATE CARD - not AI
            line_items.append(InvoiceLineItemData(
                description=rate_item.name,
                quantity=parsed_item.quantity,
                unit=rate_item.unit,
                unit_price=rate_item.rate,
                rate_item_id=rate_item.id,
                notes=parsed_item.notes,
                matched=True
            ))
        else:
            # Item not in rate card - flag for user review
            unmatched.append(f"{parsed_item.item_key} (qty: {parsed_item.quantity})")
    
    # Compute totals
    subtotal = sum(item.line_total for item in line_items)
    
    tax_amount = Decimal("0")
    if user.tax_rate:
        tax_amount = (subtotal * user.tax_rate).quantize(Decimal("0.01"))
    
    secondary_tax_amount = Decimal("0")
    if user.secondary_tax_rate:
        secondary_tax_amount = (subtotal * user.secondary_tax_rate).quantize(Decimal("0.01"))
    
    total = subtotal + tax_amount + secondary_tax_amount
    
    return InvoiceData(
        line_items=line_items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        secondary_tax_amount=secondary_tax_amount,
        total=total,
        client_name=parsed.client_name,
        work_date=parsed.work_date,
        notes=parsed.notes,
        unmatched_items=unmatched
    )


async def save_invoice(
    db: AsyncSession,
    user_id: UUID,
    invoice_data: InvoiceData,
    original_input: str,
    client_id: Optional[UUID] = None
) -> Invoice:
    """Save invoice to database."""
    # Generate invoice number
    result = await db.execute(
        select(Invoice).where(Invoice.user_id == user_id).order_by(Invoice.created_at.desc()).limit(1)
    )
    last_invoice = result.scalar_one_or_none()
    
    if last_invoice:
        # Extract number and increment
        try:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            invoice_number = f"{datetime.now().year}-{last_num + 1:04d}"
        except:
            invoice_number = f"{datetime.now().year}-0001"
    else:
        invoice_number = f"{datetime.now().year}-0001"
    
    # Parse work date
    work_date = None
    if invoice_data.work_date:
        try:
            work_date = datetime.strptime(invoice_data.work_date, "%Y-%m-%d")
        except:
            work_date = datetime.now()
    else:
        work_date = datetime.now()
    
    # Create invoice
    invoice = Invoice(
        user_id=user_id,
        client_id=client_id,
        invoice_number=invoice_number,
        status="draft",
        original_input=original_input,
        work_date=work_date,
        invoice_date=datetime.now(),
        due_date=datetime.now() + timedelta(days=30),
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        secondary_tax_amount=invoice_data.secondary_tax_amount,
        total=invoice_data.total,
        notes=invoice_data.notes
    )
    db.add(invoice)
    await db.flush()
    
    # Add line items
    for i, item in enumerate(invoice_data.line_items):
        line = InvoiceLineItem(
            invoice_id=invoice.id,
            rate_item_id=item.rate_item_id,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            line_total=item.line_total,
            sort_order=i
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(invoice)
    
    return invoice
