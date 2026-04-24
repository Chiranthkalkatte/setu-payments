from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import EventIngest, EventIngestResponse
from app.services.event_service import ingest_event

router = APIRouter()


@router.post("/events", response_model=EventIngestResponse)
async def post_event(
    event: EventIngest,
    db: AsyncSession = Depends(get_db)
):
    result = await ingest_event(db, event)
    return result