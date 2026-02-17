"""
QR Code Payment Service.

Generates QR codes for:
- Interac e-Transfer (Canada)
- Payment links
- Invoice reference
"""

import io
import base64
from decimal import Decimal
from typing import Optional

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


def generate_payment_qr(
    amount: Decimal,
    recipient_email: str,
    invoice_number: str,
    message: Optional[str] = None,
    style: str = "default"
) -> str:
    """
    Generate a QR code for Interac e-Transfer.
    
    Returns base64-encoded PNG image.
    """
    if not HAS_QRCODE:
        raise ImportError("qrcode package required: pip install qrcode[pil]")
    
    # Build e-Transfer message
    # Format: amount, recipient, reference
    etransfer_data = f"""INTERAC E-TRANSFER
To: {recipient_email}
Amount: ${amount:.2f} CAD
Reference: Invoice {invoice_number}
{message or ''}
""".strip()
    
    # Generate QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(etransfer_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def generate_payment_link_qr(
    payment_url: str,
    invoice_number: str
) -> str:
    """
    Generate QR code for a payment link (Stripe, PayPal, etc).
    
    Returns base64-encoded PNG image.
    """
    if not HAS_QRCODE:
        raise ImportError("qrcode package required: pip install qrcode[pil]")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payment_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def generate_invoice_qr(
    invoice_number: str,
    total: Decimal,
    due_date: str,
    business_name: str
) -> str:
    """
    Generate QR code with invoice details for quick reference.
    
    Can be scanned to see invoice summary.
    """
    if not HAS_QRCODE:
        raise ImportError("qrcode package required: pip install qrcode[pil]")
    
    invoice_data = f"""INVOICE: {invoice_number}
From: {business_name}
Total: ${total:.2f}
Due: {due_date}
"""
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(invoice_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#2563eb", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
