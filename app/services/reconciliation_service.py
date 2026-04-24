from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.models.models import Transaction, Merchant, ReconciliationFlag


async def get_summary(db: AsyncSession):
    # --- Summary by merchant ---
    merchant_result = await db.execute(
        select(
            Transaction.merchant_id,
            Merchant.merchant_name,
            func.count(Transaction.id).label("total_transactions"),
            func.sum(Transaction.amount).label("total_amount"),
            func.sum(case((Transaction.status == "payment_initiated", 1), else_=0)).label("initiated"),
            func.sum(case((Transaction.status == "payment_processed", 1), else_=0)).label("processed"),
            func.sum(case((Transaction.status == "payment_failed", 1), else_=0)).label("failed"),
            func.sum(case((Transaction.status == "settled", 1), else_=0)).label("settled"),
        )
        .join(Merchant, Merchant.merchant_id == Transaction.merchant_id)
        .group_by(Transaction.merchant_id, Merchant.merchant_name)
    )
    by_merchant = [
        {
            "merchant_id": row.merchant_id,
            "merchant_name": row.merchant_name,
            "total_transactions": row.total_transactions,
            "total_amount": float(row.total_amount or 0),
            "initiated": row.initiated,
            "processed": row.processed,
            "failed": row.failed,
            "settled": row.settled,
        }
        for row in merchant_result.all()
    ]


    by_date_result = await db.execute(
        select(
            func.date(Transaction.initiated_at).label("date"),
            func.count(Transaction.id).label("total_transactions"),
            func.sum(Transaction.amount).label("total_amount"),
            func.sum(case((Transaction.status == "payment_initiated", 1), else_=0)).label("initiated"),
            func.sum(case((Transaction.status == "payment_processed", 1), else_=0)).label("processed"),
            func.sum(case((Transaction.status == "payment_failed", 1), else_=0)).label("failed"),
            func.sum(case((Transaction.status == "settled", 1), else_=0)).label("settled"),
        )
        .group_by(func.date(Transaction.initiated_at))
        .order_by(func.date(Transaction.initiated_at).desc())
    )
    by_date = [
        {
            "date": str(row.date),
            "total_transactions": row.total_transactions,
            "total_amount": float(row.total_amount or 0),
            "initiated": row.initiated,
            "processed": row.processed,
            "failed": row.failed,
            "settled": row.settled,
        }
        for row in by_date_result.all()
    ]

    return {
        "by_merchant": by_merchant,
        "by_date": by_date,
    }


async def get_discrepancies(db: AsyncSession):
    # Fetch transactions that have reconciliation flags
    result = await db.execute(
        select(
            Transaction.transaction_id,
            Transaction.merchant_id,
            Transaction.amount,
            Transaction.currency,
            Transaction.status,
            Transaction.settlement_status,
            Transaction.initiated_at,
            ReconciliationFlag.flag_type,
            ReconciliationFlag.description,
            ReconciliationFlag.detected_at,
        )
        .join(ReconciliationFlag, ReconciliationFlag.transaction_id == Transaction.transaction_id)
        .order_by(ReconciliationFlag.detected_at.desc())
    )
    rows = result.all()

    data = [
        {
            "transaction_id": row.transaction_id,
            "merchant_id": row.merchant_id,
            "amount": float(row.amount),
            "currency": row.currency,
            "status": row.status,
            "settlement_status": row.settlement_status,
            "flag_type": row.flag_type,
            "description": row.description,
            "detected_at": row.detected_at,
            "initiated_at": row.initiated_at,
        }
        for row in rows
    ]

    return {
        "total": len(data),
        "data": data,
    }