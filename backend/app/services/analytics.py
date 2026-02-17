"""
Invoice Analytics Service.

Provides dashboard data:
- Revenue over time
- Outstanding amounts
- Top clients
- Invoice status breakdown
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Invoice, Client


async def get_dashboard_stats(
    db: AsyncSession,
    user_id: UUID,
    days: int = 30
) -> dict:
    """Get key dashboard statistics."""
    cutoff = datetime.now() - timedelta(days=days)
    
    # Total revenue (paid invoices)
    result = await db.execute(
        select(func.sum(Invoice.amount_paid))
        .where(
            Invoice.user_id == user_id,
            Invoice.paid_at >= cutoff
        )
    )
    revenue_period = result.scalar() or Decimal("0")
    
    # Total outstanding
    result = await db.execute(
        select(func.sum(Invoice.total - func.coalesce(Invoice.amount_paid, 0)))
        .where(
            Invoice.user_id == user_id,
            Invoice.status.in_(["sent", "draft", "overdue", "partial"])
        )
    )
    outstanding = result.scalar() or Decimal("0")
    
    # Invoice counts by status
    result = await db.execute(
        select(Invoice.status, func.count(Invoice.id))
        .where(Invoice.user_id == user_id)
        .group_by(Invoice.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}
    
    # Total all-time revenue
    result = await db.execute(
        select(func.sum(Invoice.amount_paid))
        .where(Invoice.user_id == user_id)
    )
    total_revenue = result.scalar() or Decimal("0")
    
    # Invoice count
    result = await db.execute(
        select(func.count(Invoice.id))
        .where(Invoice.user_id == user_id)
    )
    total_invoices = result.scalar() or 0
    
    return {
        "revenue_period": float(revenue_period),
        "revenue_period_days": days,
        "outstanding": float(outstanding),
        "total_revenue": float(total_revenue),
        "total_invoices": total_invoices,
        "status_breakdown": status_counts,
        "overdue_count": status_counts.get("overdue", 0)
    }


async def get_revenue_chart(
    db: AsyncSession,
    user_id: UUID,
    months: int = 6
) -> list[dict]:
    """Get monthly revenue for chart."""
    data = []
    now = datetime.now()
    
    for i in range(months - 1, -1, -1):
        # Calculate month
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        
        # Get revenue for this month
        result = await db.execute(
            select(func.sum(Invoice.amount_paid))
            .where(
                Invoice.user_id == user_id,
                extract('month', Invoice.paid_at) == month,
                extract('year', Invoice.paid_at) == year
            )
        )
        revenue = result.scalar() or Decimal("0")
        
        # Get invoice count
        result = await db.execute(
            select(func.count(Invoice.id))
            .where(
                Invoice.user_id == user_id,
                extract('month', Invoice.invoice_date) == month,
                extract('year', Invoice.invoice_date) == year
            )
        )
        count = result.scalar() or 0
        
        month_name = datetime(year, month, 1).strftime("%b %Y")
        data.append({
            "month": month_name,
            "revenue": float(revenue),
            "invoices": count
        })
    
    return data


async def get_top_clients(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 5
) -> list[dict]:
    """Get top clients by revenue."""
    result = await db.execute(
        select(
            Client.id,
            Client.name,
            func.sum(Invoice.total).label("total_billed"),
            func.sum(Invoice.amount_paid).label("total_paid"),
            func.count(Invoice.id).label("invoice_count")
        )
        .join(Invoice, Invoice.client_id == Client.id)
        .where(Client.user_id == user_id)
        .group_by(Client.id, Client.name)
        .order_by(func.sum(Invoice.total).desc())
        .limit(limit)
    )
    
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "total_billed": float(row.total_billed or 0),
            "total_paid": float(row.total_paid or 0),
            "invoice_count": row.invoice_count
        }
        for row in result.all()
    ]


async def get_overdue_invoices(
    db: AsyncSession,
    user_id: UUID
) -> list[dict]:
    """Get list of overdue invoices."""
    now = datetime.now()
    
    result = await db.execute(
        select(Invoice)
        .where(
            Invoice.user_id == user_id,
            Invoice.due_date < now,
            Invoice.status.in_(["sent", "partial"]),
            Invoice.amount_paid < Invoice.total
        )
        .order_by(Invoice.due_date)
    )
    
    invoices = result.scalars().all()
    
    return [
        {
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "total": float(inv.total),
            "amount_paid": float(inv.amount_paid or 0),
            "outstanding": float(inv.total - (inv.amount_paid or Decimal("0"))),
            "due_date": inv.due_date.isoformat(),
            "days_overdue": (now - inv.due_date).days
        }
        for inv in invoices
    ]
