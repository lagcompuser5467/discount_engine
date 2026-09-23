from datetime import datetime, timedelta
from decimal import Decimal

from models import Product, CartItem, Customer, Order
from factory import DiscountFactory
from config import ConfigProvider
from engine import PricingEngine


def main():

    headphones = Product(
        "1",
        "Наушники",
        Decimal("3000"),
        "electronics"
    )

    mouse = Product(
        "2",
        "Мышь",
        Decimal("1000"),
        "electronics"
    )

    customer = Customer(
        "1",
        datetime.now() - timedelta(days=10),
        False
    )

    order = Order(
        "100",
        customer,
        [
            CartItem(headphones, 2),
            CartItem(mouse, 1)
        ],
        None,
        datetime.now(),
        Decimal("300")
    )

    discounts = [
        DiscountFactory.create(
            "three_for_two",
            {
                "category": "electronics"
            }
        ),

        DiscountFactory.create(
            "percent",
            {
                "percent": 10
            }
        ),

        DiscountFactory.create(
            "loyalty",
            {
                "percent": 5
            }
        ),

        DiscountFactory.create(
            "free_delivery",
            {
                "threshold": 4000
            }
        )
    ]

    config = ConfigProvider()
    config.set_discounts(discounts)

    engine = PricingEngine()

    result = engine.calculate(
        order,
        config.get_discounts()
    )

    print("Начальная сумма:", result.base_total, "₽")
    print()
    print("Применённые скидки:")

    for discount in result.applied_discounts:
        print(
            "-",
            discount.name,
            ": -",
            discount.amount,
            "₽",
            "(" + discount.reason + ")"
        )

    print()
    print("Итоговая сумма:", result.final_total, "₽")


if __name__ == "__main__":
    main()