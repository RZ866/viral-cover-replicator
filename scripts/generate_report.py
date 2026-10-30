#!/usr/bin/env python3
"""Render a validated report as a single offline HTML file."""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any

from validate_report import ValidationError, load_and_validate

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "report-template.html"
MAX_IMAGE_BYTES = 12 * 1024 * 1024
SIGNATURES = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".webp": (b"RIFF",),
}
TYPE_LABELS = {"OBSERVATION": "可直接观察", "INFERENCE": "合理推测", "RECOMMENDATION": "建议参数", "UNKNOWN": "未知"}


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def list_html(items: list[Any] | None) -> str:
    if not items:
        return '<div class="empty">未获取到数据</div>'
    return '<ul class="list">' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def claims_html(claims: list[dict[str, Any]] | None) -> str:
    if not claims:
        return '<div class="empty">未获取到可核验结论</div>'
    blocks = []
    for claim in claims:
        kind = claim["type"]
        evidence = f'<div class="evidence">依据：{esc(claim.get("evidence"))}</div>' if claim.get("evidence") else ""
        confidence = "" if claim.get("confidence") is None else f" · 置信度 {claim['confidence']:.0%}"
        blocks.append(f'<div class="claim {kind}"><span class="badge">{TYPE_LABELS[kind]}</span>{esc(claim["statement"])}{esc(confidence)}{evidence}</div>')
    return "".join(blocks)


def _safe_image_uri(raw_path: str | None, base: Path) -> str | None:
    if not raw_path:
        return None
    unresolved = base / raw_path
    if unresolved.is_symlink():
        raise ValueError(f"图片不允许使用符号链接：{raw_path}")
    candidate = unresolved.resolve()
    base_resolved = base.resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(f"图片必须位于报告 JSON 目录内：{raw_path}") from exc
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"图片不存在或不允许符号链接：{raw_path}")
    suffix = candidate.suffix.lower()
    if suffix not in SIGNATURES:
        raise ValueError(f"不支持的图片格式：{raw_path}")
    data = candidate.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"图片超过 12 MiB：{raw_path}")
    if not any(data.startswith(signature) for signature in SIGNATURES[suffix]):
        raise ValueError(f"图片签名与扩展名不一致：{raw_path}")
    if suffix == ".webp" and data[8:12] != b"WEBP":
        raise ValueError(f"WebP 文件签名无效：{raw_path}")
    mime = mimetypes.types_map.get(suffix, "image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _box(box: dict[str, float], width: int = 640, height: int = 420) -> tuple[float, float, float, float]:
    return (box["x"] * width, box["y"] * height, box["width"] * width, box["height"] * height)


def top_svg(data: dict[str, Any], title: str = "俯视布景图") -> str:
    width, height = 640, 420
    def rect(box: dict[str, float], color: str, label: str) -> str:
        x, y, w, h = _box(box, width, height)
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="10" fill="{color}" stroke="#594b40"/><text x="{x+w/2:.1f}" y="{y+h/2:.1f}" text-anchor="middle" dominant-baseline="middle">{esc(label)}</text>'
    body = rect(data["subject"], "#d9a77d", "商品") + rect(data["camera"], "#b6c8d7", "手机") + rect(data["light"], "#ffe49b", "主光")
    if data.get("reflector"):
        body += rect(data["reflector"], "#f4f1e8", "反光板")
    for item in data.get("props", []):
        body += rect(item["position"], "#c8d3bd", item["name"][:8])
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}"><defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#9b6545"/></marker></defs><rect x="4" y="4" width="632" height="412" rx="18" fill="#f7f3ec" stroke="#b7aa98"/><text x="24" y="30" font-weight="700">{esc(title)} · 推荐布局</text>{body}<line x1="{data["camera"]["x"]*width:.1f}" y1="{data["camera"]["y"]*height:.1f}" x2="{(data["subject"]["x"]+data["subject"]["width"]/2)*width:.1f}" y2="{(data["subject"]["y"]+data["subject"]["height"]/2)*height:.1f}" stroke="#9b6545" stroke-width="3" marker-end="url(#arr)"/></svg>'


