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


# ============ Voice Input ============

@router.post("/voice/transcribe")
async def transcribe_voice(
    file: bytes,
    language: Optional[str] = None
):
    """
    Transcribe voice audio to text for invoice creation.
    
    Send audio file (webm, mp3, wav) and get back text that can be
    used with /invoices/parse.
    """
    from app.services.voice_input import transcribe_audio
    
    try:
        text = await transcribe_audio(file, language=language)
        return {"text": text, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# ============ Templates ============

@router.get("/templates")
async def list_templates():
    """List available invoice templates."""
    from app.services.pdf_generator import list_templates
    return list_templates()


@router.get("/templates/{template_id}/preview")
async def preview_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Preview a template with sample data."""
    from app.services.pdf_generator import generate_invoice_pdf, TEMPLATES
    from datetime import datetime, timedelta
    
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    user = await get_or_create_demo_user(db)
    
    # Create sample invoice for preview
    class SampleLineItem:
        description = "Sample Service"
        quantity = Decimal("2")
        unit = "hour"
        unit_price = Decimal("85.00")
        line_total = Decimal("170.00")
        sort_order = 0
    
    class SampleClient:
        name = "Sample Client"
        company = "Sample Company"
        email = "client@example.com"
        address = "123 Main St"
        payment_terms = 30
    
    class SampleInvoice:
        invoice_number = "PREVIEW-001"
        invoice_date = datetime.now()
        work_date = datetime.now()
        due_date = datetime.now() + timedelta(days=30)
        subtotal = Decimal("170.00")
        tax_amount = Decimal("8.50")
        secondary_tax_amount = Decimal("0")
        total = Decimal("178.50")
        notes = "This is a preview of the invoice template."
        client = SampleClient()
        line_items = [SampleLineItem()]
        template = template_id
    
    pdf_bytes = generate_invoice_pdf(SampleInvoice(), user, template_id)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="preview-{template_id}.pdf"'}
    )


# ============ Payment Tracking ============

@router.post("/invoices/{invoice_id}/payment")
async def record_payment(
    invoice_id: UUID,
    amount: Decimal,
    method: str = "cash",
    reference: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a payment against an invoice.
    
    Automatically updates status to 'paid' when fully paid.
    """
    from datetime import datetime
    
    user = await get_or_create_demo_user(db)
    
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.user_id == user.id)
        .options(selectinload(Invoice.client))
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update payment
    invoice.amount_paid = (invoice.amount_paid or Decimal("0")) + amount
    invoice.payment_method = method
    invoice.payment_reference = reference
    invoice.paid_at = datetime.now()
    
    # Update status
    if invoice.amount_paid >= invoice.total:
        invoice.status = "paid"
    elif invoice.amount_paid > 0:
        invoice.status = "partial"
    
    # Update client stats
    if invoice.client:
        invoice.client.total_paid = (invoice.client.total_paid or Decimal("0")) + amount
    
    await db.commit()
    
    return {
        "invoice_id": str(invoice_id),
        "amount_paid": float(invoice.amount_paid),
        "total": float(invoice.total),
        "remaining": float(invoice.total - invoice.amount_paid),
        "status": invoice.status
    }


@router.post("/invoices/{invoice_id}/send")
async def send_invoice_email(
    invoice_id: UUID,
    to_email: Optional[str] = None,
    message: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Send invoice via email.
    
    Uses client email if to_email not provided.
    """
    from datetime import datetime
    from app.services.email_sender import EmailService, EmailConfig
    from app.config import get_settings
    
    settings = get_settings()
    user = await get_or_create_demo_user(db)
    
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.user_id == user.id)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.client))
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Determine recipient
    recipient_email = to_email
    recipient_name = "Customer"
    
    if not recipient_email and invoice.client:
        recipient_email = invoice.client.email
        recipient_name = invoice.client.name
    
    if not recipient_email:
        raise HTTPException(status_code=400, detail="No email address provided or on file for client")
    
    # Check email config
    if not settings.smtp_user:
        raise HTTPException(status_code=400, detail="Email not configured. Set SMTP settings in environment.")
    
    # Generate PDF
    pdf_bytes = generate_invoice_pdf(invoice, user)
    
    # Send email
    email_config = EmailConfig(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        from_email=settings.from_email or settings.smtp_user,
        from_name=settings.from_name
    )
    
    email_service = EmailService(email_config)
    
    success = await email_service.send_invoice(
        to_email=recipient_email,
        to_name=recipient_name,
        invoice_number=invoice.invoice_number,
        total=f"${invoice.total:,.2f}",
        pdf_bytes=pdf_bytes,
        business_name=user.business_name or "My Business",
        custom_message=message
    )
    
    if success:
        # Update invoice
        invoice.status = "sent"
        invoice.sent_at = datetime.now()
        invoice.sent_to = recipient_email
        await db.commit()
        
        return {"success": True, "sent_to": recipient_email}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")


# ============ Client Stats ============

@router.get("/clients/{client_id}/stats")
async def get_client_stats(client_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get stats for a client (total invoiced, paid, outstanding)."""
    from sqlalchemy import func
    
    user = await get_or_create_demo_user(db)
    
    # Get client
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get invoice stats
    result = await db.execute(
        select(
            func.count(Invoice.id).label("invoice_count"),
            func.sum(Invoice.total).label("total_invoiced"),
            func.sum(Invoice.amount_paid).label("total_paid")
        )
        .where(Invoice.client_id == client_id)
    )
    stats = result.one()
    
    total_invoiced = float(stats.total_invoiced or 0)
    total_paid = float(stats.total_paid or 0)
    
    return {
        "client_id": str(client_id),
        "client_name": client.name,
        "invoice_count": stats.invoice_count or 0,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "outstanding": total_invoiced - total_paid
    }
