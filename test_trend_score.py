import csv
import shutil
import tempfile
import unittest
from pathlib import Path

import ai_factory.products.product_manager as product_manager
import ai_factory.intelligence.trend_score as trend_score


class TrendScoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp())
        product_manager.PRODUCTS_CSV = self.tempdir / "products.csv"
        trend_score.TREND_DATA_CSV = self.tempdir / "trend_data.csv"
        self._create_products_csv()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _create_products_csv(self):
        rows = [
            {
                "id": "1",
                "batch_id": "1",
                "niche": "surf culture",
                "filename": "design1.png",
                "status": "upload_ready",
                "created_at": "2026-05-16T00:00:00",
                "quality_score": "4",
                "trend_score": "0",
                "title_quality_score": "0",
                "tag_quality_score": "0",
                "listing_completeness_score": "0",
                "niche_confidence": "0",
                "performance_rating": "",
                "platform": "etsy",
                "title": "Surfer Vibes Poster",
                "tags": "surf|ocean|beach",
                "description": "A surfer poster for coastal lovers.",
                "estimated_category": "home decor",
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
                "idea": "surf art",
                "image_path": "designs/design1.png",
                "mockup_paths": "mockups/front.png|mockups/lifestyle.png",
            }
        ]
        with product_manager.PRODUCTS_CSV.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=product_manager.CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

    def test_import_trend_csv_and_generate_product_intelligence(self):
        trend_csv = self.tempdir / "trends.csv"
        with trend_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["keyword", "niche", "search_volume", "trend_velocity", "source"])
            writer.writeheader()
            writer.writerow(
                {
                    "keyword": "surf",
                    "niche": "surf culture",
                    "search_volume": "1400",
                    "trend_velocity": "50",
                    "source": "manual",
                }
            )

        result = trend_score.import_trend_csv(trend_csv)
        self.assertEqual(result["imported"], 1)

        product = product_manager.read_products()[0]
        trends = trend_score.load_trend_data()
        intelligence = trend_score.generate_product_intelligence(product, trends)

        self.assertGreater(int(intelligence["trend_score"]), 0)
        self.assertGreaterEqual(intelligence["title_quality_score"], 0)
        self.assertGreaterEqual(intelligence["tag_quality_score"], 0)
        self.assertGreaterEqual(intelligence["listing_completeness_score"], 0)
        self.assertGreaterEqual(intelligence["niche_confidence"], 0)

    def test_score_all_products_updates_product_row(self):
        trend_csv = self.tempdir / "trends.csv"
        with trend_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["keyword", "niche", "search_volume", "trend_velocity", "source"])
            writer.writeheader()
            writer.writerow(
                {
                    "keyword": "surf",
                    "niche": "surf culture",
                    "search_volume": "1400",
                    "trend_velocity": "50",
                    "source": "manual",
                }
            )
        trend_score.import_trend_csv(trend_csv)
        result = trend_score.score_all_products(trend_score.load_trend_data())
        self.assertEqual(result["updated_products"], 1)

        product = product_manager.read_products()[0]
        self.assertNotEqual(product.get("trend_score"), "0")
        self.assertNotEqual(product.get("title_quality_score"), "0")
        self.assertNotEqual(product.get("tag_quality_score"), "0")
        self.assertNotEqual(product.get("listing_completeness_score"), "0")
        self.assertNotEqual(product.get("niche_confidence"), "0")


if __name__ == "__main__":
    unittest.main()
