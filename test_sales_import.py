import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_factory.analytics.revenue_tracker import record_sale_from_order_text
from ai_factory.listings import listing_tracker
from ai_factory.products import product_manager


class SalesImportTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp())
        self.products_csv = self.tempdir / "products.csv"
        self.listings_csv = self.tempdir / "listings.csv"
        product_manager.PRODUCTS_CSV = self.products_csv
        listing_tracker.LISTINGS_CSV = self.listings_csv
        self._write_products()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _write_products(self):
        with self.products_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=product_manager.CSV_COLUMNS)
            writer.writeheader()
            writer.writerow(
                {
                    "id": "42",
                    "batch_id": "batch-1",
                    "niche": "cars",
                    "filename": "corvette-c5.png",
                    "status": "uploaded",
                    "created_at": "2026-06-02T00:00:00",
                    "quality_score": "5",
                    "trend_score": "0",
                    "confidence_score": "0",
                    "saturation_score": "0",
                    "opportunity_score": "0",
                    "upload_priority": "medium",
                    "title_quality_score": "0",
                    "tag_quality_score": "0",
                    "listing_completeness_score": "0",
                    "niche_confidence": "0",
                    "performance_rating": "",
                    "platform": "etsy",
                    "title": "Corvette C5 Illustrated Car Tee | Classic Sports Car Graphic T-Shirt",
                    "tags": "car|tee|graphic",
                    "description": "A classic car graphic tee.",
                    "image_prompt": "",
                    "generation_hash": "",
                    "estimated_category": "clothing",
                    "upload_date": "",
                    "reviewed_at": "",
                    "mockup_created_at": "",
                    "listed_at": "",
                    "sold_at": "",
                    "last_updated_at": "2026-06-02T00:00:00",
                    "pipeline_stage": "published",
                    "sales_count": "0",
                    "revenue": "0",
                    "actual_revenue": "0",
                    "actual_sales_count": "0",
                    "first_sale_date": "",
                    "last_sale_date": "",
                    "total_orders": "0",
                    "platform_fees_estimate": "0",
                    "estimated_profit": "0",
                    "notes": "",
                    "parent_product_id": "",
                    "product_type": "original",
                    "idea": "Corvette car tee",
                    "image_path": "designs/corvette-c5.png",
                    "mockup_paths": "",
                }
            )
            writer.writerow(
                {
                    "id": "43",
                    "batch_id": "batch-2",
                    "niche": "cars",
                    "filename": "corvette-c6.png",
                    "status": "uploaded",
                    "created_at": "2026-06-02T00:00:00",
                    "quality_score": "5",
                    "trend_score": "0",
                    "confidence_score": "0",
                    "saturation_score": "0",
                    "opportunity_score": "0",
                    "upload_priority": "medium",
                    "title_quality_score": "0",
                    "tag_quality_score": "0",
                    "listing_completeness_score": "0",
                    "niche_confidence": "0",
                    "performance_rating": "",
                    "platform": "etsy",
                    "title": "Corvette C6 Illustrated Car Tee | Classic Sports Car Graphic T-Shirt",
                    "tags": "car|tee|graphic",
                    "description": "A classic C6 car graphic tee.",
                    "image_prompt": "",
                    "generation_hash": "",
                    "estimated_category": "clothing",
                    "upload_date": "",
                    "reviewed_at": "",
                    "mockup_created_at": "",
                    "listed_at": "",
                    "sold_at": "",
                    "last_updated_at": "2026-06-02T00:00:00",
                    "pipeline_stage": "published",
                    "sales_count": "0",
                    "revenue": "0",
                    "actual_revenue": "0",
                    "actual_sales_count": "0",
                    "first_sale_date": "",
                    "last_sale_date": "",
                    "total_orders": "0",
                    "platform_fees_estimate": "0",
                    "estimated_profit": "0",
                    "notes": "",
                    "parent_product_id": "",
                    "product_type": "original",
                    "idea": "Corvette C6 car tee",
                    "image_path": "designs/corvette-c6.png",
                    "mockup_paths": "",
                }
            )

    def test_record_sale_from_order_text_marks_matching_product_sold(self):
        order_text = """
Seth

[#4075631366](https://www.etsy.com/your/orders/sold?ref=seller-platform-mcnav&order_id=4075631366)$27.21

Corvette C5 Illustrated Car Tee | Classic Sports Car Graphic T-Shirt
- Quantity1
- SKU12710191827980057200
- ColorsAsh
- SizesM
"""

        result = record_sale_from_order_text(order_text)

        self.assertEqual(result["order_id"], "4075631366")
        self.assertEqual(result["revenue"], 27.21)
        self.assertEqual(result["product_id"], "42")
        self.assertTrue(result["recorded"])

        updated = product_manager.read_products(path=self.products_csv)[0]
        self.assertEqual(updated["status"], "sold")
        self.assertEqual(updated["total_orders"], "1")
        self.assertEqual(updated["actual_revenue"], "27.21")

    def test_record_sale_from_order_text_matches_c6_title_without_listing_row(self):
        order_text = """
David Ghirardi

[#4075631367](https://www.etsy.com/your/orders/sold?ref=seller-platform-mcnav&order_id=4075631367)$31.50

Corvette C6 Illustrated Car Tee | Classic Sports Car Graphic T-Shirt
- Quantity1
- SKU12710191827980057201
- ColorsAsh
- SizesM
"""

        result = record_sale_from_order_text(order_text)

        self.assertTrue(result["recorded"])
        self.assertEqual(result["product_id"], "43")
        self.assertEqual(result["revenue"], 31.5)
        self.assertEqual(result["listing_id"], "")

        updated = product_manager.read_products(path=self.products_csv)[1]
        self.assertEqual(updated["status"], "sold")
        self.assertEqual(updated["total_orders"], "1")
        self.assertEqual(updated["actual_revenue"], "31.50")


if __name__ == "__main__":
    unittest.main()
