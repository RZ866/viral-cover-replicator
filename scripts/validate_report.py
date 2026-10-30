#!/usr/bin/env python3
"""Validate a report with the bundled JSON Schema subset, without dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "shooting-report.schema.json"


class ValidationError(ValueError):
    pass


def _resolve(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValidationError(f"不支持外部 $ref：{ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def _is_type(value: Any, expected: str) -> bool:
    checks = {
        "null": value is None,
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }
    return checks.get(expected, False)


def validate_instance(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if "$ref" in schema:
        errors.extend(validate_instance(value, _resolve(root, schema["$ref"]), root, path))

    expected = schema.get("type")
    if expected is not None:
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(_is_type(value, item) for item in allowed):
            return errors + [f"{path}: 类型应为 {allowed}，实际为 {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: 必须等于 {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: 值 {value!r} 不在允许范围 {schema['enum']}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: 缺少必填字段 {key!r}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: 不允许未知字段 {key!r}")
        for key, child in value.items():
            if key in properties:
                errors.extend(validate_instance(child, properties[key], root, f"{path}.{key}"))

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: 至少需要 {schema['minItems']} 项")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: 最多允许 {schema['maxItems']} 项")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_instance(item, item_schema, root, f"{path}[{index}]"))

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: 字符串过短")
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            errors.append(f"{path}: 不符合格式 {pattern}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: 不能小于 {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: 不能大于 {schema['maximum']}")
    return errors


def validate_semantics(report: dict[str, Any]) -> list[str]:
    """Check cross-field rules that JSON Schema cannot express clearly."""
    errors: list[str] = []
    plans = report.get("original_shooting_plans", [])
    if [plan.get("id") for plan in plans] != ["A", "B", "C"]:
        errors.append("$.original_shooting_plans: 三套方案必须按 A、B、C 排列")
    for field in ("theme", "scenario", "composition", "lighting", "background"):
        values = [str(plan.get(field, "")).strip().casefold() for plan in plans]
        if len(values) == 3 and len(set(values)) != 3:
            errors.append(f"$.original_shooting_plans: 三套方案的 {field} 必须有实质差异")
    priorities = [item.get("priority") for item in (report.get("correction_actions") or [])]
    if len(priorities) != len(set(priorities)):
        errors.append("$.correction_actions: 纠偏优先级不得重复")
    for group_name in ("image_observations", "visual_strengths"):
        for index, claim in enumerate(report.get(group_name, [])):
            if claim.get("type") == "UNKNOWN" and claim.get("confidence") is not None:
                errors.append(f"$.{group_name}[{index}]: UNKNOWN 的 confidence 必须为 null")
    return errors


def load_and_validate(report_path: Path, schema_path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(str(exc)) from exc
    errors = validate_instance(report, schema, schema) + validate_semantics(report)
    if errors:
        raise ValidationError("报告校验失败：\n- " + "\n- ".join(errors))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="校验爆款封面复刻器报告 JSON")
    parser.add_argument("report", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    try:
        load_and_validate(args.report.resolve(), args.schema.resolve())
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"PASS: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
