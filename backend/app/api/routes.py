from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import User, RateItem, Client, Invoice, InvoiceLineItem
from app.api.schemas import (
    RateItemCreate, RateItemResponse,
    ClientCreate, ClientResponse,
    ParseRequest, ParseResponse, ParsedLineItemResponse,
    InvoiceCreateFromParse, InvoiceResponse, InvoiceLineItemResponse,
    BusinessSettingsUpdate, BusinessSettingsResponse
)
from app.services.ai_parser import parse_work_description
from app.services.invoice_builder import build_invoice_from_parsed, save_invoice
from app.services.pdf_generator import generate_invoice_pdf

router = APIRouter()

# For MVP: single-user mode (no auth)
# In production, replace with proper auth
DEMO_USER_ID = None  # Will be set on first request


async def get_or_create_demo_user(db: AsyncSession) -> User:
    """Get or create a demo user for MVP."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email="demo@smartinvoice.local",
            hashed_password="demo",
            business_name="My Business",
            tax_rate=Decimal("0.05"),
            tax_name="GST"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user


# ============ Rate Items (Rate Card) ============

@router.get("/rate-items", response_model=list[RateItemResponse])
async def list_rate_items(db: AsyncSession = Depends(get_db)):
    """List all rate card items."""
    user = await get_or_create_demo_user(db)
    result = await db.execute(
        select(RateItem)
        .where(RateItem.user_id == user.id, RateItem.is_active == True)
        .order_by(RateItem.category, RateItem.name)
    )
    return result.scalars().all()


@router.post("/rate-items", response_model=RateItemResponse)
async def create_rate_item(item: RateItemCreate, db: AsyncSession = Depends(get_db)):
    """Add a new rate card item."""
    user = await get_or_create_demo_user(db)
    rate_item = RateItem(
        user_id=user.id,
        category=item.category,
        name=item.name,
        description=item.description,
        rate=item.rate,
        unit=item.unit,
        aliases=item.aliases
    )
    db.add(rate_item)
    await db.commit()
    await db.refresh(rate_item)
    return rate_item


@router.put("/rate-items/{item_id}", response_model=RateItemResponse)
async def update_rate_item(
    item_id: UUID,
    item: RateItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update a rate card item."""
    user = await get_or_create_demo_user(db)
    result = await db.execute(
        select(RateItem).where(RateItem.id == item_id, RateItem.user_id == user.id)
    )
    rate_item = result.scalar_one_or_none()
    if not rate_item:
        raise HTTPException(status_code=404, detail="Rate item not found")
    
    rate_item.category = item.category
    rate_item.name = item.name
    rate_item.description = item.description
    rate_item.rate = item.rate
    rate_item.unit = item.unit
    rate_item.aliases = item.aliases
    
    await db.commit()
    await db.refresh(rate_item)
    return rate_item


@router.delete("/rate-items/{item_id}")
async def delete_rate_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a rate card item."""
    user = await get_or_create_demo_user(db)
    result = await db.execute(
        select(RateItem).where(RateItem.id == item_id, RateItem.user_id == user.id)
    )
    rate_item = result.scalar_one_or_none()
    if not rate_item:
        raise HTTPException(status_code=404, detail="Rate item not found")
    
    rate_item.is_active = False  # Soft delete
    await db.commit()
    return {"status": "deleted"}


# ============ Clients ============

@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(db: AsyncSession = Depends(get_db)):
    """List all clients."""
    user = await get_or_create_demo_user(db)
    result = await db.execute(
        select(Client).where(Client.user_id == user.id).order_by(Client.name)
    )
    return result.scalars().all()


@router.post("/clients", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: AsyncSession = Depends(get_db)):
    """Add a new client."""
    user = await get_or_create_demo_user(db)
    db_client = Client(user_id=user.id, **client.model_dump())
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client


# ============ Invoice Parsing (THE MAGIC) ============

@router.post("/invoices/parse", response_model=ParseResponse)
async def parse_work_to_invoice(
    request: ParseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Parse work description into invoice draft.
    
    This is where the AI magic happens:
    1. AI extracts items and quantities from natural language
    2. Items are matched to the user's rate card
    3. PRICES come from the rate card - NOT from AI
    
    Returns a draft for user review before saving.
    """
    user = await get_or_create_demo_user(db)
    
    # Get user's rate items
    result = await db.execute(
        select(RateItem).where(
            RateItem.user_id == user.id,
            RateItem.is_active == True
        )
    )
    rate_items = result.scalars().all()
    
    if not rate_items:
        raise HTTPException(
            status_code=400,
            detail="No rate items configured. Please set up your rate card first."
        )
    
    # Parse with AI
    parsed = await parse_work_description(request.work_description, rate_items)
    
    # Build invoice data with pricing from rate card
    invoice_data = await build_invoice_from_parsed(db, user.id, parsed)
    
    # Build response
    line_items = []
    for item in invoice_data.line_items:
        line_items.append(ParsedLineItemResponse(
            item_key=f"{item.description}",
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            line_total=item.line_total,
            rate_item_id=item.rate_item_id,
            notes=item.notes,
            matched=item.matched
        ))
    
    return ParseResponse(
        line_items=line_items,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        tax_name=user.tax_name or "Tax",
        secondary_tax_amount=invoice_data.secondary_tax_amount if invoice_data.secondary_tax_amount else None,
        secondary_tax_name=user.secondary_tax_name,
        total=invoice_data.total,
        client_name=invoice_data.client_name,
        work_date=invoice_data.work_date,
        notes=invoice_data.notes,
        unmatched_items=invoice_data.unmatched_items
    )


