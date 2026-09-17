"""Tests for src.metrics.

Run with either:
    python3 -m unittest discover -s tests
    python3 -m pytest
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import metrics  # noqa: E402
from src.loader import load_projects, load_transactions, load_units  # noqa: E402


class TestPricePerSqft(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(metrics.price_per_sqft(800000, 640), 1250.0)

    def test_rounds_to_cents(self):
        self.assertEqual(metrics.price_per_sqft(1000000, 777), 1287.0)

    def test_rejects_zero_sqft(self):
        with self.assertRaises(ValueError):
            metrics.price_per_sqft(500000, 0)


class TestDiscount(unittest.TestCase):
    def test_sold_at_list_is_zero(self):
        self.assertEqual(metrics.discount_pct(900000, 900000), 0.0)

    def test_two_percent_off(self):
        self.assertEqual(metrics.discount_pct(1000000, 980000), 2.0)

    def test_over_list_is_negative(self):
        self.assertEqual(metrics.discount_pct(1000000, 1010000), -1.0)


class TestAbsorption(unittest.TestCase):
    def test_empty_inventory(self):
        self.assertEqual(metrics.absorption_rate([]), 0.0)

    def test_counts_firm_and_closed(self):
        units = [
            {"status": "firm"},
            {"status": "closed"},
            {"status": "available"},
            {"status": "held"},
        ]
        self.assertEqual(metrics.absorption_rate(units), 50.0)


class TestDaysOnMarket(unittest.TestCase):
    def test_span(self):
        self.assertEqual(metrics.days_on_market("2025-01-01", "2025-01-31"), 30)

    def test_same_day(self):
        self.assertEqual(metrics.days_on_market("2025-06-02", "2025-06-02"), 0)


class TestDataIntegrity(unittest.TestCase):
    """Guard rails on the CSVs in data/."""

    @classmethod
    def setUpClass(cls):
        cls.projects = load_projects()
        cls.units = load_units()
        cls.transactions = load_transactions()

    def test_files_are_not_empty(self):
        self.assertTrue(self.projects)
        self.assertTrue(self.units)
        self.assertTrue(self.transactions)

    def test_every_unit_belongs_to_a_project(self):
        known = {p["project_id"] for p in self.projects}
        for unit in self.units:
            self.assertIn(unit["project_id"], known, unit["unit_id"])

    def test_every_transaction_points_at_a_real_unit(self):
        known = {u["unit_id"] for u in self.units}
        for txn in self.transactions:
            self.assertIn(txn["unit_id"], known, txn["txn_id"])

    def test_unit_ids_are_unique(self):
        ids = [u["unit_id"] for u in self.units]
        self.assertEqual(len(ids), len(set(ids)))

    def test_only_sold_units_have_transactions(self):
        unit_status = {u["unit_id"]: u["status"] for u in self.units}
        for txn in self.transactions:
            self.assertIn(unit_status[txn["unit_id"]], ("firm", "closed"), txn["txn_id"])

    def test_prices_are_positive(self):
        for unit in self.units:
            self.assertGreater(unit["list_price"], 0, unit["unit_id"])
            self.assertGreater(unit["interior_sqft"], 0, unit["unit_id"])

    def test_sales_happen_after_launch(self):
        launches = {p["project_id"]: p["launch_date"] for p in self.projects}
        for txn in self.transactions:
            days = metrics.days_on_market(launches[txn["project_id"]], txn["sale_date"])
            self.assertGreaterEqual(days, 0, txn["txn_id"])

    def test_project_rollup_covers_every_project(self):
        rows = metrics.project_rollup(self.projects, self.units, self.transactions)
        self.assertEqual(len(rows), len(self.projects))


if __name__ == "__main__":
    unittest.main()
