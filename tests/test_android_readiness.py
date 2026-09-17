import json
import sqlite3
import unittest
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AndroidReadinessTests(unittest.TestCase):
    def _main_source(self):
        return (ROOT / "main.py").read_text(encoding="utf-8")

    def _language_dict(self):
        tree = ast.parse(self._main_source())
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "lang_dict":
                        return ast.literal_eval(node.value)
        self.fail("self.lang_dict assignment not found")

    def test_default_config_has_no_private_values(self):
        config = json.loads((ROOT / "config.json").read_text())

        self.assertEqual(config["email"], "")
        self.assertEqual(config["phone"], "")
        self.assertEqual(config["app_password"], "")
        self.assertEqual(config["backup_folder"], "backups")

    def test_upsert_keeps_locked_rate_on_existing_entry(self):
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE entries(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT UNIQUE,
                milk REAL,
                payment REAL,
                status TEXT DEFAULT 'unfilled',
                rate REAL DEFAULT 65.0
            )
            """
        )
        sql = """
            INSERT INTO entries(entry_date, milk, payment, rate, status)
            VALUES(?, ?, ?, ?, 'filled')
            ON CONFLICT(entry_date) DO UPDATE SET milk=excluded.milk, payment=excluded.payment, rate=excluded.rate, status='filled'
        """

        cur.execute(sql, ("2026-08-31", 1.0, 0.0, 60.0))
        cur.execute(sql, ("2026-08-31", 2.0, 10.0, 70.0))
        row = cur.execute("SELECT milk, payment, rate, status FROM entries").fetchone()

        self.assertEqual(row, (2.0, 10.0, 70.0, "filled"))

    def test_android_permissions_include_notifications(self):
        spec = (ROOT / "buildozer.spec").read_text()

        self.assertIn("source.exclude_dirs = tests,__pycache__", spec)
        self.assertIn("android.permissions = INTERNET,POST_NOTIFICATIONS", spec)
        self.assertIn("python3==3.11.9,hostpython3==3.11.9", spec)
        self.assertNotIn("kivymd", spec)
        self.assertNotIn("reportlab", spec)

    def test_reportlab_dependency_removed(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")

        self.assertNotIn("from reportlab", main)
        self.assertIn("def write_simple_pdf", main)

    def test_pdf_open_has_android_intent_fallback(self):
        main = self._main_source()

        self.assertIn("Intent.ACTION_VIEW", main)
        self.assertIn("application/pdf", main)
        self.assertIn("PDF Bill Ready", main)

    def test_language_dictionary_has_complete_hindi_and_gujarati(self):
        lang = self._language_dict()

        self.assertIn("Gujarati", lang)
        self.assertEqual(lang["Hindi"]["milk"], "दूध")
        self.assertEqual(lang["Hindi"]["rate"], "दर")
        self.assertEqual(lang["Hindi"]["notes_hint"], "इस तारीख के लिए नोट लिखें...")
        self.assertEqual(lang["Gujarati"]["milk"], "દૂધ")
        self.assertEqual(lang["Gujarati"]["rate"], "દર")
        self.assertEqual(lang["Gujarati"]["notes_hint"], "આ તારીખ માટે નોંધ લખો...")
        self.assertEqual(set(lang["English"]), set(lang["Hindi"]))
        self.assertEqual(set(lang["English"]), set(lang["Gujarati"]))

    def test_first_launch_and_settings_offer_all_languages(self):
        main = self._main_source()

        self.assertIn('"language": ""', (ROOT / "config.py").read_text(encoding="utf-8"))
        self.assertIn('values=("English", "Hindi", "Gujarati")', main)
        self.assertIn("open_language_selector", main)
        self.assertIn("Choose App Language", main)
        self.assertIn("ऐप की भाषा चुनें", main)
        self.assertIn("એપની ભાષા પસંદ કરો", main)

    def test_pdf_output_uses_selected_language_strings(self):
        main = self._main_source()

        self.assertIn('self.t("pdf_statement_title")', main)
        self.assertIn('self.t("pdf_month")', main)
        self.assertIn('self.t("pdf_owner")', main)
        self.assertIn('self.t("pdf_notes")', main)


if __name__ == "__main__":
    unittest.main()
