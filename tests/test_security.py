from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from create_example import build
from generate_report import _safe_image_uri, render


class SecurityTests(unittest.TestCase):
    def test_user_html_is_escaped(self):
        data = build()
        data["project_info"]["name"] = '<img src=x onerror="alert(1)">'
        html = render(data, ROOT / "examples")
        self.assertIn("&lt;img", html)
        self.assertNotIn("onerror=\"alert", html)

    def test_parent_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                _safe_image_uri("../outside.png", Path(directory))

    def test_remote_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                _safe_image_uri("https://example.com/a.png", Path(directory))

    def test_template_has_no_remote_requests(self):
        template = (ROOT / "assets" / "report-template.html").read_text(encoding="utf-8")
        self.assertNotIn("http://", template)
        self.assertNotIn("https://", template)
        self.assertIn("connect-src 'none'", template)


if __name__ == "__main__":
    unittest.main()
