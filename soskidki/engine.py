from decimal import Decimal
from discounts import money
from context import DiscountContext
from models import PricingResult


class PricingEngine:
    def calculate(self, order, discounts):
        discounts = list(discounts)
        goods_total = sum((item.product.base_price * item.quantity for item in order.items), Decimal('0'))
        base_total = money(goods_total + order.delivery_cost)
        context = DiscountContext(order, money(goods_total), money(order.delivery_cost))

        # Stage 1: quantity discounts.
        for discount in discounts:
            if discount.stage == 1:
                discount.apply(context)

        # Stage 2: choose between the regular percent and percentage promo.
        regular = next((d for d in discounts if d.stage == 2 and d.percentage_candidate), None)
        promo = next((d for d in discounts if d.stage == 2 and d.promo_candidate and d.valid(context)), None)
        if regular and promo:
            selected = promo if promo.amount_for(context.current_total) >= regular.amount_for(context.current_total) else regular
        else:
            selected = promo or regular

        competitor_done = False
        for discount in discounts:
            if discount.stage != 2:
                continue
            if discount.percentage_candidate or discount.promo_candidate:
                if not competitor_done:
                    if selected is not None:
                        selected.apply(context)
                    competitor_done = True
            else:
                discount.apply(context)

        # Stage 3: fixed discounts, including fixed promo codes.
        for discount in discounts:
            if discount.stage == 3:
                discount.apply(context)

        # Stage 4: free delivery.
        for discount in discounts:
            if discount.stage == 4:
                discount.apply(context)

        final_total = money(context.current_total + context.delivery_cost)
        return PricingResult(base_total, context.applied_discounts, max(final_total, Decimal('0.00')))
