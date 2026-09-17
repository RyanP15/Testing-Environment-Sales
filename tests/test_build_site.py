"""Tests for src.build_site.

Structural checks on the generated site -- that every project gets a page,
that the figures land in the HTML, and that text from the CSVs is escaped
rather than injected raw.

Run with either:
    python3 -m unittest discover -s tests
    python3 -m pytest
"""
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import build_site  # noqa: E402
from src.loader import load_projects, load_transactions, load_units  # noqa: E402


class TestFormatters(unittest.TestCase):
    def test_money(self):
        self.assertEqual(build_site.money(1250000), "$1,250,000")

    def test_compact_money_millions(self):
        self.assertEqual(build_site.compact_money(25874000), "$25.9M")

    def test_compact_money_thousands(self):
        self.assertEqual(build_site.compact_money(412000), "$412K")

    def test_compact_money_small(self):
        self.assertEqual(build_site.compact_money(940), "$940")

    def test_pct(self):
        self.assertEqual(build_site.pct(43.75), "43.8%")

    def test_esc_escapes_markup(self):
        self.assertEqual(
            build_site.esc('<script>"x"</script>'),
            "&lt;script&gt;&quot;x&quot;&lt;/script&gt;",
        )


class TestTable(unittest.TestCase):
    COLUMNS = [("name", "Name", "l"), ("qty", "Qty", "r")]

    def test_empty_rows_render_a_placeholder(self):
        self.assertIn("No rows", build_site.table([], self.COLUMNS))

    def test_headers_and_values_present(self):
        out = build_site.table([{"name": "Studio", "qty": 4}], self.COLUMNS)
        self.assertIn("<th>Name</th>", out)
        self.assertIn("Studio", out)
        self.assertIn("4", out)

    def test_right_aligned_columns_get_the_num_class(self):
        out = build_site.table([{"name": "Studio", "qty": 4}], self.COLUMNS)
        self.assertIn('<th class="num">Qty</th>', out)
        self.assertIn('<td class="num">4</td>', out)


class TestBuild(unittest.TestCase):
    """Build the real site into a temp directory and inspect it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "site"
        build_site.build(cls.out)
        cls.projects = load_projects()
        cls.units = load_units()
        cls.transactions = load_transactions()
        cls.index = (cls.out / "index.html").read_text()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_index_and_assets_written(self):
        for name in ("index.html", "style.css", "app.js", ".nojekyll"):
            self.assertTrue((self.out / name).exists(), name)

    def test_every_project_gets_a_page(self):
        for project in self.projects:
            path = self.out / "project-{}.html".format(project["project_id"])
            self.assertTrue(path.exists(), project["project_id"])

    def test_index_links_every_project_page(self):
        for project in self.projects:
            self.assertIn(
                'href="project-{}.html"'.format(project["project_id"]),
                self.index,
                project["project_id"],
            )

    def test_index_names_every_project(self):
        for project in self.projects:
            self.assertIn(project["project_name"], self.index)

    def test_index_carries_the_synthetic_data_warning(self):
        self.assertIn("Synthetic practice data", self.index)

    def test_project_page_lists_its_own_suites_only(self):
        project = self.projects[0]
        pid = project["project_id"]
        html = (self.out / "project-{}.html".format(pid)).read_text()
        mine = [u for u in self.units if u["project_id"] == pid]
        theirs = [u for u in self.units if u["project_id"] != pid]
        for unit in mine:
            self.assertIn(">{}<".format(unit["suite"]), html, unit["unit_id"])
        # A suite number from another tower must not leak onto this page.
        foreign = {u["suite"] for u in theirs} - {u["suite"] for u in mine}
        for suite in sorted(foreign):
            self.assertNotIn(">{}<".format(suite), html, suite)

    def test_every_agent_appears_on_the_leaderboard(self):
        for txn in self.transactions:
            self.assertIn(txn["agent"], self.index, txn["txn_id"])

    def test_rebuild_is_clean(self):
        """Building twice must not leave files behind from the first pass."""
        stale = self.out / "project-GG-99.html"
        stale.write_text("stale")
        build_site.build(self.out)
        self.assertFalse(stale.exists())

    def test_no_unrendered_format_placeholders(self):
        """Catch a `{name}` that never got substituted.

        CSS and JS live in their own files, so a brace in the HTML output is
        always a bug. ("None" is *not* checked -- it is a real value in the
        incentive_package column, meaning no incentive was offered.)
        """
        for path in sorted(self.out.glob("*.html")):
            leftover = re.findall(r"\{[a-z_0-9:.]*\}", path.read_text())
            self.assertEqual(leftover, [], "{}: {}".format(path.name, leftover))


if __name__ == "__main__":
    unittest.main()
