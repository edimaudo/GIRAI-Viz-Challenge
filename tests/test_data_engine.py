import unittest

from data_engine import (
    get_comparison,
    get_country_profile,
    get_explore,
    get_rankings,
)


class DataEngineTests(unittest.TestCase):
    def test_dataset_shape(self):
        data = get_explore()
        self.assertEqual(len(data["map"]), 138)
        self.assertEqual(len(data["regional"]), 7)

    def test_thematic_region_filter_uses_median(self):
        data = get_explore(view="thematic", metric="AI and human rights", region="Europe")
        self.assertTrue(data["map"])
        self.assertTrue(all(row["region"] == "Europe" for row in data["map"]))
        self.assertEqual(data["headline"]["countries"], len(data["map"]))

    def test_country_profile(self):
        profile = get_country_profile("CAN")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["summary"]["country"], "Canada")
        self.assertTrue(profile["themes"])
        scores = [row["ta_score"] for row in profile["themes"] if row["ta_score"] is not None]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_rankings_region_filter(self):
        rows = get_rankings(region="Europe")
        self.assertTrue(rows)
        self.assertTrue(all(row["region"] == "Europe" for row in rows))

    def test_rankings_country_filter(self):
        rows = get_rankings(region="North America", iso3="CAN")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["iso3"], "CAN")
        self.assertEqual(rows[0]["country"], "Canada")

    def test_two_region_comparison(self):
        result = get_comparison("regions", "Europe", "North America")
        self.assertEqual(len(result["rows"]), 7)
        self.assertEqual(result["first_label"], "Europe")
        self.assertEqual(result["second_label"], "North America")

    def test_two_country_comparison(self):
        result = get_comparison("countries", "CAN", "USA")
        self.assertEqual(len(result["rows"]), 7)
        self.assertEqual(result["first_label"], "Canada")
        self.assertEqual(result["second_label"], "United States")


if __name__ == "__main__":
    unittest.main()
