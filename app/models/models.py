from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.merchant_id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="payment_initiated")
    settlement_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    merchant: Mapped["Merchant"] = relationship(back_populates="transactions")
    events: Mapped[list["PaymentEvent"]] = relationship(back_populates="transaction", order_by="PaymentEvent.timestamp")
    flags: Mapped[list["ReconciliationFlag"]] = relationship(back_populates="transaction")

    __table_args__ = (
        Index("ix_transactions_merchant_status", "merchant_id", "status"),
        Index("ix_transactions_initiated_at", "initiated_at"),
    )


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(64), ForeignKey("transactions.transaction_id"), nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transaction: Mapped["Transaction"] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_payment_events_transaction_id", "transaction_id"),
        Index("ix_payment_events_timestamp", "timestamp"),
    )


class ReconciliationFlag(Base):
    __tablename__ = "reconciliation_flags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(64), ForeignKey("transactions.transaction_id"), nullable=False)
    flag_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transaction: Mapped["Transaction"] = relationship(back_populates="flags")

    __table_args__ = (
        UniqueConstraint("transaction_id", "flag_type", name="uq_flag_per_transaction_type"),
        Index("ix_recon_flags_transaction_id", "transaction_id"),
    )
