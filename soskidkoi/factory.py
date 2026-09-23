from discounts import (
    PercentDiscount,
    FixedDiscount,
    ThreeForTwoDiscount,
    PromoCodeDiscount,
    LoyaltyDiscount,
    FreeDeliveryDiscount,
    FirstOrderDiscount
)


class DiscountFactory:

    @staticmethod
    def create(discount_type, config):

        if discount_type == "percent":
            return PercentDiscount(
                config["percent"]
            )

        if discount_type == "fixed":
            return FixedDiscount(
                config["amount"],
                config["threshold"]
            )

        if discount_type == "three_for_two":
            return ThreeForTwoDiscount(
                config["category"]
            )

        if discount_type == "promo":
            return PromoCodeDiscount(
                config["code"],
                config["discount_type"],
                config["amount"],
                config.get("end_date"),
                config.get("active", True)
            )

        if discount_type == "loyalty":
            return LoyaltyDiscount(
                config.get("percent", 5)
            )

        if discount_type == "free_delivery":
            return FreeDeliveryDiscount(
                config["threshold"]
            )

        if discount_type == "first_order":
            return FirstOrderDiscount(
                config.get("percent", 10)
            )

        raise ValueError(
            "Неизвестный тип скидки"
        )
