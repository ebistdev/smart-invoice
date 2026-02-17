"""
Email sending service for invoices.
Supports SMTP and can be extended for SendGrid, Mailgun, etc.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class EmailConfig(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "Smart Invoice"


class EmailService:
    """Send invoices via email."""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config
    
    async def send_invoice(
        self,
        to_email: str,
        to_name: str,
        invoice_number: str,
        total: str,
        pdf_bytes: bytes,
        business_name: str,
        custom_message: Optional[str] = None
    ) -> bool:
        """
        Send invoice PDF via email.
        
        Returns True if sent successfully.
        """
        if not self.config or not self.config.smtp_user:
            raise ValueError("Email not configured. Set up SMTP settings first.")
        
        # Build email
        msg = MIMEMultipart()
        msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
        msg['To'] = to_email
        msg['Subject'] = f"Invoice {invoice_number} from {business_name}"
        
        # Email body
        body = f"""Hi {to_name},

Please find attached invoice {invoice_number} for {total}.

{custom_message or ''}

Thank you for your business!

Best regards,
{business_name}

---
Sent via Smart Invoice
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
        pdf_attachment.add_header(
            'Content-Disposition', 
            'attachment', 
            filename=f'invoice-{invoice_number}.pdf'
        )
        msg.attach(pdf_attachment)
        
        # Send
        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False


def build_invoice_email_html(
    invoice_number: str,
    client_name: str,
    total: str,
    due_date: str,
    business_name: str,
    payment_link: Optional[str] = None
) -> str:
    """Build beautiful HTML email for invoice."""
    payment_button = ""
    if payment_link:
        payment_button = f'''
        <a href="{payment_link}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px;">
            Pay Now
        </a>
        '''
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .invoice-box {{ background: #f9fafb; border-radius: 8px; padding: 24px; margin: 20px 0; }}
        .amount {{ font-size: 32px; font-weight: bold; color: #2563eb; }}
        .footer {{ margin-top: 40px; text-align: center; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="color: #1f2937; margin: 0;">Invoice from {business_name}</h1>
        </div>
        
        <p>Hi {client_name},</p>
        
        <p>Here's your invoice. Thank you for your business!</p>
        
        <div class="invoice-box">
            <p style="margin: 0; color: #6b7280;">Invoice #{invoice_number}</p>
            <p class="amount">{total}</p>
            <p style="margin: 0; color: #6b7280;">Due: {due_date}</p>
        </div>
        
        <p>Please find the PDF invoice attached to this email.</p>
        
        {payment_button}
        
        <div class="footer">
            <p>Questions? Reply to this email.</p>
            <p>Powered by Smart Invoice</p>
        </div>
    </div>
</body>
</html>
'''
