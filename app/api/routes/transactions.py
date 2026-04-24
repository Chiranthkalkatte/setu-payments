from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.db.session import get_db
from app.schemas.schemas import TransactionDetailResponse, TransactionListResponse
from app.services.transaction_service import get_transactions, get_transactions_details

router = APIRouter()


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    merchant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("initiated_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db)
):
    return await get_transactions(
        db=db,
        merchant_id=merchant_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )



@router.get("/transactions/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await get_transactions_details(db, transaction_id)
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return result