from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import date, datetime
from models import AppliedDiscount
from context import DiscountContext

CENT = Decimal('0.01')

def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_EVEN)

def as_date(value):
    return value.date() if isinstance(value, datetime) else value


class Discount(ABC):
    stage = 0
    percentage_candidate = False
    promo_candidate = False
    @abstractmethod
    def apply(self, context: DiscountContext):
        pass


def apply_amount(context, name, amount, reason):
    amount = money(min(Decimal(str(amount)), context.current_total))
    if amount <= 0:
        return
    context.current_total = money(context.current_total - amount)
    context.applied_discounts.append(AppliedDiscount(name, amount, reason))


class PercentDiscount(Discount):
    stage = 2
    percentage_candidate = True
    def __init__(self, percent, name='Процентная скидка'):
        self.percent = Decimal(str(percent)); self.name = name
        if not 0 <= self.percent <= 100: raise ValueError('Процент должен быть от 0 до 100')
    def amount_for(self, total): return money(Decimal(str(total)) * self.percent / 100)
    def apply(self, c): apply_amount(c, self.name, self.amount_for(c.current_total), f'Скидка {self.percent}%')

class FixedDiscount(Discount):
    stage = 3
    def __init__(self, amount, threshold, name='Фиксированная скидка'):
        self.amount, self.threshold, self.name = Decimal(str(amount)), Decimal(str(threshold)), name
        if self.amount < 0 or self.threshold < 0: raise ValueError('Скидка и порог не могут быть отрицательными')
    def apply(self, c):
        if c.current_total >= self.threshold:
            apply_amount(c, self.name, self.amount, f'Сумма товаров не меньше {self.threshold} ₽')

class ThreeForTwoDiscount(Discount):
    stage = 1
    name = '3 по цене 2'
    def __init__(self, category): self.category = category
    def apply(self, c):
        prices = [item.product.base_price for item in c.order.items if item.product.category == self.category for _ in range(item.quantity)]
        free_count = len(prices) // 3
        if free_count:
            prices.sort()
            amount = sum(prices[:free_count], Decimal('0'))
            apply_amount(c, self.name, amount, f'Категория {self.category}: {free_count} единиц бесплатно')

class PromoDiscount(Discount):
    def __init__(self, code, discount_type, amount, end_date=None, active=True):
        if discount_type not in ('percent', 'fixed'): raise ValueError('Тип промокода должен быть percent или fixed')
        self.code, self.discount_type = code, discount_type
        self.amount, self.end_date, self.active = Decimal(str(amount)), end_date, active
        self.stage = 2 if discount_type == 'percent' else 3
        self.promo_candidate = discount_type == 'percent'
        if self.amount < 0 or (discount_type == 'percent' and self.amount > 100): raise ValueError('Некорректный размер промокода')
    def valid(self, c):
        return self.active and bool(self.code) and c.order.promo_code == self.code and (self.end_date is None or as_date(c.order.created_at) <= as_date(self.end_date))
    def amount_for(self, total):
        if self.discount_type == 'percent': return money(Decimal(str(total)) * self.amount / 100)
        return money(min(self.amount, Decimal(str(total))))
    def apply(self, c):
        if not self.valid(c): return
        value = self.amount_for(c.current_total)
        if value > 0:
            apply_amount(c, 'Промокод', value, f'Промокод {self.code}')
            c.applied_promo_code = self.code

class LoyaltyDiscount(PercentDiscount):
    percentage_candidate = False
    def __init__(self, percent=5, days=30):
        super().__init__(percent, 'Лояльность'); self.days_limit = int(days)
    def apply(self, c):
        last = c.order.customer.last_purchase_date
        if last is None: return
        days = (as_date(c.order.created_at) - as_date(last)).days
        if 0 <= days <= self.days_limit:
            apply_amount(c, self.name, self.amount_for(c.current_total), f'Последняя покупка была {days} дней назад')

class FirstOrderDiscount(PercentDiscount):
    percentage_candidate = False
    def __init__(self, percent=10): super().__init__(percent, 'Первый заказ')
    def apply(self, c):
        if c.order.customer.is_first_order:
            apply_amount(c, self.name, self.amount_for(c.current_total), f'Первый заказ, скидка {self.percent}%')

class FreeDeliveryDiscount(Discount):
    stage = 4
    name = 'Бесплатная доставка'
    def __init__(self, threshold):
        self.threshold = Decimal(str(threshold))
        if self.threshold < 0: raise ValueError('Порог не может быть отрицательным')
    def apply(self, c):
        if c.current_total > self.threshold and c.delivery_cost > 0:
            amount = money(c.delivery_cost)
            c.delivery_cost = Decimal('0.00')
            c.applied_discounts.append(AppliedDiscount(self.name, amount, f'Сумма товаров больше {self.threshold} ₽'))
