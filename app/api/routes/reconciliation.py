from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import ReconciliationSummaryResponse, DiscrepanciesResponse
from app.services.reconciliation_service import get_summary, get_discrepancies

router = APIRouter()


@router.get("/reconciliation/summary", response_model=ReconciliationSummaryResponse)
async def reconciliation_summary(db: AsyncSession = Depends(get_db)):
    return await get_summary(db)


@router.get("/reconciliation/discrepancies", response_model=DiscrepanciesResponse)
async def reconciliation_discrepancies(db: AsyncSession = Depends(get_db)):
    return await get_discrepancies(db)