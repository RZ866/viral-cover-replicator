#!/usr/bin/env python3
"""Create the bundled synthetic fixture and transparent example report data."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def claim(kind: str, statement: str, evidence: str | None, confidence: float | None) -> dict:
    return {"type": kind, "statement": statement, "evidence": evidence, "confidence": confidence}


def box(x: float, y: float, width: float, height: float) -> dict:
    return {"x": x, "y": y, "width": width, "height": height}


def diagram(subject: dict, camera: dict, light: dict, reflector: dict, props: list[dict], angle: float) -> dict:
    return {"subject": subject, "camera": camera, "light": light, "reflector": reflector, "props": props,
            "camera_height": 48, "subject_height": 16, "camera_angle": angle}


def plan(pid: str, name: str, theme: str, intensity: str, scenario: str, goal: str,
         background: str, composition: str, lighting: str, camera: str, props: list[str], diag: dict) -> dict:
    return {
        "id": pid, "name": name, "theme": theme, "intensity": intensity, "scenario": scenario,
        "visual_goal": goal,
        "borrowed_principles": ["保持单一主视觉焦点", "使用大面积柔光表现商品材质"],
        "differences": [f"重新设计为{scenario}", f"改用{composition}", f"采用{lighting}"],
        "props": props, "background": background, "composition": composition, "lighting": lighting,
        "camera": camera,
        "parameters": ["先使用手机 2× 或等效中焦段试拍", "对焦商品正面标签", "曝光从 -0.3 EV 附近试起"],
        "steps": ["清理背景并确定主体位置", "按示意图放置道具与光源", "固定手机后试拍并只调整一个变量"],
        "substitutes": ["白卡纸代替反光板", "纱帘代替专业柔光布"],
        "failure_causes": ["道具抢走主体注意力", "光源太近导致标签反光"],
        "acceptance": ["缩略图中能立即识别商品", "标签无高光遮挡", "场景与参考图形成实质差异"],
        "diagram": diag,
    }


def make_image(path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter

    canvas = Image.new("RGB", (900, 1200), "#e9dfcf")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 760, 900, 1200), fill="#b88459")
    draw.ellipse((505, 820, 790, 910), fill="#6f4c35")
    draw.rectangle((535, 400, 760, 875), fill="#f5efe5", outline="#684f3e", width=5)
    draw.rectangle((555, 555, 740, 720), fill="#d8b276")
    draw.text((605, 620), "CANDLE", fill="#3d3129")
    draw.ellipse((555, 360, 740, 455), fill="#f8e2a6", outline="#684f3e", width=5)
    draw.rectangle((145, 835, 420, 895), fill="#e7e0d7", outline="#5b5248", width=3)
    draw.rectangle((170, 785, 445, 845), fill="#f5f1ea", outline="#5b5248", width=3)
    draw.line((70, 200, 430, 1000), fill="#f7f0dc", width=80)
    canvas = canvas.filter(ImageFilter.GaussianBlur(0.35))
    canvas.save(path, format="PNG")


def build() -> dict:
    subject = box(.57, .34, .24, .40)
    props = [{"name": "两本浅色书", "purpose": "形成低矮前景层次", "position": box(.15, .68, .30, .10)}]
    base_diagram = diagram(subject, box(.10, .78, .15, .10), box(.04, .18, .18, .30), box(.84, .40, .10, .28), props, 25)
    steps = []
    titles = ["选择位置", "布置背景", "放置商品", "摆放主道具", "加入辅助道具", "确定主光", "柔化光线", "固定机位", "检查构图", "试拍微调"]
    for index, title in enumerate(titles, 1):
        steps.append({"order": index, "title": title, "action": f"完成第 {index} 步：{title}",
                      "method": "参照示意图操作，每次只移动一个元素", "purpose": "保持调整结果可判断",
                      "expected": "主体清晰、层次稳定", "check": "缩小预览仍能先看到商品",
                      "common_error": "同时改动多个变量，无法判断改善来源"})
    return {
        "project_info": {"name": "暖调香薰蜡烛封面练习", "version": "1.0.0", "mode": "E", "created_at": "2026-10-31T10:00:00+08:00", "status": "waiting_for_shoot"},
        "source_images": [{"id": "synthetic_reference", "role": "reference", "path": "synthetic-cover.png", "caption": "项目自制合成测试图，不代表平台真实爆款"}],
        "image_observations": [
            claim("OBSERVATION", "浅色圆柱形商品位于画面右侧，约占画面宽度四分之一。", "synthetic_reference：商品轮廓与画面边界", .98),
            claim("OBSERVATION", "左下方有两本横放的浅色书作为前景道具。", "synthetic_reference：左下区域", .99),
            claim("INFERENCE", "左上到右下的亮带可作为左侧柔光的视觉提示。", "亮带方向与商品左侧更亮", .72),
        ],
        "composition": {"summary": "主体右置，左侧保留呼吸空间，低矮书本平衡视觉重心。", "claims": [claim("OBSERVATION", "主体中心接近右侧三分线。", "主体包围框中心 x≈0.69", .94)]},
        "camera_position": {"summary": "建议从略高于商品的斜侧平视起步。", "angle_range": "20°–35°俯角（建议起始范围）", "distance_range": "约 60–100 cm，按手机焦段调整", "starting_zoom": "2× 或等效中焦段起试", "focus": "商品标签中央", "exposure": "从 -0.3 EV 附近试拍，避免白色包装过曝", "tripod": True, "timer": True, "claims": [claim("RECOMMENDATION", "避免使用超广角近距离拍摄，以减少圆柱商品变形。", "基于圆柱包装的透视控制", .86)]},
        "lighting": {"summary": "画面适合左侧大面积柔光，右侧白卡弱补光。", "main_direction": "left", "softness": "soft", "shadow_direction": "right", "fill": "右侧白卡纸弱补光", "low_cost_setup": ["窗户置于商品左前方", "窗边挂白纱帘柔化直射光", "商品右侧竖起白卡纸"], "claims": [claim("INFERENCE", "参考效果可能对应左前侧柔光。", "商品左侧亮、右侧明暗过渡缓慢", .74)]},
        "scene_and_props": {"background": "暖米色无明显纹理背景", "surface": "中暖棕色木质或仿木桌面", "subject": subject, "props": props, "required_props": ["真实商品", "暖色桌面或背景纸"], "optional_props": ["两本浅色旧书"], "substitutes": ["牛皮纸代替暖米色背景", "硬纸板包木纹贴纸代替桌板"]},
        "colors_and_editing": {"summary": "暖米色、浅棕与奶油黄构成低饱和暖调。", "claims": [claim("OBSERVATION", "画面以暖米色和棕色为主。", "背景、桌面与包装颜色", .96), claim("RECOMMENDATION", "修图先轻降高光，再少量增加暖色，避免改变商品真实颜色。", "保护包装细节与商品真实性", .88)]},
        "visual_strengths": [claim("ANALYSIS" if False else "INFERENCE", "清晰的明暗块和大面积留白有利于缩略图识别。", "主体轮廓与背景反差", .78)],
        "shooting_preparation": {"equipment": ["手机", "手机支架或三脚架", "2 秒定时拍摄"], "required_props": ["真实商品", "桌面", "暖米色背景"], "optional_props": ["两本浅色书", "白色泡沫板"], "low_cost_substitutes": ["白纸代替反光板", "纱帘代替柔光布"], "checklist": ["商品正面清洁且标签朝向镜头", "背景边缘不入镜", "高光不遮挡文字", "缩略图能识别商品", "保存一张未修图原片"]},
        "replication_steps": steps,
        "scene_diagrams": base_diagram,
        "comparison_results": None,
        "correction_actions": None,
        "original_shooting_plans": [
            plan("A", "窗边晨间低成本方案", "晨间整理", "轻度", "窗边早餐桌", "形成轻松、可执行的生活气息", "浅灰亚麻布", "左侧主体配右下杯碟的三分构图", "右侧窗户漫射顺侧光", "手机略高 20°，从左前方拍摄", ["浅色杯碟", "亚麻布"], diagram(box(.18,.36,.24,.38), box(.72,.76,.15,.10), box(.78,.12,.15,.28), box(.04,.40,.10,.25), [{"name":"杯碟","purpose":"生活线索","position":box(.55,.62,.20,.15)}], 20)),
            plan("B", "夜间书桌叙事方案", "夜读陪伴", "中度", "夜间书桌", "让暖光与阅读动作形成新的叙事", "深棕木桌与墨绿色背景", "主体偏左、台灯形成对角线引导", "左后方暖台灯加右前白卡补光", "手机平视偏右 15°", ["旧书", "暖色台灯", "眼镜"], diagram(box(.20,.42,.22,.36), box(.72,.50,.15,.10), box(.05,.12,.18,.25), box(.75,.70,.12,.22), [{"name":"眼镜","purpose":"阅读线索","position":box(.50,.68,.20,.10)}], 10)),
            plan("C", "极简几何重构方案", "材质实验", "深度", "纯色几何影棚", "只保留柔光材质原理，建立独立视觉表达", "低饱和蓝灰无缝纸", "中心偏下对称构图，使用圆形纸台", "顶部偏后大柔光制造轮廓渐变", "手机正面平视，等效中焦段", ["圆形纸台", "一张蓝灰背景纸"], diagram(box(.39,.42,.22,.38), box(.42,.82,.15,.10), box(.40,.06,.20,.16), box(.08,.38,.10,.28), [{"name":"圆台","purpose":"几何基座","position":box(.32,.72,.36,.12)}], 5)),
        ],
        "originality_review": None,
        "limitations": ["这是对自制合成测试图的视觉分析，不代表真实平台表现。", "单张图片不能还原真实相机、焦段、距离、光源功率或后期历史。", "所有距离、角度和倍率都是可验证的起始建议。", "平台原创审核结果无法保证。"]
    }


def main() -> int:
    EXAMPLES.mkdir(exist_ok=True)
    make_image(EXAMPLES / "synthetic-cover.png")
    (EXAMPLES / "sample-report.json").write_text(json.dumps(build(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(EXAMPLES / "sample-report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
