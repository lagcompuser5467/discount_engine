from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from models import Product, CartItem, Customer, Order
from factory import DiscountFactory
from engine import PricingEngine
from discounts import money
from config import ConfigProvider

NOW = datetime(2026, 9, 23, 12)
def order(price='1000', qty=1, category='other', promo=None, delivery='0', last=None, first=False, items=None, created=NOW):
    if items is None: items = [CartItem(Product('1', 'Товар', Decimal(price), category), qty)]
    return Order('1', Customer('1', last, first), items, promo, created, Decimal(delivery))
def calc(o, *configs):
    ds = [DiscountFactory.create(t, c) for t, c in configs]
    return PricingEngine().calculate(o, ds)

# All 7 strategy types: applicable and non-applicable cases
def test_percent_applies_and_breakdown():
    r=calc(order(), ('percent', {'percent':10}))
    assert r.final_total == Decimal('900.00') and r.applied_discounts[0].amount == Decimal('100.00')
def test_percent_zero_no_breakdown():
    r=calc(order(), ('percent', {'percent':0}))
    assert r.final_total == Decimal('1000.00') and not r.applied_discounts
def test_fixed_applies_at_threshold():
    r=calc(order(price='1000'), ('fixed', {'amount':250,'threshold':1000}))
    assert r.final_total == Decimal('750.00')
def test_fixed_below_threshold():
    r=calc(order(price='999'), ('fixed', {'amount':250,'threshold':1000}))
    assert r.final_total == Decimal('999.00') and not r.applied_discounts
def test_three_for_two_single_category_cheapest_free():
    items=[CartItem(Product('a','Дорогой',Decimal('500'),'book'),1),CartItem(Product('b','Дешевый',Decimal('100'),'book'),2)]
    r=calc(order(items=items), ('three_for_two', {'category':'book'}))
    assert r.final_total == Decimal('600.00') and r.applied_discounts[0].amount == Decimal('100.00')
def test_three_for_two_categories_not_mixed():
    items=[CartItem(Product('a','A',Decimal('100'),'A'),2),CartItem(Product('b','B',Decimal('100'),'B'),1)]
    r=calc(order(items=items), ('three_for_two', {'category':'A'}))
    assert r.final_total == Decimal('300.00') and not r.applied_discounts
def test_percent_promo_more_beneficial():
    r=calc(order(promo='SAVE'), ('percent',{'percent':10}), ('promo',{'code':'SAVE','discount_type':'percent','amount':20}))
    assert r.final_total==Decimal('800.00') and r.applied_discounts[0].name=='Промокод'
def test_percent_promo_equal_wins():
    r=calc(order(promo='SAVE'), ('percent',{'percent':10}), ('promo',{'code':'SAVE','discount_type':'percent','amount':10}))
    assert r.final_total==Decimal('900.00') and r.applied_discounts[0].name=='Промокод'
def test_regular_percent_wins():
    r=calc(order(promo='SAVE'), ('percent',{'percent':20}), ('promo',{'code':'SAVE','discount_type':'percent','amount':10}))
    assert r.final_total==Decimal('800.00') and r.applied_discounts[0].name=='Процентная скидка'
def test_fixed_promo_stacks_with_percent():
    r=calc(order(promo='SAVE'), ('percent',{'percent':10}), ('promo',{'code':'SAVE','discount_type':'fixed','amount':100}))
    assert r.final_total==Decimal('800.00')
def test_unknown_promo_not_applied():
    r=calc(order(promo='BAD'), ('promo',{'code':'SAVE','discount_type':'percent','amount':20}))
    assert r.final_total==Decimal('1000.00') and not r.applied_discounts
def test_expired_promo_not_applied():
    r=calc(order(promo='SAVE'), ('promo',{'code':'SAVE','discount_type':'fixed','amount':100,'end_date':NOW-timedelta(days=1)}))
    assert r.final_total==Decimal('1000.00') and not r.applied_discounts
def test_promo_end_date_inclusive():
    r=calc(order(promo='SAVE'), ('promo',{'code':'SAVE','discount_type':'fixed','amount':100,'end_date':NOW}))
    assert r.final_total==Decimal('900.00')
def test_promo_inactive():
    r=calc(order(promo='SAVE'), ('promo',{'code':'SAVE','discount_type':'percent','amount':20,'active':False}))
    assert r.final_total==Decimal('1000.00') and not r.applied_discounts
def test_loyalty_exactly_30_days():
    r=calc(order(last=NOW-timedelta(days=30)), ('loyalty',{}))
    assert r.final_total==Decimal('950.00')
def test_loyalty_31_days_no_discount():
    r=calc(order(last=NOW-timedelta(days=31)), ('loyalty',{}))
    assert r.final_total==Decimal('1000.00') and not r.applied_discounts
def test_loyalty_future_date_invalid():
    r=calc(order(last=NOW+timedelta(days=1)), ('loyalty',{}))
    assert r.final_total==Decimal('1000.00') and not r.applied_discounts
