import unittest

from shipping import shipping_cents


class ShippingTest(unittest.TestCase):
    def test_member_over_threshold_ships_free(self):
        self.assertEqual(shipping_cents(6000, True, "US"), 0)

    def test_small_order_pays_domestic_rate(self):
        self.assertEqual(shipping_cents(1200, False, "US"), 799)

    def test_international_flat_rate(self):
        self.assertEqual(shipping_cents(6000, True, "DE"), 2500)


if __name__ == "__main__":
    unittest.main()
