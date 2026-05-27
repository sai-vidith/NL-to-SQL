"""
Nexus — Business domain ORM models (e-commerce analytics).

These tables represent the analytics data warehouse that generated SQL
queries will run against via the read-only database connection.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base


# ── Customer ───────────────────────────────────────────────────────
class BizCustomer(Base):
    __tablename__ = "biz_customers"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(
        String(100), nullable=False, default="India", server_default="India",
    )
    segment: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    orders: Mapped[list[BizOrder]] = relationship(
        "BizOrder", back_populates="customer", lazy="selectin",
    )
    reviews: Mapped[list[BizReview]] = relationship(
        "BizReview", back_populates="customer", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_biz_customers_email", "email"),
        Index("ix_biz_customers_segment", "segment"),
        Index("ix_biz_customers_city_state", "city", "state"),
    )

    def __repr__(self) -> str:
        return f"<BizCustomer id={self.customer_id!s} name={self.name!r}>"


# ── Product ────────────────────────────────────────────────────────
class BizProduct(Base):
    __tablename__ = "biz_products"

    product_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    sub_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False,
    )
    cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False,
    )
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    order_items: Mapped[list[BizOrderItem]] = relationship(
        "BizOrderItem", back_populates="product", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_biz_products_category", "category"),
        Index("ix_biz_products_sub_category", "sub_category"),
        Index("ix_biz_products_brand", "brand"),
    )

    def __repr__(self) -> str:
        return f"<BizProduct id={self.product_id!s} name={self.name!r}>"


# ── Order ──────────────────────────────────────────────────────────
class BizOrder(Base):
    __tablename__ = "biz_orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biz_customers.customer_id", ondelete="CASCADE"),
        nullable=False,
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ship_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    customer: Mapped[BizCustomer] = relationship(
        "BizCustomer", back_populates="orders",
    )
    items: Mapped[list[BizOrderItem]] = relationship(
        "BizOrderItem", back_populates="order", lazy="selectin",
    )
    payments: Mapped[list[BizPayment]] = relationship(
        "BizPayment", back_populates="order", lazy="selectin",
    )
    reviews: Mapped[list[BizReview]] = relationship(
        "BizReview", back_populates="order", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_biz_orders_customer_id", "customer_id"),
        Index("ix_biz_orders_order_date", "order_date"),
        Index("ix_biz_orders_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<BizOrder id={self.order_id!s} "
            f"date={self.order_date} status={self.status!r}>"
        )


# ── OrderItem ──────────────────────────────────────────────────────
class BizOrderItem(Base):
    __tablename__ = "biz_order_items"

    item_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biz_orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biz_products.product_id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0.00",
    )

    # ── Relationships ──────────────────────────────────────────────
    order: Mapped[BizOrder] = relationship("BizOrder", back_populates="items")
    product: Mapped[BizProduct] = relationship("BizProduct", back_populates="order_items")

    __table_args__ = (
        Index("ix_biz_order_items_order_id", "order_id"),
        Index("ix_biz_order_items_product_id", "product_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<BizOrderItem id={self.item_id!s} "
            f"order={self.order_id!s} qty={self.quantity}>"
        )


# ── Payment ────────────────────────────────────────────────────────
class BizPayment(Base):
    __tablename__ = "biz_payments"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biz_orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────
    order: Mapped[BizOrder] = relationship("BizOrder", back_populates="payments")

    __table_args__ = (
        Index("ix_biz_payments_order_id", "order_id"),
        Index("ix_biz_payments_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<BizPayment id={self.payment_id!s} "
            f"method={self.payment_method!r} amount={self.amount}>"
        )

    # ── Relationships ──────────────────────────────────────────────
    order: Mapped[BizOrder] = relationship("BizOrder", back_populates="payments")

    __table_args__ = (
        Index("ix_biz_payments_order_id", "order_id"),
        Index("ix_biz_payments_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<BizPayment id={self.payment_id!s} "
            f"method={self.payment_method!r} amount={self.amount}>"
        )


# ── Seller ─────────────────────────────────────────────────────────
class BizSeller(Base):
    __tablename__ = "biz_sellers"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("5.00"), server_default="5.00",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )

    __table_args__ = (
        Index("ix_biz_sellers_region", "region"),
        Index("ix_biz_sellers_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<BizSeller id={self.seller_id!s} name={self.name!r}>"


# ── Review ─────────────────────────────────────────────────────────
class BizReview(Base):
    __tablename__ = "biz_reviews"

    review_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biz_orders.order_id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biz_customers.customer_id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    order: Mapped[BizOrder] = relationship("BizOrder", back_populates="reviews")
    customer: Mapped[BizCustomer] = relationship("BizCustomer", back_populates="reviews")

    __table_args__ = (
        Index("ix_biz_reviews_order_id", "order_id"),
        Index("ix_biz_reviews_customer_id", "customer_id"),
        Index("ix_biz_reviews_rating", "rating"),
    )

    def __repr__(self) -> str:
        return (
            f"<BizReview id={self.review_id!s} "
            f"rating={self.rating} customer={self.customer_id!s}>"
        )