def test_first_order_discount_and_nonfirst():
    r=calc(order(first=True), ('first_order',{}))
    assert r.final_total==Decimal('900.00')
    r2=calc(order(first=False), ('first_order',{}))
    assert r2.final_total==Decimal('1000.00') and not r2.applied_discounts
def test_free_delivery_strict_threshold():
    r=calc(order(price='1000',delivery='300'), ('free_delivery',{'threshold':1000}))
    assert r.final_total==Decimal('1300.00') and not r.applied_discounts
    r2=calc(order(price='1001',delivery='300'), ('free_delivery',{'threshold':1000}))
    assert r2.final_total==Decimal('1001.00') and r2.applied_discounts[0].amount==Decimal('300.00')
def test_base_total_includes_delivery():
    r=calc(order(price='1000',delivery='300'), ('percent',{'percent':10}))
    assert r.base_total==Decimal('1300.00') and r.final_total==Decimal('1200.00')
def test_discount_order_and_stacking():
    r=calc(order(price='3000',qty=3,delivery='500',last=NOW-timedelta(days=12),first=True),
        ('three_for_two',{'category':'other'}),('percent',{'percent':10}),('loyalty',{}),('first_order',{}),('fixed',{'amount':50,'threshold':0}),('free_delivery',{'threshold':1000}))
    assert [d.name for d in r.applied_discounts]==['3 по цене 2','Процентная скидка','Лояльность','Первый заказ','Фиксированная скидка','Бесплатная доставка']
    assert r.base_total==Decimal('9500.00')
def test_round_half_even():
    assert money('1.005')==Decimal('1.00')
    assert money('1.015')==Decimal('1.02')
def test_empty_cart_still_charges_delivery():
    r=calc(order(items=[],delivery='250'), ('free_delivery',{'threshold':0}))
    assert r.base_total==Decimal('250.00') and r.final_total==Decimal('250.00')
def test_invalid_qty_rejected():
    with pytest.raises(ValueError): CartItem(Product('1','T',Decimal('10'),'x'),0)
def test_negative_product_price_rejected():
    with pytest.raises(ValueError): Product('1','T',Decimal('-1'),'x')
def test_negative_delivery_rejected():
    with pytest.raises(ValueError): order(delivery='-1')
def test_factory_unknown_type():
    with pytest.raises(ValueError): DiscountFactory.create('unknown',{})
def test_singleton_configuration():
    a,b=ConfigProvider(),ConfigProvider()
    a.set_discounts(['example'])
    assert a is b and b.get_discounts()==['example']
    a.set_discounts([])
def test_breakdown_only_positive_discounts():
    r=calc(order(), ('percent',{'percent':0}), ('fixed',{'amount':0,'threshold':0}))
    assert not r.applied_discounts

def test_breakdown_has_reason_and_order_and_delivery_amount():
    r = calc(
        order(price='3000', qty=3, delivery='500', last=NOW-timedelta(days=12), first=True),
        ('three_for_two', {'category': 'other'}),
        ('percent', {'percent': 10}),
        ('loyalty', {}),
        ('first_order', {}),
        ('fixed', {'amount': 50, 'threshold': 0}),
        ('free_delivery', {'threshold': 1000}),
    )
    assert [d.amount for d in r.applied_discounts] == [
        Decimal('3000.00'), Decimal('600.00'), Decimal('270.00'),
        Decimal('513.00'), Decimal('50.00'), Decimal('500.00')
    ]
    assert all(d.reason for d in r.applied_discounts)

def test_fixed_promo_discount_is_limited_to_goods_total():
    r = calc(order(price='100', promo='P'), ('promo', {'code': 'P', 'discount_type': 'fixed', 'amount': 500}))
    assert r.final_total == Decimal('0.00')
    assert r.applied_discounts[0].amount == Decimal('100.00')

def test_promo_code_is_case_sensitive():
    r = calc(order(promo='sale'), ('promo', {'code': 'SALE', 'discount_type': 'percent', 'amount': 15}))
    assert r.final_total == Decimal('1000.00') and not r.applied_discounts

def test_percent_above_100_rejected():
    with pytest.raises(ValueError):
        DiscountFactory.create('percent', {'percent': 101})

def test_multiple_quantity_items_are_counted_together():
    items = [
        CartItem(Product('a', 'Товар A', Decimal('50'), 'cat'), 2),
        CartItem(Product('b', 'Товар B', Decimal('100'), 'cat'), 1),
    ]
    r = calc(order(items=items), ('three_for_two', {'category': 'cat'}))
    assert r.final_total == Decimal('150.00')
    assert r.applied_discounts[0].amount == Decimal('50.00')

def test_loyalty_accepts_date_values():
    r = calc(order(last=NOW.date()-timedelta(days=30), created=NOW.date()), ('loyalty', {}))
    assert r.final_total == Decimal('950.00')

def test_promo_expiry_accepts_date_with_datetime_order():
    r = calc(order(promo='X', created=NOW), ('promo', {'code': 'X', 'discount_type': 'fixed', 'amount': 100, 'end_date': NOW.date()}))
    assert r.final_total == Decimal('900.00')
