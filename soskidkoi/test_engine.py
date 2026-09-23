from datetime import datetime, timedelta
from decimal import Decimal

from models import Product, CartItem, Customer, Order
from factory import DiscountFactory
from engine import PricingEngine


def create_order(
    items,
    promo_code=None,
    last_purchase_date=None,
    is_first_order=False,
    delivery_cost="0",
    created_at=None
):

    if created_at is None:
        created_at = datetime(2026, 9, 23, 12, 0)

    customer = Customer(
        "1",
        last_purchase_date,
        is_first_order
    )

    return Order(
        "100",
        customer,
        items,
        promo_code,
        created_at,
        Decimal(delivery_cost)
    )


def calculate(order, configs):

    discounts = []

    for discount_type, config in configs:
        discounts.append(
            DiscountFactory.create(
                discount_type,
                config
            )
        )

    engine = PricingEngine()

    return engine.calculate(
        order,
        discounts
    )


def test_percent_discount():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "other"
    )

    order = create_order([
        CartItem(product, 1)
    ])

    result = calculate(
        order,
        [
            ("percent", {"percent": 10})
        ]
    )

    assert result.final_total == Decimal("900.00")


def test_fixed_discount():

    product = Product(
        "1",
        "Товар",
        Decimal("2000"),
        "other"
    )

    order = create_order([
        CartItem(product, 1)
    ])

    result = calculate(
        order,
        [
            (
                "fixed",
                {
                    "amount": 500,
                    "threshold": 1000
                }
            )
        ]
    )

    assert result.final_total == Decimal("1500.00")


def test_fixed_discount_not_applied():

    product = Product(
        "1",
        "Товар",
        Decimal("500"),
        "other"
    )

    order = create_order([
        CartItem(product, 1)
    ])

    result = calculate(
        order,
        [
            (
                "fixed",
                {
                    "amount": 500,
                    "threshold": 1000
                }
            )
        ]
    )

    assert result.final_total == Decimal("500.00")


def test_three_for_two():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "electronics"
    )

    order = create_order([
        CartItem(product, 3)
    ])

    result = calculate(
        order,
        [
            (
                "three_for_two",
                {
                    "category": "electronics"
                }
            )
        ]
    )

    assert result.final_total == Decimal("2000.00")


def test_three_for_two_before_percent():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "electronics"
    )

    order = create_order([
        CartItem(product, 3)
    ])

    result = calculate(
        order,
        [
            ("percent", {"percent": 10}),
            (
                "three_for_two",
                {
                    "category": "electronics"
                }
            )
        ]
    )

    assert result.final_total == Decimal("1800.00")

    assert result.applied_discounts[0].name == "Три по цене двух"


def test_loyalty_discount():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "other"
    )

    created_at = datetime(2026, 9, 23, 12, 0)

    order = create_order(
        [
            CartItem(product, 1)
        ],
        last_purchase_date=created_at - timedelta(days=30),
        created_at=created_at
    )

    result = calculate(
        order,
        [
            ("loyalty", {"percent": 5})
        ]
    )

    assert result.final_total == Decimal("950.00")


def test_loyalty_not_applied_after_30_days():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "other"
    )

    created_at = datetime(2026, 9, 23, 12, 0)

    order = create_order(
        [
            CartItem(product, 1)
        ],
        last_purchase_date=created_at - timedelta(days=31),
        created_at=created_at
    )

    result = calculate(
        order,
        [
            ("loyalty", {"percent": 5})
        ]
    )

    assert result.final_total == Decimal("1000.00")


def test_first_order():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "other"
    )

    order = create_order(
        [
            CartItem(product, 1)
        ],
        is_first_order=True
    )

    result = calculate(
        order,
        [
            ("first_order", {"percent": 10})
        ]
    )

    assert result.final_total == Decimal("900.00")


def test_free_delivery():

    product = Product(
        "1",
        "Товар",
        Decimal("5000"),
        "other"
    )

    order = create_order(
        [
            CartItem(product, 1)
        ],
        delivery_cost="500"
    )

    result = calculate(
        order,
        [
            (
                "free_delivery",
                {
                    "threshold": 4000
                }
            )
        ]
    )

    assert result.final_total == Decimal("5000.00")


def test_free_delivery_at_threshold():

    product = Product(
        "1",
        "Товар",
        Decimal("4000"),
        "other"
    )

    order = create_order(
        [
            CartItem(product, 1)
        ],
        delivery_cost="500"
    )

    result = calculate(
        order,
        [
            (
                "free_delivery",
                {
                    "threshold": 4000
                }
            )
        ]
    )

    assert result.final_total == Decimal("4500.00")


def test_promo_code():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "other"
    )

    order = create_order(
        [
            CartItem(product, 1)
        ],
        promo_code="SALE20"
    )

    result = calculate(
        order,
        [
            (
                "promo",
                {
                    "code": "SALE20",
                    "discount_type": "percent",
                    "amount": 20
                }
            )
        ]
    )

    assert result.final_total == Decimal("800.00")


def test_promo_wins_over_percent():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "other"
    )

    order = create_order(
        [
            CartItem(product, 1)
        ],
        promo_code="SALE20"
    )

    result = calculate(
        order,
        [
            ("percent", {"percent": 10}),
            (
                "promo",
                {
                    "code": "SALE20",
                    "discount_type": "percent",
                    "amount": 20
                }
            )
        ]
    )

    assert result.final_total == Decimal("800.00")

    assert result.applied_discounts[0].name == "Промокод"


def test_promo_tie_wins():

    product = Product(
        "1",
        "Товар",
        Decimal("1000"),
        "other"
    )

    order = create_order(
        [
            CartItem(product, 1)
        ],
        promo_code="SALE10"
    )

    result = calculate(
        order,
        [
            ("percent", {"percent": 10}),
            (
                "promo",
                {
                    "code": "SALE10",
                    "discount_type": "percent",
                    "amount": 10
                }
            )
        ]
    )

    assert result.final_total == Decimal("900.00")

    assert result.applied_discounts[0].name == "Промокод"


def test_big_fixed_discount():

    product = Product(
        "1",
        "Товар",
        Decimal("100"),
        "other"
    )

    order = create_order([
        CartItem(product, 1)
    ])

    result = calculate(
        order,
        [
            (
                "fixed",
                {
                    "amount": 500,
                    "threshold": 50
                }
            )
        ]
    )

    assert result.final_total == Decimal("0.00")


def test_breakdown_order():

    product = Product(
        "1",
        "Товар",
        Decimal("3000"),
        "electronics"
    )

    customer = Customer(
        "1",
        datetime(2026, 9, 13, 12, 0),
        False
    )

    order = Order(
        "100",
        customer,
        [
            CartItem(product, 3)
        ],
        None,
        datetime(2026, 9, 23, 12, 0),
        Decimal("500")
    )

    result = calculate(
        order,
        [
            (
                "three_for_two",
                {
                    "category": "electronics"
                }
            ),
            ("percent", {"percent": 10}),
            ("loyalty", {"percent": 5}),
            (
                "free_delivery",
                {
                    "threshold": 4000
                }
            )
        ]
    )

    names = []

    for discount in result.applied_discounts:
        names.append(discount.name)

    assert names == [
        "Три по цене двух",
        "Процентная скидка",
        "Скидка постоянного клиента",
        "Бесплатная доставка"
    ]