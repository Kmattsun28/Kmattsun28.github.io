import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "bin"))

from add_site_entry import add_entry


class AddSiteEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)

    def write_yaml(self, name: str, content: str) -> Path:
        path = self.temp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_appends_publication_without_rewriting_existing_content(self):
        original = (
            "# Publications list\n\n"
            "- title: \"Existing paper\"\n"
            "  authors: \"Author A\"\n"
            "  venue: \"Venue\"\n"
            "  year: 2024\n"
            "  url: \"https://example.com/old\"\n"
        )
        path = self.write_yaml("publications.yml", original)

        result = add_entry(
            "publication",
            {
                "title": "新しい論文",
                "authors": "松本亘平, Author B",
                "venue": "Example Conference",
                "year": "2026",
                "url": "https://example.com/new",
            },
            path,
        )

        self.assertEqual(result["year"], 2026)
        updated = path.read_text(encoding="utf-8")
        self.assertTrue(updated.startswith(original))
        self.assertIn("title: 新しい論文", updated)
        self.assertIn("url: https://example.com/new", updated)

    def test_appends_activity_with_unicode_period_date(self):
        path = self.write_yaml("activities.yml", "[]\n")

        result = add_entry(
            "activity",
            {
                "title": "研究展示",
                "date": "2026-08-01〜2026-08-03",
                "type": "展示",
                "venue": "名古屋大学",
                "description": "説明",
                "url": "",
            },
            path,
        )

        self.assertEqual(result["date"], "2026-08-01〜2026-08-03")
        self.assertIn("研究展示", path.read_text(encoding="utf-8"))

    def test_rejects_invalid_year_and_url(self):
        path = self.write_yaml("publications.yml", "[]\n")
        with self.assertRaises(ValueError):
            add_entry(
                "publication",
                {"title": "P", "authors": "A", "venue": "V", "year": "26", "url": ""},
                path,
            )
        with self.assertRaises(ValueError):
            add_entry(
                "publication",
                {
                    "title": "P",
                    "authors": "A",
                    "venue": "V",
                    "year": "2026",
                    "url": "example.com",
                },
                path,
            )

    def test_rejects_multiline_publication_title(self):
        path = self.write_yaml("publications.yml", "[]\n")
        with self.assertRaisesRegex(ValueError, "title must be a single line"):
            add_entry(
                "publication",
                {
                    "title": "Author Name\tActual title",
                    "authors": "Author Name",
                    "venue": "Venue",
                    "year": "2026",
                    "url": "",
                },
                path,
            )

    def test_rejects_duplicate_publication_and_activity(self):
        publication_path = self.write_yaml(
            "publications.yml",
            "- title: Existing\n  authors: A\n  venue: V\n  year: 2026\n  url: ''\n",
        )
        with self.assertRaises(ValueError):
            add_entry(
                "publication",
                {
                    "title": " Existing ",
                    "authors": "B",
                    "venue": "W",
                    "year": "2026",
                    "url": "",
                },
                publication_path,
            )

        activity_path = self.write_yaml(
            "activities.yml",
            "- title: Event\n  date: 2026-08-01\n  type: 展示\n  venue: ''\n  description: ''\n  url: ''\n",
        )
        with self.assertRaises(ValueError):
            add_entry(
                "activity",
                {
                    "title": "event",
                    "date": "2026-08-01",
                    "type": "発表",
                    "venue": "",
                    "description": "",
                    "url": "",
                },
                activity_path,
            )


if __name__ == "__main__":
    unittest.main()
