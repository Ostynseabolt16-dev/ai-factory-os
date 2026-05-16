import unittest

from ai_factory.visuals.factory_map import (
    _best_signal_value,
    _ready_to_scale,
    collect_factory_map_data,
)


class FactoryMapTests(unittest.TestCase):
    def test_best_signal_value_falls_back_to_most_common(self):
        rows = [
            {"niche": "Flutter"},
            {"niche": "flutter"},
            {"niche": "Rust"},
        ]
        self.assertEqual(_best_signal_value(rows, "niche", "none yet"), "flutter")

    def test_ready_to_scale_prefers_orders(self):
        listings = [{"orders": "1"}, {"favorites": "5"}]
        self.assertEqual(_ready_to_scale(listings), "small cluster expansion")

    def test_collect_factory_map_data_has_expected_structure(self):
        data = collect_factory_map_data()
        self.assertIsInstance(data, dict)
        self.assertIn("rooms", data)
        self.assertIsInstance(data["rooms"], list)
        self.assertIn("pipeline", data)
        self.assertIsInstance(data["pipeline"], list)
        self.assertIn("signal_heatmap", data)
        self.assertIsInstance(data["signal_heatmap"], list)
        self.assertIn("summary", data)
        self.assertIsInstance(data["summary"], dict)
        self.assertIn("top_emotional_hook", data["summary"])


if __name__ == "__main__":
    unittest.main()
