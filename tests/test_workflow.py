from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from detect_mode import detect_mode
from project_record import _append, _write_new


class WorkflowTests(unittest.TestCase):
    def test_natural_language_routes(self):
        cases = {
            "拆解这张封面": "A", "教我拍出这张照片": "B", "对比我的实拍照片": "C",
            "给我三套差异化原创方案": "D", "执行完整工作流": "E",
        }
        for text, expected in cases.items():
            images = 2 if expected == "C" else 1
            self.assertEqual(expected, detect_mode(text, images)["mode"])

    def test_unspecified_single_image_uses_default_chain(self):
        self.assertEqual("A+B+D", detect_mode("看看这张图", 1)["mode"])

    def test_record_limits_rounds_and_issues(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            _write_new(path, "test", "reference.png")
            issues = ["主体偏小"]
            for number in range(1, 4):
                _append(path, f"r{number}.png", issues, ["移动手机"], "主体比例更接近", "检查光线")
            with self.assertRaises(ValueError):
                _append(path, "r4.png", issues, [], "无", "停止")

    def test_skill_documents_eight_photography_cases(self):
        text = (ROOT / "references" / "photography-analysis.md").read_text(encoding="utf-8")
        expected = ["自然光", "暗调", "俯拍", "复杂道具", "AI", "模糊", "机位", "三套"]
        for keyword in expected:
            self.assertIn(keyword, text)

    def test_cli_refuses_existing_output_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            output.write_text("keep", encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_report.py"), str(ROOT / "examples" / "sample-report.json"), "--output", str(output)], capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("keep", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
