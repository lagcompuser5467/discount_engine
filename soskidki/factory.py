from discounts import (PercentDiscount, FixedDiscount, ThreeForTwoDiscount, PromoDiscount,
                     LoyaltyDiscount, FreeDeliveryDiscount, FirstOrderDiscount)

class DiscountFactory:
    @staticmethod
    def create(kind, cfg):
        creators = {
            'percent': lambda: PercentDiscount(cfg['percent'], cfg.get('name', 'Процентная скидка')),
            'fixed': lambda: FixedDiscount(cfg['amount'], cfg['threshold'], cfg.get('name', 'Фиксированная скидка')),
            'three_for_two': lambda: ThreeForTwoDiscount(cfg['category']),
            'promo': lambda: PromoDiscount(cfg['code'], cfg['discount_type'], cfg['amount'], cfg.get('end_date'), cfg.get('active', True)),
            'loyalty': lambda: LoyaltyDiscount(cfg.get('percent', 5), cfg.get('days', 30)),
            'free_delivery': lambda: FreeDeliveryDiscount(cfg['threshold']),
            'first_order': lambda: FirstOrderDiscount(cfg.get('percent', 10)),
        }
        if kind not in creators: raise ValueError(f'Неизвестный тип скидки: {kind}')
        return creators[kind]()
