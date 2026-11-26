import re
import unittest
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = REPO_ROOT / "_pages"
I18N_PATH = REPO_ROOT / "_data" / "i18n.yml"
ACTIVITY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "add-activity.yml"
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def load_front_matter(path: Path) -> dict:
    match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    if match is None:
        raise AssertionError(f"{path.name} has no front matter")
    return yaml.safe_load(match.group(1)) or {}


def load_pages() -> dict:
    return {path.name: load_front_matter(path) for path in sorted(PAGES_DIR.glob("*.md"))}


class PagePairTests(unittest.TestCase):
    def setUp(self):
        self.pages = load_pages()

    def test_every_ref_has_exactly_one_page_per_language(self):
        refs = {}
        for name, fm in self.pages.items():
            if "ref" in fm:
                refs.setdefault(fm["ref"], []).append((fm.get("lang"), name))
        self.assertEqual({"home", "research", "publications", "activities"}, set(refs))
        for ref, entries in refs.items():
            langs = sorted(lang for lang, _ in entries)
            self.assertEqual(["en", "ja"], langs, f"ref {ref}: {entries}")

    def test_permalinks_are_unique(self):
        permalinks = Counter(fm.get("permalink") for fm in self.pages.values())
        duplicates = [link for link, count in permalinks.items() if link and count > 1]
        self.assertEqual([], duplicates)

    def test_english_pages_live_under_en(self):
        for name, fm in self.pages.items():
            permalink = fm.get("permalink", "")
            if fm.get("lang") == "en":
                self.assertTrue(permalink.startswith("/en/"), name)
            if fm.get("lang") == "ja":
                self.assertFalse(permalink.startswith("/en/"), name)

    def test_nav_pages_have_language_and_order(self):
        for name, fm in self.pages.items():
            if fm.get("nav"):
                self.assertIn(fm.get("lang"), ("ja", "en"), name)
                self.assertNotEqual("home", fm.get("ref"), name)
                self.assertIsInstance(fm.get("nav_order"), int, name)

    def test_old_japanese_research_url_redirects(self):
        fm = self.pages["research-ja.md"]
        self.assertEqual("/research-ja/", fm["permalink"])
        self.assertEqual("/research/", fm["redirect"])
        self.assertNotIn("ref", fm)
        self.assertFalse(fm.get("nav", False))


class I18nTests(unittest.TestCase):
    def setUp(self):
        self.i18n = yaml.safe_load(I18N_PATH.read_text(encoding="utf-8"))

    def test_both_languages_define_the_same_keys(self):
        self.assertEqual(set(self.i18n["ja"]), set(self.i18n["en"]))
        self.assertEqual("/", self.i18n["ja"]["home_url"])
        self.assertEqual("/en/", self.i18n["en"]["home_url"])

    def test_every_workflow_activity_type_has_english_name(self):
        workflow = yaml.safe_load(ACTIVITY_WORKFLOW.read_text(encoding="utf-8"))
        on_block = workflow.get("on", workflow.get(True))
        options = on_block["workflow_dispatch"]["inputs"]["type"]["options"]
        missing = [option for option in options if option not in self.i18n["activity_types_en"]]
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
