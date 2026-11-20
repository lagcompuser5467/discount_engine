from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class Product:
    id: str
    name: str
    base_price: Decimal
    category: str

    def __post_init__(self):
        self.base_price = Decimal(str(self.base_price))
        if self.base_price < 0:
            raise ValueError('Цена не может быть отрицательной')


@dataclass
class CartItem:
    product: Product
    quantity: int

    def __post_init__(self):
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError('Количество должно быть целым числом больше 0')


@dataclass
class Customer:
    id: str
    last_purchase_date: date | datetime | None = None
    is_first_order: bool = False


@dataclass
class Order:
    id: str
    customer: Customer
    items: list[CartItem]
    promo_code: str | None
    created_at: datetime
    delivery_cost: Decimal

    def __post_init__(self):
        self.delivery_cost = Decimal(str(self.delivery_cost))
        if self.delivery_cost < 0:
            raise ValueError('Стоимость доставки не может быть отрицательной')


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
