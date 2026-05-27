"""
Database seeding script.
Generates sample e-commerce business data (customers, products, orders, reviews, etc.)
and default users (admin/viewer) to populate the database for immediate analytics use.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database.session import AsyncSessionFactory
from app.database.models import Base
from app.database.models.user import User
from app.database.models.business import (
    BizCustomer,
    BizProduct,
    BizOrder,
    BizOrderItem,
    BizPayment,
    BizSeller,
    BizReview,
)

logger = structlog.get_logger(__name__)

async def seed_data(session: AsyncSession) -> None:
    # ── 1. Create Default Users ──────────────────────────────────
    logger.info("seeding.users", status="start")
    
    admin = User(
        username="admin",
        email="admin@nexus.com",
        password_hash=hash_password("admin1234"),
        role="admin",
        is_active=True,
    )
    
    session.add_all([admin])
    await session.flush()
    logger.info("seeding.users", status="completed")

    # ── 2. Create Sellers ────────────────────────────────────────
    logger.info("seeding.sellers", status="start")
    sellers = [
        BizSeller(name="TechHub North", region="North", commission_rate=Decimal("4.50")),
        BizSeller(name="StyleZone West", region="West", commission_rate=Decimal("6.00")),
        BizSeller(name="HomeDirect South", region="South", commission_rate=Decimal("5.00")),
    ]
    session.add_all(sellers)
    await session.flush()
    
    # ── 3. Create Products ───────────────────────────────────────
    logger.info("seeding.products", status="start")
    products = [
        BizProduct(name="Quantum Pro Wireless Headphones", category="Electronics", sub_category="Audio", price=Decimal("8999.00"), cost=Decimal("5200.00"), brand="Quantum"),
        BizProduct(name="Apex Curved Gaming Monitor 27\"", category="Electronics", sub_category="Monitors", price=Decimal("24999.00"), cost=Decimal("17000.00"), brand="Apex"),
        BizProduct(name="FitTrack Sports Watch v2", category="Electronics", sub_category="Wearables", price=Decimal("5499.00"), cost=Decimal("3100.00"), brand="FitTrack"),
        
        BizProduct(name="Classic Leather Oxford Shoes", category="Clothing", sub_category="Footwear", price=Decimal("3499.00"), cost=Decimal("1800.00"), brand="RedTape"),
        BizProduct(name="Premium Slim Fit Cotton Shirt", category="Clothing", sub_category="Apparel", price=Decimal("1499.00"), cost=Decimal("650.00"), brand="Zara"),
        
        BizProduct(name="Smart Brew Espresso Machine", category="Home & Kitchen", sub_category="Appliances", price=Decimal("18999.00"), cost=Decimal("12500.00"), brand="BrewMaster"),
        BizProduct(name="Ergonomic Memory Foam Pillow", category="Home & Kitchen", sub_category="Bedding", price=Decimal("1999.00"), cost=Decimal("950.00"), brand="SleepWell"),
        
        BizProduct(name="The Art of Clean Code", category="Books", sub_category="Tech", price=Decimal("599.00"), cost=Decimal("220.00"), brand="OReilly"),
    ]
    session.add_all(products)
    await session.flush()

    # ── 4. Create Customers ──────────────────────────────────────
    logger.info("seeding.customers", status="start")
    customers = [
        BizCustomer(name="Rajesh Kumar", email="rajesh.kumar@gmail.com", city="Mumbai", state="Maharashtra", segment="Consumer"),
        BizCustomer(name="Priya Sharma", email="priya.sharma@yahoo.com", city="Delhi", state="Delhi", segment="Consumer"),
        BizCustomer(name="Amit Patel", email="amit.patel@corp.in", city="Ahmedabad", state="Gujarat", segment="Corporate"),
        BizCustomer(name="Sneha Reddy", email="sneha.reddy@gmail.com", city="Hyderabad", state="Telangana", segment="Consumer"),
        BizCustomer(name="Vijay Singh", email="vijay.singh@office.co.in", city="Bangalore", state="Karnataka", segment="Corporate"),
    ]
    session.add_all(customers)
    await session.flush()

    # ── 5. Create Orders, OrderItems, Payments and Reviews ────────
    logger.info("seeding.orders", status="start")
    
    # Order 1: Rajesh buys Headphones & Pillow
    o1 = BizOrder(customer_id=customers[0].customer_id, order_date=date.today() - timedelta(days=12), ship_date=date.today() - timedelta(days=9), ship_mode="Standard", status="Delivered")
    session.add(o1)
    await session.flush()
    
    item1 = BizOrderItem(order_id=o1.order_id, product_id=products[0].product_id, quantity=1, unit_price=products[0].price, discount=Decimal("10.00"))
    item2 = BizOrderItem(order_id=o1.order_id, product_id=products[6].product_id, quantity=2, unit_price=products[6].price, discount=Decimal("0.00"))
    session.add_all([item1, item2])
    
    pay1 = BizPayment(order_id=o1.order_id, payment_method="Credit Card", amount=Decimal("12098.10"), status="Completed", paid_at=datetime.now() - timedelta(days=12))
    session.add(pay1)
    
    rev1 = BizReview(order_id=o1.order_id, customer_id=customers[0].customer_id, rating=5, review_text="Excellent headphones, pillow is comfortable.")
    session.add(rev1)

    # Order 2: Priya buys Espresso Machine
    o2 = BizOrder(customer_id=customers[1].customer_id, order_date=date.today() - timedelta(days=5), ship_date=date.today() - timedelta(days=3), ship_mode="Express", status="Delivered")
    session.add(o2)
    await session.flush()
    
    item3 = BizOrderItem(order_id=o2.order_id, product_id=products[5].product_id, quantity=1, unit_price=products[5].price, discount=Decimal("5.00"))
    session.add(item3)
    
    pay2 = BizPayment(order_id=o2.order_id, payment_method="UPI", amount=Decimal("18049.05"), status="Completed", paid_at=datetime.now() - timedelta(days=5))
    session.add(pay2)
    
    rev2 = BizReview(order_id=o2.order_id, customer_id=customers[1].customer_id, rating=4, review_text="Amazing coffee quality, slightly noisy.")
    session.add(rev2)

    # Order 3: Amit buys Monitor & Shirt
    o3 = BizOrder(customer_id=customers[2].customer_id, order_date=date.today() - timedelta(days=1), ship_mode="Standard", status="Pending")
    session.add(o3)
    await session.flush()
    
    item4 = BizOrderItem(order_id=o3.order_id, product_id=products[1].product_id, quantity=1, unit_price=products[1].price, discount=Decimal("0.00"))
    item5 = BizOrderItem(order_id=o3.order_id, product_id=products[4].product_id, quantity=3, unit_price=products[4].price, discount=Decimal("0.00"))
    session.add_all([item4, item5])
    
    pay3 = BizPayment(order_id=o3.order_id, payment_method="Net Banking", amount=Decimal("29496.00"), status="Pending")
    session.add(pay3)

    await session.commit()
    logger.info("seeding.database", status="success")

async def main():
    async with AsyncSessionFactory() as session:
        await seed_data(session)

if __name__ == "__main__":
    asyncio.run(main())