def side_svg(data: dict[str, Any]) -> str:
    angle = data["camera_angle"]
    cam_y = 330 - min(data["camera_height"], 180) * 1.4
    subj_y = 330 - min(data["subject_height"], 120) * 1.4
    return f'<svg viewBox="0 0 640 420" role="img" aria-label="侧视机位图"><defs><marker id="sidearr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#9b6545"/></marker></defs><rect x="4" y="4" width="632" height="412" rx="18" fill="#f7f3ec" stroke="#b7aa98"/><text x="24" y="30" font-weight="700">侧视机位图 · 建议角度 {angle:.0f}°</text><line x1="40" y1="330" x2="600" y2="330" stroke="#7d6f61" stroke-width="5"/><rect x="430" y="{subj_y:.1f}" width="90" height="{330-subj_y:.1f}" rx="8" fill="#d9a77d" stroke="#594b40"/><text x="475" y="310" text-anchor="middle">商品</text><rect x="90" y="{cam_y:.1f}" width="70" height="42" rx="8" fill="#b6c8d7" stroke="#594b40"/><text x="125" y="{cam_y+25:.1f}" text-anchor="middle">手机</text><line x1="160" y1="{cam_y+20:.1f}" x2="460" y2="{subj_y+20:.1f}" stroke="#9b6545" stroke-width="3" marker-end="url(#sidearr)"/><path d="M510 72 L430 165 L590 165 Z" fill="#ffe49b" opacity=".65"/><text x="510" y="62" text-anchor="middle">主光</text></svg>'


def light_svg(data: dict[str, Any], lighting: dict[str, Any]) -> str:
    direction = esc(lighting["main_direction"])
    shadow = esc(lighting["shadow_direction"])
    return f'<svg viewBox="0 0 640 320" role="img" aria-label="光线方向图"><defs><marker id="lightarr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#d79b2e"/></marker><marker id="fillarr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6c8da3"/></marker></defs><rect x="4" y="4" width="632" height="312" rx="18" fill="#f7f3ec" stroke="#b7aa98"/><text x="24" y="30" font-weight="700">光线图 · 主光 {direction} / 阴影 {shadow}</text><circle cx="320" cy="175" r="55" fill="#d9a77d" stroke="#594b40"/><text x="320" y="180" text-anchor="middle">商品</text><rect x="60" y="90" width="100" height="130" rx="12" fill="#ffe49b" stroke="#b88a2d"/><text x="110" y="160" text-anchor="middle">主光</text><line x1="160" y1="155" x2="260" y2="170" stroke="#d79b2e" stroke-width="8" marker-end="url(#lightarr)"/><rect x="500" y="105" width="70" height="100" rx="8" fill="#eef2f4" stroke="#6c8da3"/><text x="535" y="160" text-anchor="middle">反光板</text><line x1="500" y1="165" x2="380" y2="175" stroke="#6c8da3" stroke-width="5" stroke-dasharray="8 6" marker-end="url(#fillarr)"/></svg>'


def section(number: int, title: str, body: str, extra: str = "") -> str:
    return f'<section id="s{number:02d}" class="section {extra}"><div class="section-no">PART {number:02d}</div><h2>{esc(title)}</h2>{body}</section>'


