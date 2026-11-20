from datetime import datetime, timedelta
from decimal import Decimal
from models import Product, CartItem, Customer, Order
from factory import DiscountFactory
from config import ConfigProvider
from engine import PricingEngine

def main():
    items = [CartItem(Product('1', 'Наушники', Decimal('3000'), 'electronics'), 2),
              CartItem(Product('2', 'Мышь', Decimal('1000'), 'electronics'), 1)]
    customer = Customer('1', datetime.now() - timedelta(days=10), False)
    order = Order('100', customer, items, None, datetime.now(), Decimal('300'))
    provider = ConfigProvider()
    provider.set_discounts([
        DiscountFactory.create('three_for_two', {'category': 'electronics'}),
        DiscountFactory.create('percent', {'percent': 10, 'name': 'Осенняя распродажа'}),
        DiscountFactory.create('loyalty', {'percent': 5}),
        DiscountFactory.create('free_delivery', {'threshold': 4000}),
    ])
    result = PricingEngine().calculate(order, provider.get_discounts())
    print(f'Начальная сумма: {result.base_total} ₽')
    print('Применённые скидки:')
    for discount in result.applied_discounts:
        print(f'- {discount.name}: -{discount.amount} ₽ ({discount.reason})')
    print(f'Итог к оплате: {result.final_total} ₽')

if __name__ == '__main__': main()
