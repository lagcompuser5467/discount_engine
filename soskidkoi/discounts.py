from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_EVEN

from context import DiscountContext
from models import AppliedDiscount


def money(value):
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_EVEN
    )


class Discount(ABC):

    stage = 0

    @abstractmethod
    def apply(self, context: DiscountContext):
        pass

    def is_percent(self):
        return False

    def is_promo(self):
        return False


class PercentDiscount(Discount):

    stage = 2

    def __init__(self, percent):
        self.percent = Decimal(str(percent))

    def is_percent(self):
        return True

    def apply(self, context):
        if context.current_total <= 0:
            return

        amount = money(
            context.current_total
            * self.percent
            / Decimal("100")
        )

        if amount <= 0:
            return

        context.current_total = money(
            context.current_total - amount
        )

        context.applied_discounts.append(
            AppliedDiscount(
                "Процентная скидка",
                amount,
                f"Скидка {self.percent}%"
            )
        )


class FixedDiscount(Discount):

    stage = 3

    def __init__(self, amount, threshold):
        self.amount = Decimal(str(amount))
        self.threshold = Decimal(str(threshold))

    def apply(self, context):
        if context.current_total < self.threshold:
            return

        amount = min(
            self.amount,
            context.current_total
        )

        amount = money(amount)

        if amount <= 0:
            return

        context.current_total = money(
            context.current_total - amount
        )

        context.applied_discounts.append(
            AppliedDiscount(
                "Фиксированная скидка",
                amount,
                f"Сумма заказа от {self.threshold} ₽"
            )
        )


class ThreeForTwoDiscount(Discount):

    stage = 1

    def __init__(self, category):
        self.category = category

    def apply(self, context):
        prices = []

        for item in context.order.items:
            if item.product.category == self.category:
                for i in range(item.quantity):
                    prices.append(item.product.base_price)

        free_count = len(prices) // 3

        if free_count == 0:
            return

        prices.sort()

        amount = Decimal("0")

        for i in range(free_count):
            amount += prices[i]

        amount = money(amount)

        if amount > context.current_total:
            amount = context.current_total

        context.current_total = money(
            context.current_total - amount
        )

        context.applied_discounts.append(
            AppliedDiscount(
                "Три по цене двух",
                amount,
                f"Бесплатных товаров: {free_count}"
            )
        )


class PromoCodeDiscount(Discount):

    def __init__(
        self,
        code,
        discount_type,
        amount,
        end_date=None,
        active=True
    ):
        self.code = code
        self.discount_type = discount_type
        self.amount = Decimal(str(amount))
        self.end_date = end_date
        self.active = active

        if discount_type == "percent":
            self.stage = 2
        else:
            self.stage = 3

    def is_percent(self):
        return self.discount_type == "percent"

    def is_promo(self):
        return True

    def is_valid(self, context):
        if not self.active:
            return False

        if context.order.promo_code != self.code:
            return False

        if self.end_date is not None:
            if context.order.created_at > self.end_date:
                return False

        return True

    def calculate_amount(self, current_total):
        if self.discount_type == "percent":
            return money(
                current_total
                * self.amount
                / Decimal("100")
            )

        return money(
            min(self.amount, current_total)
        )

    def apply(self, context):
        if not self.is_valid(context):
            return

        amount = self.calculate_amount(
            context.current_total
        )

        if amount <= 0:
            return

        context.current_total = money(
            context.current_total - amount
        )

        context.applied_discounts.append(
            AppliedDiscount(
                "Промокод",
                amount,
                f"Промокод {self.code}"
            )
        )


class LoyaltyDiscount(Discount):

    stage = 2

    def __init__(self, percent=5):
        self.percent = Decimal(str(percent))

    def apply(self, context):
        customer = context.order.customer

        if customer.last_purchase_date is None:
            return

        days = (
            context.order.created_at.date()
            - customer.last_purchase_date.date()
        ).days

        if days < 0 or days > 30:
            return

        amount = money(
            context.current_total
            * self.percent
            / Decimal("100")
        )

        if amount <= 0:
            return

        context.current_total = money(
            context.current_total - amount
        )

        context.applied_discounts.append(
            AppliedDiscount(
                "Скидка постоянного клиента",
                amount,
                f"Покупка была {days} дней назад"
            )
        )


class FreeDeliveryDiscount(Discount):

    stage = 4

    def __init__(self, threshold):
        self.threshold = Decimal(str(threshold))

    def apply(self, context):
        if context.current_total <= self.threshold:
            return

        if context.delivery_cost <= 0:
            return

        amount = money(context.delivery_cost)

        context.delivery_cost = Decimal("0.00")

        context.applied_discounts.append(
            AppliedDiscount(
                "Бесплатная доставка",
                amount,
                f"Сумма товаров больше {self.threshold} ₽"
            )
        )


class FirstOrderDiscount(Discount):

    stage = 2

    def __init__(self, percent=10):
        self.percent = Decimal(str(percent))

    def apply(self, context):
        if not context.order.customer.is_first_order:
            return

        amount = money(
            context.current_total
            * self.percent
            / Decimal("100")
        )

        if amount <= 0:
            return

        context.current_total = money(
            context.current_total - amount
        )

        context.applied_discounts.append(
            AppliedDiscount(
                "Скидка на первый заказ",
                amount,
                f"Первый заказ, скидка {self.percent}%"
            )
        )