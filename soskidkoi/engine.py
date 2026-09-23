from decimal import Decimal

from context import DiscountContext
from models import PricingResult
from discounts import money


class PricingEngine:

    def calculate(self, order, discounts):

        base_total = Decimal("0")

        for item in order.items:
            base_total += (
                item.product.base_price * item.quantity
            )

        base_total = money(base_total)

        context = DiscountContext(
            order,
            base_total,
            order.delivery_cost
        )

        # 1. Сначала 3 по цене 2
        for discount in discounts:
            if discount.stage == 1:
                discount.apply(context)

        # 2. Процентные скидки
        normal_percent = None
        promo_percent = None

        for discount in discounts:
            if discount.stage == 2:

                if discount.is_promo():
                    if discount.is_valid(context):
                        promo_percent = discount

                elif discount.is_percent():
                    normal_percent = discount

        # Сравниваем обычную процентную скидку
        # и процентный промокод
        if normal_percent is not None and promo_percent is not None:

            normal_amount = (
                context.current_total
                * normal_percent.percent
                / Decimal("100")
            )

            promo_amount = promo_percent.calculate_amount(
                context.current_total
            )

            if promo_amount >= normal_amount:
                promo_percent.apply(context)
            else:
                normal_percent.apply(context)

        elif promo_percent is not None:
            promo_percent.apply(context)

        elif normal_percent is not None:
            normal_percent.apply(context)

        # Лояльность и первый заказ
        for discount in discounts:
            if discount.stage == 2:
                if not discount.is_percent() and not discount.is_promo():
                    discount.apply(context)

        # 3. Фиксированные скидки
        for discount in discounts:
            if discount.stage == 3:
                discount.apply(context)

        # 4. Бесплатная доставка
        for discount in discounts:
            if discount.stage == 4:
                discount.apply(context)

        final_total = money(
            context.current_total
            + context.delivery_cost
        )

        if final_total < 0:
            final_total = Decimal("0.00")

        return PricingResult(
            base_total,
            context.applied_discounts,
            final_total
        )