def plan_html(plan: dict[str, Any]) -> str:
    cards = f'<div class="grid"><div class="card"><h3>主题与场景</h3><p>{esc(plan["theme"])}</p><p>{esc(plan["scenario"])}</p><p><span class="pill">{esc(plan["intensity"])}创新</span></p></div><div class="card"><h3>视觉目标</h3><p>{esc(plan["visual_goal"])}</p></div><div class="card"><h3>借鉴原理</h3>{list_html(plan["borrowed_principles"])}</div><div class="card"><h3>主要区别</h3>{list_html(plan["differences"])}</div></div>'
    details = f'<h3>布景、构图与光线</h3><div class="grid"><div class="card"><b>背景</b><p>{esc(plan["background"])}</p><b>道具</b>{list_html(plan["props"])}</div><div class="card"><b>构图</b><p>{esc(plan["composition"])}</p><b>光线</b><p>{esc(plan["lighting"])}</p><b>机位</b><p>{esc(plan["camera"])}</p></div></div><h3>参数与执行</h3>{list_html(plan["parameters"])}{list_html(plan["steps"])}<h3>低成本替代</h3>{list_html(plan["substitutes"])}<h3>失败原因与验收</h3><div class="grid"><div class="card">{list_html(plan["failure_causes"])}</div><div class="card">{list_html(plan["acceptance"])}</div></div><div class="diagram">{top_svg(plan["diagram"], plan["name"] + "布景图")}</div>'
    return cards + details


