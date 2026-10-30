#!/usr/bin/env python3
"""Create and append bounded correction rounds to a local project record."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _write_new(path: Path, project: str, reference: str) -> None:
    if path.exists():
        raise FileExistsError(f"拒绝覆盖现有记录：{path}")
    payload = {
        "schema_version": "1.0.0",
        "project": project,
        "reference_image": reference,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rounds": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append(path: Path, image: str, issues: list[str], adjustments: list[str], improvement: str, next_step: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rounds = payload.get("rounds")
    if not isinstance(rounds, list):
        raise ValueError("记录文件 rounds 字段非法")
    if len(rounds) >= 3:
        raise ValueError("最多记录三轮纠偏；请重新评估参考图和拍摄方案")
    if len(issues) > 3:
        raise ValueError("每轮最多记录三个主要问题")
    rounds.append({
        "round": len(rounds) + 1,
        "image": image,
        "issues": issues,
        "adjustments": adjustments,
        "improvement": improvement,
        "next_step": next_step,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="管理爆款封面复刻器本地项目记录")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("record", type=Path)
    init.add_argument("--project", required=True)
    init.add_argument("--reference", required=True)
    add = sub.add_parser("add-round")
    add.add_argument("record", type=Path)
    add.add_argument("--image", required=True)
    add.add_argument("--issue", action="append", default=[])
    add.add_argument("--adjustment", action="append", default=[])
    add.add_argument("--improvement", required=True)
    add.add_argument("--next", required=True, dest="next_step")
    args = parser.parse_args()
    try:
        if args.command == "init":
            _write_new(args.record.resolve(), args.project, args.reference)
        else:
            _append(args.record.resolve(), args.image, args.issue, args.adjustment, args.improvement, args.next_step)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"PASS: {args.record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
