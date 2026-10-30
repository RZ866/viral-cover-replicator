from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from create_example import build
from generate_report import render, top_svg


class ReportTests(unittest.TestCase):
    def test_report_has_18_sections_and_offline_assets(self):
        html = render(build(), ROOT / "examples")
        for number in range(1, 19):
            self.assertIn(f'id="s{number:02d}"', html)
        self.assertIn("爆款封面复刻器", html)
        self.assertIn("data:image/png;base64,", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("<script", html.casefold())
        self.assertIn("@media print", html)
        self.assertIn("viewBox=", html)

    def test_dynamic_svg_changes_with_layout(self):
        first = build()["scene_diagrams"]
        second = build()["scene_diagrams"]
        second["subject"]["x"] = .10
        self.assertNotEqual(top_svg(first), top_svg(second))

    def test_empty_optional_stages_are_explained(self):
        html = render(build(), ROOT / "examples")
        self.assertIn("等待用户上传实拍图", html)
        self.assertIn("等待用户上传原创成片", html)


if __name__ == "__main__":
    unittest.main()
