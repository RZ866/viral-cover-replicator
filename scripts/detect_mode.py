#!/usr/bin/env python3
"""Small deterministic helper for routing the five documented workflows."""

from __future__ import annotations

import argparse
import json


def detect_mode(text: str, image_count: int = 1) -> dict[str, object]:
    value = text.casefold()
    if any(word in value for word in ("完整工作流", "全流程", "从拆解到原创")):
        mode = "E"
    elif any(word in value for word in ("原创成片", "原创差异", "原创审核")) and image_count >= 2:
        mode = "E"
    elif any(word in value for word in ("对比", "纠偏", "纠正", "下一轮")) and image_count >= 2:
        mode = "C"
    elif any(word in value for word in ("原创", "差异化", "三套方案", "重新设计")):
        mode = "D"
    elif any(word in value for word in ("教我拍", "还原", "复刻", "实拍教程")):
        mode = "B"
    elif any(word in value for word in ("拆解", "分析", "布光", "构图", "机位")):
        mode = "A"
    else:
        mode = "A+B+D"
    return {"mode": mode, "image_count": image_count, "needs_pause": mode in {"C", "E"} and image_count < 2}


def main() -> int:
    parser = argparse.ArgumentParser(description="识别爆款封面复刻器工作模式")
    parser.add_argument("text")
    parser.add_argument("--images", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(detect_mode(args.text, args.images), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