def render(report: dict[str, Any], base: Path) -> str:
    info = report["project_info"]
    images = []
    for item in report["source_images"]:
        uri = _safe_image_uri(item.get("path"), base)
        image = f'<img class="image" src="{uri}" alt="{esc(item["caption"])}">' if uri else '<div class="placeholder">图片未嵌入；结构示例或路径为空</div>'
        images.append(f'<div class="card">{image}<p>{esc(item["caption"])}</p><span class="pill">{esc(item["role"])}</span></div>')

    comp = report["composition"]
    camera = report["camera_position"]
    lighting = report["lighting"]
    scene = report["scene_and_props"]
    colors = report["colors_and_editing"]
    prep = report["shooting_preparation"]
    diagrams = report["scene_diagrams"]
    steps = "".join(f'<div class="step"><h3>{esc(s["title"])}</h3><p><b>动作：</b>{esc(s["action"])}</p><p><b>方法：</b>{esc(s["method"])}</p><p><b>目的：</b>{esc(s["purpose"])}</p><p><b>预期：</b>{esc(s["expected"])}</p><p><b>检查：</b>{esc(s["check"])}</p><p><b>常见错误：</b>{esc(s["common_error"])}</p></div>' for s in report["replication_steps"])
    corrections = report.get("correction_actions")
    correction_html = '<div class="empty">本阶段尚未进行；等待用户上传实拍图。</div>' if not corrections else "".join(f'<div class="card"><h3>优先级 {c["priority"]}</h3><div class="comparison"><div><b>观察差异</b>{esc(c["difference"])}</div><div><b>可能原因</b>{esc(c["possible_cause"])}</div><div><b>调整动作</b>{esc(c["action"])}</div><div><b>验证方法</b>{esc(c["verification"])}</div></div></div>' for c in corrections)
    originality = report.get("originality_review")
    originality_html = '<div class="empty">本阶段尚未进行；等待用户上传原创成片。</div>' if not originality else f'<h3>{esc(originality["conclusion"])}</h3>{claims_html(originality["evidence"])}{list_html(originality["improvements"])}'
    plans = report["original_shooting_plans"]

    sections = [
        f'<section id="s01" class="hero"><div class="eyebrow">VIRAL COVER REPLICATOR · V1.0</div><h1>爆款封面复刻器<br>拍摄指导报告</h1><p>{esc(info["name"])} · 模式 {esc(info["mode"])} · 状态 {esc(info["status"])}</p><p>复刻用于掌握摄影方法，原创重构才是最终目标。所有机位与参数均为建议起始值，不代表原图真实拍摄历史。</p></section>',
        section(2, "参考图片展示", '<div class="grid">' + "".join(images) + "</div>"),
        section(3, "摄影风格总结", claims_html(report["image_observations"])),
        section(4, "构图分析", f'<p>{esc(comp["summary"])}</p>{claims_html(comp["claims"])}'),
        section(5, "拍摄机位分析", f'<p>{esc(camera["summary"])}</p><div class="grid"><div class="card">角度：{esc(camera["angle_range"])}<br>距离：{esc(camera["distance_range"])}<br>起始倍率：{esc(camera["starting_zoom"])}</div><div class="card">对焦：{esc(camera["focus"])}<br>曝光：{esc(camera["exposure"])}<br>三脚架：{"建议" if camera["tripod"] else "可选"}</div></div>{claims_html(camera["claims"])}'),
        section(6, "光线分析", f'<p>{esc(lighting["summary"])}</p>{claims_html(lighting["claims"])}<h3>低成本实现</h3>{list_html(lighting["low_cost_setup"])}'),
        section(7, "背景与道具拆解", f'<div class="grid"><div class="card"><h3>背景</h3><p>{esc(scene["background"])}</p><p>{esc(scene["surface"])}</p></div><div class="card"><h3>替代材料</h3>{list_html(scene["substitutes"])}</div></div><h3>道具</h3>{list_html([p["name"] + "：" + p["purpose"] for p in scene["props"]])}'),
        section(8, "色彩与后期建议", f'<p>{esc(colors["summary"])}</p>{claims_html(colors["claims"])}'),
        section(9, "拍摄准备清单", f'<div class="grid"><div class="card"><h3>设备</h3>{list_html(prep["equipment"])}</div><div class="card"><h3>必备道具</h3>{list_html(prep["required_props"])}</div><div class="card"><h3>可选道具</h3>{list_html(prep["optional_props"])}</div><div class="card"><h3>低成本替代</h3>{list_html(prep["low_cost_substitutes"])}</div></div>'),
        section(10, "实拍复刻教程", f'<div class="steps">{steps}</div>'),
        section(11, "布景及布光示意图", f'<p class="muted">以下为根据结构化分析动态生成的推荐布局，不是原图真实现场的确定还原。</p><div class="diagram">{top_svg(diagrams)}</div><div class="diagram">{side_svg(diagrams)}</div><div class="diagram">{light_svg(diagrams, lighting)}</div>'),
        section(12, "实拍纠偏结果", correction_html),
        section(13, "差异化方案 A", plan_html(plans[0]), "plan"),
        section(14, "差异化方案 B", plan_html(plans[1]), "plan"),
        section(15, "差异化方案 C", plan_html(plans[2]), "plan"),
        section(16, "原创成片诊断", originality_html),
        section(17, "最终执行检查清单", list_html(prep["checklist"])),
        section(18, "分析依据与限制说明", f'{claims_html(report["visual_strengths"])}<h3>限制</h3>{list_html(report["limitations"])}'),
    ]
    nav_titles = ["报告封面", "参考图片", "摄影风格", "构图", "机位", "光线", "背景道具", "色彩后期", "准备清单", "复刻教程", "布景布光", "纠偏", "方案 A", "方案 B", "方案 C", "原创诊断", "检查清单", "依据限制"]
    nav = "".join(f'<a href="#s{i:02d}">{i}. {esc(title)}</a>' for i, title in enumerate(nav_titles, 1))
    template = TEMPLATE.read_text(encoding="utf-8")
    return template.replace("{{TITLE}}", "爆款封面复刻器 · 拍摄指导报告").replace("{{NAV}}", nav).replace("{{CONTENT}}", "".join(sections))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成爆款封面复刻器离线 HTML 报告")
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的输出 HTML")
    args = parser.parse_args()
    source = args.report.resolve()
    output = args.output.resolve()
    if output == source:
        print("拒绝覆盖输入 JSON", file=sys.stderr)
        return 1
    if output.exists() and not args.force:
        print("输出文件已存在；如确认覆盖，请添加 --force", file=sys.stderr)
        return 1
    try:
        report = load_and_validate(source)
        document = render(report, source.parent)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
    except (ValidationError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"PASS: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
