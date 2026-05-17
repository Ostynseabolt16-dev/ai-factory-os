import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_factory.etsy import etsy_upload
from ai_factory.products import product_manager


class EtsyUploadQueueTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp())
        self.products_csv = self.tempdir / "products.csv"
        self.upload_log_csv = self.tempdir / "etsy_upload_log.csv"
        product_manager.PRODUCTS_CSV = self.products_csv
        etsy_upload.ETSY_UPLOAD_LOG_CSV = self.upload_log_csv
        self._create_products_csv()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _create_products_csv(self):
        rows = [
            {
                "id": "1",
                "batch_id": "1",
                "niche": "test niche",
                "filename": "design1.png",
                "status": "upload_ready",
                "created_at": "2026-05-16T00:00:00",
                "quality_score": "5",
                "trend_score": "0",
                "performance_rating": "",
                "platform": "etsy",
                "title": "Test Product",
                "tags": "tag1|tag2",
                "description": "A test product description.",
                "estimated_category": "home",
                "upload_date": "",
                "reviewed_at": "2026-05-16T00:00:00",
                "mockup_created_at": "2026-05-16T00:00:00",
                "listed_at": "",
                "sold_at": "",
                "last_updated_at": "2026-05-16T00:00:00",
                "pipeline_stage": "listing",
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
                "idea": "Test idea",
                "image_path": "designs/design1.png",
                "mockup_paths": "mockups/front.png|mockups/lifestyle.png",
            }
        ]
        with self.products_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=product_manager.CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

    def test_dry_run_queue_validation_does_not_mark_uploaded(self):
        queue_result = etsy_upload.queue_etsy_upload()
        self.assertEqual(queue_result["queued"], 1)
        self.assertEqual(queue_result["total_queue"], 1)

        report = etsy_upload.process_etsy_upload_queue(dry_run=True)
        self.assertEqual(report["validated"], 1)
        self.assertEqual(report["published"], 0)
        self.assertEqual(report["failed"], 0)

        rows = etsy_upload._read_upload_log()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "pending")
        self.assertIn("dry_run_validation", rows[0]["notes"])


if __name__ == "__main__":
    unittest.main()
