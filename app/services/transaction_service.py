from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional
from app.models.models import Transaction, Merchant, PaymentEvent


async def get_transactions(
    db: AsyncSession,
    merchant_id: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "initiated_at",
    sort_order: str = "desc"
):
    # Base query — join merchant to get merchant_name
    query = select(Transaction, Merchant.merchant_name).join(
        Merchant, Merchant.merchant_id == Transaction.merchant_id
    )

    # Apply filters
    if merchant_id:
        query = query.where(Transaction.merchant_id == merchant_id)

    if status:
        query = query.where(Transaction.status == status)

    if from_date:
        query = query.where(Transaction.initiated_at >= from_date)

    if to_date:
        query = query.where(Transaction.initiated_at <= to_date)

    # Count total for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Sorting
    sort_column = getattr(Transaction, sort_by, Transaction.initiated_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    # Build response data
    data = []
    for transaction, merchant_name in rows:
        data.append({
            "transaction_id": transaction.transaction_id,
            "merchant_id": transaction.merchant_id,
            "merchant_name": merchant_name,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "status": transaction.status,
            "settlement_status": transaction.settlement_status,
            "initiated_at": transaction.initiated_at,
            "updated_at": transaction.updated_at,
        })

    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    }

async def get_transactions_details(db: AsyncSession, transaction_id: str):
    result = await db.execute(select (Transaction, Merchant.merchant_name).join(Merchant, Merchant.merchant_id == Transaction.merchant_id).where(Transaction.transaction_id == transaction_id))
    row = result.one_or_none()

    if not row:
        return None
    
    transaction, merchant_name = row
    events_result = await db.execute(select(PaymentEvent).where(PaymentEvent.transaction_id == transaction_id).order_by(PaymentEvent.timestamp.asc()))
    events = events_result.scalars().all()
    
    return {
        "transaction_id":transaction.transaction_id,
        "merchant": {
            "merchant_id":transaction.merchant_id,
            "merchant_name":merchant_name
        },
        "amount": float(transaction.amount),
        "currency": transaction.currency,
        "status": transaction.status,
        "settlement_status": transaction.settlement_status,
        "initiated_at": transaction.initiated_at,
        "updated_at": transaction.updated_at,
        "event_history": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "timestamp": e.timestamp,
                "ingested_at": e.ingested_at,
                "amount": float(e.amount),
                "currency": e.currency,
            }
            for e in events
        ]
    }