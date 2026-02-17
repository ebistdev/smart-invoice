"""
PDF Invoice Generator using WeasyPrint.
"""

import io
from datetime import datetime
from decimal import Decimal
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from pathlib import Path

from app.db.models import Invoice, User


TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def get_template_env():
    return Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def format_currency(value: Decimal) -> str:
    """Format decimal as currency."""
    return f"${value:,.2f}"


def format_date(dt: datetime) -> str:
    """Format datetime for display."""
    if dt:
        return dt.strftime("%B %d, %Y")
    return ""


def generate_invoice_pdf(invoice: Invoice, user: User) -> bytes:
    """Generate PDF invoice."""
    env = get_template_env()
    env.filters['currency'] = format_currency
    env.filters['date'] = format_date
    
    template = env.get_template("invoice.html")
    
    # Prepare line items
    line_items = sorted(invoice.line_items, key=lambda x: x.sort_order)
    
    html_content = template.render(
        invoice=invoice,
        user=user,
        line_items=line_items,
        has_secondary_tax=user.secondary_tax_rate and user.secondary_tax_rate > 0
    )
    
    # Generate PDF
    html = HTML(string=html_content)
    css = CSS(string=get_invoice_css())
    
    pdf_bytes = html.write_pdf(stylesheets=[css])
    return pdf_bytes


def get_invoice_css() -> str:
    """Invoice PDF styling."""
    return """
    @page {
        size: letter;
        margin: 1in;
    }
    
    body {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 12px;
        line-height: 1.4;
        color: #333;
    }
    
    .invoice-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 40px;
    }
    
    .business-info {
        text-align: left;
    }
    
    .business-name {
        font-size: 24px;
        font-weight: bold;
        color: #2563eb;
        margin-bottom: 8px;
    }
    
    .invoice-title {
        text-align: right;
    }
    
    .invoice-title h1 {
        font-size: 32px;
        color: #1f2937;
        margin: 0;
    }
    
    .invoice-number {
        font-size: 14px;
        color: #6b7280;
        margin-top: 4px;
    }
    
    .invoice-meta {
        display: flex;
        justify-content: space-between;
        margin-bottom: 30px;
    }
    
    .bill-to h3, .invoice-dates h3 {
        font-size: 12px;
        color: #6b7280;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .client-name {
        font-size: 16px;
        font-weight: bold;
    }
    
    .invoice-dates {
        text-align: right;
    }
    
    .date-row {
        margin: 4px 0;
    }
    
    .date-label {
        color: #6b7280;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 30px;
    }
    
    th {
        background-color: #f3f4f6;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e5e7eb;
    }
    
    th.right, td.right {
        text-align: right;
    }
    
    td {
        padding: 12px;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .totals {
        width: 300px;
        margin-left: auto;
    }
    
    .totals-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .totals-row.total {
        font-size: 18px;
        font-weight: bold;
        border-bottom: 2px solid #2563eb;
        color: #2563eb;
    }
    
    .notes {
        margin-top: 40px;
        padding: 16px;
        background-color: #f9fafb;
        border-radius: 4px;
    }
    
    .notes h4 {
        margin: 0 0 8px 0;
        color: #6b7280;
    }
    
    .footer {
        margin-top: 60px;
        text-align: center;
        color: #9ca3af;
        font-size: 10px;
    }
    """
