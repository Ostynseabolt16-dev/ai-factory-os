import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_factory.generation.structured_generation import (
    score_product_concept,
    validate_generated_product,
    rank_generated_products,
)
from ai_factory.products import product_manager


class StructuredGenerationTests(unittest.TestCase):
    def test_validate_generated_product_accepts_valid_object(self):
        product = {
            "idea": "Cute nurse anxiety tee",
            "niche": "nurse humor",
            "title": "Cozy Nurse Anxiety Relief Graphic Tee",
            "description": "A positive nurse gift shirt celebrating mental health with cute illustration style. Perfect for nurses who want cozy, supportive humor.",
            "tags": ["nurse gift", "anxiety tee", "mental health shirt", "medical humor", "RN gift"],
            "image_prompt": "cute nurse cartoon holding a heart with pastel colors, clean vector style, t-shirt design",
            "trend_score": 78,
            "confidence_score": 82,
        }
        validated = validate_generated_product(product)
        self.assertEqual(validated["title"], product["title"])
        self.assertEqual(validated["trend_score"], 78)
        self.assertEqual(validated["confidence_score"], 82)

    def test_validate_generated_product_rejects_missing_fields(self):
        product = {
            "idea": "",
            "niche": "",
            "title": "Too short",
            "description": "Short.",
            "tags": [],
            "image_prompt": "",
            "trend_score": 110,
            "confidence_score": -5,
        }
        with self.assertRaises(ValueError) as context:
            validate_generated_product(product)
        message = str(context.exception)
        self.assertIn("Idea is required", message)
        self.assertIn("Niche is required", message)
        self.assertIn("Tags count must be between", message)
        self.assertIn("Trend score must be an integer between 0 and 100", message)

    def test_rank_generated_products_orders_by_score(self):
        candidates = [
            {
                "idea": "A",
                "niche": "niche one",
                "title": "Title A is strong and descriptive",
                "description": "A long and valuable description that is full enough to pass validation and includes useful product detail." * 2,
                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
                "image_prompt": "simple prompt",
                "trend_score": 90,
                "confidence_score": 90,
            },
            {
                "idea": "B",
                "niche": "niche two",
                "title": "Title B",
                "description": "Another description that is sufficiently long." * 4,
                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
                "image_prompt": "brief prompt",
                "trend_score": 10,
                "confidence_score": 5,
            },
        ]
        ranked = rank_generated_products(candidates, top_n=2)
        self.assertEqual(ranked[0]["idea"], "A")
        self.assertEqual(ranked[1]["idea"], "B")
        self.assertGreater(ranked[0]["validation_score"], ranked[1]["validation_score"])


class ProductManagerSanitizationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp())
        self.products_csv = self.tempdir / "products.csv"
        product_manager.PRODUCTS_CSV = self.products_csv

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_sanitize_products_csv_removes_invalid_rows(self):
        rows = [
            {
                "id": "1",
                "batch_id": "",
                "niche": "niche",
                "filename": "image1.png",
                "status": "draft",
                "created_at": "2026-01-01T00:00:00",
                "quality_score": "0",
                "trend_score": "50",
                "confidence_score": "50",
                "saturation_score": "0",
                "opportunity_score": "0",
                "upload_priority": "low",
                "title_quality_score": "0",
                "tag_quality_score": "0",
                "listing_completeness_score": "0",
                "niche_confidence": "0",
                "performance_rating": "",
                "platform": "etsy",
                "title": "Valid title for test",
                "tags": "tag1|tag2|tag3|tag4|tag5",
                "description": "This is a valid description that is long enough to pass the sanity check and preserve the row.",
                "image_prompt": "valid prompt",
                "generation_hash": "abc123",
                "estimated_category": "",
                "upload_date": "",
                "reviewed_at": "",
                "mockup_created_at": "",
                "listed_at": "",
                "sold_at": "",
                "last_updated_at": "2026-01-01T00:00:00",
                "pipeline_stage": "ideation",
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
                "idea": "Valid idea",
                "image_path": "designs/image1.png",
                "mockup_paths": "",
            },
            {
                "id": "2",
                "batch_id": "",
                "niche": "",
                "filename": "image2.png",
                "status": "draft",
                "created_at": "",
                "quality_score": "0",
                "trend_score": "0",
                "confidence_score": "0",
                "saturation_score": "0",
                "opportunity_score": "0",
                "upload_priority": "low",
                "title_quality_score": "0",
                "tag_quality_score": "0",
                "listing_completeness_score": "0",
                "niche_confidence": "0",
                "performance_rating": "",
                "platform": "etsy",
                "title": "",
                "tags": "",
                "description": "",
                "image_prompt": "",
                "generation_hash": "",
                "estimated_category": "",
                "upload_date": "",
                "reviewed_at": "",
                "mockup_created_at": "",
                "listed_at": "",
                "sold_at": "",
                "last_updated_at": "",
                "pipeline_stage": "ideation",
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
                "idea": "",
                "image_path": "",
                "mockup_paths": "",
            },
        ]
        with self.products_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=product_manager.CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        result = product_manager.sanitize_products_csv()
        self.assertEqual(result["kept"], 1)
        self.assertEqual(result["removed"], 1)
        remaining = product_manager.read_products(self.products_csv)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["id"], "1")


if __name__ == "__main__":
    unittest.main()
