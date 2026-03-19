from __future__ import annotations

from uuid import uuid4

_PRODUCTS = [
    {'id': 101, 'name': '企业联名礼盒', 'price': 199.00, 'cover_url': 'https://example.com/p1.png'},
    {'id': 102, 'name': '办公补给礼包', 'price': 89.00, 'cover_url': 'https://example.com/p2.png'},
]
_ORDERS: list[dict] = []


class MallService:
    def list_products(self) -> list[dict]:
        return _PRODUCTS

    def get_product(self, product_id: int) -> dict | None:
        for item in _PRODUCTS:
            if item['id'] == product_id:
                return item
        return None

    def add_cart_item(self, user_id: int, sku_id: int, quantity: int) -> dict:
        return {'user_id': user_id, 'sku_id': sku_id, 'quantity': quantity, 'added': True}

    def create_order(self, user_id: int, items: list[dict], source_type: str) -> dict:
        amount = sum(item.get('quantity', 1) * 99 for item in items)
        order = {
            'id': len(_ORDERS) + 1,
            'order_no': f'ORD{uuid4().hex[:16].upper()}',
            'user_id': user_id,
            'status': 'pending',
            'pay_status': 'unpaid',
            'pay_amount': float(amount),
            'source_type': source_type,
        }
        _ORDERS.append(order)
        return order

    def list_orders(self, user_id: int | None = None) -> list[dict]:
        if user_id is None:
            return _ORDERS
        return [item for item in _ORDERS if item['user_id'] == user_id]


service = MallService()
