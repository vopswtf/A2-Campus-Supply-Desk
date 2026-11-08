from pathlib import Path
import tempfile
import unittest

from supplydesk.service import OrderService

class OrderSafetyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.json"
        self.service = OrderService(self.path)

    # Normal
    # Test that checks for incrementing order IDs when multiple orders are placed.
    # Expected ID1 = ORD-0001, ID2= ORD-0002, pass
    # Result PASS
    def test_order_id_increment(self):
        order1 = self.service.place_order("regular", [{"product_id": "pen-pack", "quantity": 2}])
        order2 = self.service.place_order("student", [{"product_id": "mug", "quantity": 1}])

        order_1_id = int(order1["order_id"].split("-")[1])
        order_2_id = int(order2["order_id"].split("-")[1])

        self.assertEqual(order_1_id + 1, order_2_id)

    # Normal
    # Test that checks that stock depletes for a product by the orders quantity when an order is placed
    # Expected stock_after = stock_before - order_quantity (2), pass
    # Result PASS
    def test_order_stock_depletion(self):
        product_id = "pen-pack"
        before = self.service.catalog()
        self.service.place_order("regular", [{"product_id":product_id, "quantity": 2}])
        after = self.service.catalog()

        # find old stock and new stock
        for product in before:
            if product["product_id"] == product_id:
                stock_before = product["stock"]

        for product in after:
            if product["product_id"] == product_id:
                stock_after = product["stock"]

        self.assertEqual(stock_after, stock_before - 2)

    # Boundry
    # A student receives a 10% discount when the subtotal is at least 5,000 cents ($50.00) (Taken from specification). This test checks for that discount exactly
    # Expected discount_cents > 0 since total is 5000 cents, pass
    # Result FAIL (service uses > 5000 instead of >= 5000)
    def test_student_discount_applied(self):
        items = [{"product_id": "bag", "quantity": 2}] # bag is 2500
        quote = self.service.quote("student", items)
        self.assertGreater(quote["discount_cents"], 0)

    # Boundry
    # Order is created with no products in the list of items, should fail
    # Expected quote errors and passes
    # Result PASS
    def test_empty_order_items(self):
        with self.assertRaises(ValueError):
            self.service.quote("regular", [])

    # Invalid
    # Order is created with an invalid customer type (not student or regular), should fail
    # Expected quote errors and passes
    # Result PASS
    def test_fake_customer_type(self):
        with self.assertRaises(ValueError):
            self.service.quote("REAL CUSTOMER HERE!", [{"product_id": "bag", "quantity": 2}])

    # Invalid
    # Quantity given as a string is not valid when calling the service directly (from specification)
    # Expected ValueError, pass
    # Result PASS
    def test_string_quantity(self):
        with self.assertRaises(ValueError):
            self.service.quote("regular", [{"product_id": "notebook", "quantity": "2"}])

    # Preserve
    # Test that checks that the quote and the placed order match exactly, pass
    # Expected quote and order match, pass
    # Result PASS
    def test_quote_matches_placed_order(self):
        items = [ {"product_id": "hoodie", "quantity": 2}, {"product_id": "mug", "quantity": 1} ]
        quote = self.service.quote("student", items, "delivery")
        order = self.service.place_order("student", items, "delivery")

        self.assertEqual(order['customer_type'], quote['customer_type'])
        self.assertEqual(order['fulfillment'], quote['fulfillment'])
        self.assertEqual(order['items'], quote['items'])
        self.assertEqual(order['subtotal_cents'], quote['subtotal_cents'])
        self.assertEqual(order['discount_cents'], quote['discount_cents'])
        self.assertEqual(order['delivery_cents'], quote['delivery_cents'])
        self.assertEqual(order['total_cents'], quote['total_cents'])

    # Preserve
    # Emulates 2 orders, first cancelled and second placed. Then "restarts" the service as if it was a fresh CLI instance.
    # Expected order history is same as before, pass
    # Result PASS
    def test_history_after_reopen(self):
        first = self.service.place_order("regular", [{"product_id": "notebook", "quantity": 1}])
        self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        self.service.cancel_order(first["order_id"])

        # refreshing the service, basically as if the app restarted
        reopened = OrderService(self.path)
        orders = reopened.list_orders()

        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]["order_id"], "ORD-0001")
        self.assertEqual(orders[0]["status"], "cancelled")
        self.assertEqual(orders[1]["order_id"], "ORD-0002")
        self.assertEqual(orders[1]["status"], "placed")
    
if __name__ == "__main__":
    unittest.main()
