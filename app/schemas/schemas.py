from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field

EventType = Literal["payment_initiated", "payment_processed", "payment_failed", "settled"]



class EventIngest(BaseModel):
    event_id: str
    event_type: EventType
    transaction_id: str
    merchant_id: str
    merchant_name: str
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    timestamp: datetime


class EventIngestResponse(BaseModel):
    status: Literal["success", "duplicate"]
    event_id: str
    transaction_id: str
    message: str


class TransactionListItem(BaseModel):
    transaction_id: str
    merchant_id: str
    merchant_name: str
    amount: float
    currency: str
    status: str
    settlement_status: Optional[str]
    initiated_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

class TransactionListResponse(BaseModel):
    data: List[TransactionListItem]
    pagination: PaginationMeta


class EventHistoryItem(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    ingested_at: datetime
    amount: float
    currency: str

    model_config = {"from_attributes": True}


class MerchantInfo(BaseModel):
    merchant_id: str
    merchant_name: str

    model_config = {"from_attributes": True}


class TransactionDetailResponse(BaseModel):
    transaction_id: str
    merchant: MerchantInfo
    amount: float
    currency: str
    status: str
    settlement_status: Optional[str]
    initiated_at: datetime
    updated_at: datetime
    event_history: List[EventHistoryItem]


class SummaryByMerchant(BaseModel):
    merchant_id: str
    merchant_name: str
    total_transactions: int
    total_amount: float
    initiated: int
    processed: int
    failed: int
    settled: int


class SummaryByDate(BaseModel):
    date: str
    total_transactions: int
    total_amount: float
    initiated: int
    processed: int
    failed: int
    settled: int


class ReconciliationSummaryResponse(BaseModel):
    by_merchant: List[SummaryByMerchant]
    by_date: List[SummaryByDate]


class DiscrepancyItem(BaseModel):
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    status: str
    settlement_status: Optional[str]
    flag_type: str
    description: str
    detected_at: datetime
    initiated_at: datetime

    model_config = {"from_attributes": True}


class DiscrepanciesResponse(BaseModel):
    total: int
    data: List[DiscrepancyItem]