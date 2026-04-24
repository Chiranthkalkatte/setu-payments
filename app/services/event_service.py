from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Merchant, Transaction, PaymentEvent
from app.schemas.schemas import EventIngest


VALID_TRANSITIONS = {
    "payment_initiated": ["payment_processed", "payment_failed"],
    "payment_processed": ["settled", "payment_failed"],
    "payment_failed": [],
    "settled": [],
}

EVENT_TO_STATUS = {
    "payment_initiated": "payment_initiated",
    "payment_processed": "payment_processed",
    "payment_failed": "payment_failed",
    "settled": "settled",
}


async def ingest_event(db: AsyncSession, event: EventIngest) -> dict:

    existing_event = await db.execute(
        select(PaymentEvent).where(PaymentEvent.event_id == event.event_id)
    )
    if existing_event.scalar_one_or_none():
        return {
            "status": "duplicate",
            "event_id": event.event_id,
            "transaction_id": event.transaction_id,
            "message": f"Event {event.event_id} already processed"
        }

    # STEP 2 — Upsert merchant
    existing_merchant = await db.execute(
        select(Merchant).where(Merchant.merchant_id == event.merchant_id)
    )
    merchant = existing_merchant.scalar_one_or_none()
    if not merchant:
        merchant = Merchant(
            merchant_id=event.merchant_id,
            merchant_name=event.merchant_name
        )
        db.add(merchant)
        await db.flush()  # flush so merchant exists before transaction FK

    # STEP 3 — Create or update transaction
    existing_txn = await db.execute(
        select(Transaction).where(Transaction.transaction_id == event.transaction_id)
    )
    transaction = existing_txn.scalar_one_or_none()

    if not transaction:
        # First event for this transaction — create it
        transaction = Transaction(
            transaction_id=event.transaction_id,
            merchant_id=event.merchant_id,
            amount=event.amount,
            currency=event.currency,
            status=EVENT_TO_STATUS[event.event_type],
            initiated_at=event.timestamp,
            updated_at=event.timestamp,
        )
        if event.event_type == "settled":
            transaction.settlement_status = "settled"
        db.add(transaction)
        await db.flush()
    else:
        # Subsequent event — only update if valid transition
        current_status = transaction.status
        new_status = EVENT_TO_STATUS[event.event_type]

        if new_status in VALID_TRANSITIONS.get(current_status, []):
            transaction.status = new_status
            transaction.updated_at = event.timestamp
            if event.event_type == "settled":
                transaction.settlement_status = "settled"

    # STEP 4 — Insert event (always, even if state didn't change)
    payment_event = PaymentEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        transaction_id=event.transaction_id,
        merchant_id=event.merchant_id,
        amount=event.amount,
        currency=event.currency,
        timestamp=event.timestamp,
    )
    db.add(payment_event)

    return {
        "status": "success",
        "event_id": event.event_id,
        "transaction_id": event.transaction_id,
        "message": f"Event {event.event_type} accepted for transaction {event.transaction_id}"
    }