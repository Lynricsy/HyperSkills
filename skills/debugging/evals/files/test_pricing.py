import unittest

from catalog import load_catalog
from pricing import line_total
from report import discounted_skus


class PricingTest(unittest.TestCase):
    def test_line_total_applies_percentage_discount(self):
        catalog = load_catalog()
        self.assertAlmostEqual(line_total(catalog["SKU-1"], 2), 8.10)

    def test_undiscounted_sku_is_not_reported_as_discounted(self):
        self.assertEqual(discounted_skus(load_catalog()), ["SKU-1", "SKU-3"])


if __name__ == "__main__":
    unittest.main()