@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    request: InvoiceCreateFromParse,
    db: AsyncSession = Depends(get_db)
):
    """
    Create an invoice from work description.
    
    Parses the description and saves the invoice.
    """
    user = await get_or_create_demo_user(db)
    
    # Get rate items
    result = await db.execute(
        select(RateItem).where(
            RateItem.user_id == user.id,
            RateItem.is_active == True
        )
    )
    rate_items = result.scalars().all()
    
    # Parse
    parsed = await parse_work_description(request.work_description, rate_items)
    
    # Build invoice data
    invoice_data = await build_invoice_from_parsed(db, user.id, parsed)
    
    if request.notes:
        invoice_data.notes = request.notes
    
    # Save
    invoice = await save_invoice(
        db, user.id, invoice_data,
        original_input=request.work_description,
        client_id=request.client_id
    )
    
    # Reload with line items
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice.id)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.client))
    )
    invoice = result.scalar_one()
    
    # Build response
    response = InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        client_name=invoice.client.name if invoice.client else None,
        work_date=invoice.work_date,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        secondary_tax_amount=invoice.secondary_tax_amount,
        total=invoice.total,
        notes=invoice.notes,
        line_items=[
            InvoiceLineItemResponse(
                id=li.id,
                description=li.description,
                quantity=li.quantity,
                unit=li.unit,
                unit_price=li.unit_price,
                line_total=li.line_total
            ) for li in sorted(invoice.line_items, key=lambda x: x.sort_order)
        ],
        created_at=invoice.created_at
    )
    
    return response


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List invoices."""
    user = await get_or_create_demo_user(db)
    
    query = select(Invoice).where(Invoice.user_id == user.id)
    if status:
        query = query.where(Invoice.status == status)
    
    query = query.options(
        selectinload(Invoice.line_items),
        selectinload(Invoice.client)
    ).order_by(Invoice.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return [
        InvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            status=inv.status,
            client_name=inv.client.name if inv.client else None,
            work_date=inv.work_date,
            invoice_date=inv.invoice_date,
            due_date=inv.due_date,
            subtotal=inv.subtotal,
            tax_amount=inv.tax_amount,
            secondary_tax_amount=inv.secondary_tax_amount,
            total=inv.total,
            notes=inv.notes,
            line_items=[
                InvoiceLineItemResponse(
                    id=li.id,
                    description=li.description,
                    quantity=li.quantity,
                    unit=li.unit,
                    unit_price=li.unit_price,
                    line_total=li.line_total
                ) for li in sorted(inv.line_items, key=lambda x: x.sort_order)
            ],
            created_at=inv.created_at
        ) for inv in invoices
    ]


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single invoice."""
    user = await get_or_create_demo_user(db)
    
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.user_id == user.id)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.client))
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        client_name=invoice.client.name if invoice.client else None,
        work_date=invoice.work_date,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        secondary_tax_amount=invoice.secondary_tax_amount,
        total=invoice.total,
        notes=invoice.notes,
        line_items=[
            InvoiceLineItemResponse(
                id=li.id,
                description=li.description,
                quantity=li.quantity,
                unit=li.unit,
                unit_price=li.unit_price,
                line_total=li.line_total
            ) for li in sorted(invoice.line_items, key=lambda x: x.sort_order)
        ],
        created_at=invoice.created_at
    )


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    """Download invoice as PDF."""
    user = await get_or_create_demo_user(db)
    
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.user_id == user.id)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.client))
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_bytes = generate_invoice_pdf(invoice, user)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="invoice-{invoice.invoice_number}.pdf"'
        }
    )


# ============ Business Settings ============

@router.get("/settings", response_model=BusinessSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get business settings."""
    user = await get_or_create_demo_user(db)
    return BusinessSettingsResponse.model_validate(user)


@router.put("/settings", response_model=BusinessSettingsResponse)
async def update_settings(
    settings: BusinessSettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update business settings."""
    user = await get_or_create_demo_user(db)
    
    update_data = settings.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return BusinessSettingsResponse.model_validate(user)
