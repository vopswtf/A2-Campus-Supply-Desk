"""Tests based on requirements in CR-01"""

from pathlib import Path
import tempfile
import unittest

from supplydesk.service import OrderService

class OrderExpressTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.json"
        self.service = OrderService(self.path)

    def test_regular_express(self):
        items = [{"product_id": "notebook", "quantity": 2}]
        quote = self.service.quote("regular", items, "express")
        self.assertEqual(quote["subtotal_cents"], 1000)
        self.assertEqual(quote["discount_cents"], 0)
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 2200)

    def test_student_express(self):
        items = [{"product_id": "hoodie", "quantity": 2}]
        quote = self.service.quote("student", items, "express")
        self.assertEqual(quote["subtotal_cents"], 8000)
        self.assertEqual(quote["discount_cents"], 800)
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 8400)

    def test_three_hoodies(self):
        items = [{"product_id": "hoodie", "quantity": 3}]
        standard = self.service.quote("regular", items, "delivery")
        express = self.service.quote("regular", items, "express")
        self.assertEqual(standard["total_cents"], 12000)
        self.assertEqual(express["total_cents"], 13200)
        self.assertEqual(express["delivery_cents"], 1200)


if __name__ == "__main__":
    unittest.main()
