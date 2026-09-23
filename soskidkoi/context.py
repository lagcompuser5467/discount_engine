from dataclasses import dataclass, field
from decimal import Decimal

from models import Order, AppliedDiscount


@dataclass
class DiscountContext:
    order: Order
    current_total: Decimal
    delivery_cost: Decimal
    applied_discounts: list[AppliedDiscount] = field(default_factory=list)