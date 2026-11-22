"""
Unit tests for Google Ads Multi-Agent System.
Validates input parsing, security boundaries, and cross-industry copy specs.
"""

import unittest
import datetime
from pathlib import Path

from scripts.audit_accounts import (
    validate_date_str,
    generate_sample_data,
    load_json,
    CONFIG_DIR,
    REPORTS_DIR,
    export_csv,
    export_markdown_summary,
)
from scripts.orchestrate_team import (
    generate_rsa_copy_for_business,
    generate_staged_action_plan,
    sanitize_text,
)


class TestSecurityValidation(unittest.TestCase):
    def test_valid_date_format(self):
        self.assertEqual(validate_date_str("2026-11-22"), "2026-11-22")

    def test_invalid_date_format_rejected(self):
        with self.assertRaises(Exception):
            validate_date_str("2026/11/22")

    def test_path_traversal_date_rejected(self):
        with self.assertRaises(Exception):
            validate_date_str("/../../etc/passwd")

        with self.assertRaises(Exception):
            validate_date_str("..\\..\\windows")

    def test_calendar_date_logic(self):
        # Invalid day in month
        with self.assertRaises(Exception):
            validate_date_str("2026-02-31")

    def test_path_escape_rejected_in_csv_export(self):
        results = []
        evil_path = REPORTS_DIR / ".." / "escaped.csv"
        with self.assertRaises(ValueError):
            export_csv(results, evil_path)


class TestMultiBusinessLogic(unittest.TestCase):
    def setUp(self):
        self.accounts_config = load_json(CONFIG_DIR / "accounts.json")
        self.thresholds = load_json(CONFIG_DIR / "thresholds.json")

    def test_sample_dataset_generation(self):
        results = generate_sample_data(self.accounts_config, self.thresholds)
        self.assertEqual(len(results), len(self.accounts_config["accounts"]))
        for r in results:
            self.assertIn("business_type", r)
            self.assertIn("primary_metric", r)
            self.assertIn("status", r)
            self.assertIn("yesterday_spend", r)

    def test_rsa_character_length_limits(self):
        business_types = [
            "ecommerce", "b2b_saas", "local_service", 
            "mobile_app", "lead_gen", "healthcare", "info_product"
        ]
        for b_type in business_types:
            pack = generate_rsa_copy_for_business(b_type, f"TestBrand - {b_type}")
            for headline in pack["headlines"]:
                self.assertLessEqual(
                    len(headline), 30,
                    f"Headline '{headline}' exceeded 30 characters in {b_type} ({len(headline)} chars)"
                )
            for desc in pack["descriptions"]:
                self.assertLessEqual(
                    len(desc), 90,
                    f"Description '{desc}' exceeded 90 characters in {b_type} ({len(desc)} chars)"
                )

    def test_text_sanitizer(self):
        raw = "Brand [Name]\nWith Newlines\rand [brackets]"
        cleaned = sanitize_text(raw)
        self.assertNotIn("\n", cleaned)
        self.assertNotIn("\r", cleaned)
        self.assertNotIn("[", cleaned)
        self.assertNotIn("]", cleaned)


if __name__ == "__main__":
    unittest.main()
