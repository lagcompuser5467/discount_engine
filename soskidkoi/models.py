from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Product:
    id: str
    name: str
    base_price: Decimal
    category: str


@dataclass
class CartItem:
    product: Product
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Количество должно быть больше 0")


@dataclass
class Customer:
    id: str
    last_purchase_date: datetime | None
    is_first_order: bool


@dataclass
class Order:
    id: str
    customer: Customer
    items: list[CartItem]
    promo_code: str | None
    created_at: datetime
    delivery_cost: Decimal


@dataclass
class AppliedDiscount:
    name: str
    amount: Decimal
    reason: str


@dataclass
class PricingResult:
    base_total: Decimal
    applied_discounts: list[AppliedDiscount]
    final_total: Decimal