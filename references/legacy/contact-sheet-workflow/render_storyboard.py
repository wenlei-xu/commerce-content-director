#!/usr/bin/env python3
"""Render a legible, deterministic video-conditioning storyboard from a JSON manifest."""

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


PAGE = (3840, 2160)
MARGIN = 48
GAP = 30
TITLE_H = 88


def font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    if bold:
        # Keep a CJK-capable face first; Arial Bold renders Chinese as tofu boxes.
        candidates.insert(1, "/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def line_wrap(draw, text, font_obj, width):
    """Wrap both whitespace-delimited and CJK text without losing characters."""
    lines, line = [], ""
    for char in str(text):
        candidate = line + char
        if line and draw.textlength(candidate, font=font_obj) > width:
            lines.append(line.rstrip())
            line = char.lstrip()
        else:
            line = candidate
    if line or not lines:
        lines.append(line.rstrip())
    return lines


def add_field(draw, x, y, label, value, width, body_font, line_height):
    prefix = f"{label}: "
    text = f"{prefix}{value}"
    for line in line_wrap(draw, text, body_font, width):
        draw.text((x, y), line, fill="#1d1d1f", font=body_font)
        y += line_height
    return y + 6


def open_panel_image(path, size):
    image = Image.open(path).convert("RGB")
    # Preserve the supplied 9:16 keyframe instead of cropping it for the sheet.
    framed = Image.new("RGB", size, "#e9edf1")
    contained = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    x = (size[0] - contained.width) // 2
    y = (size[1] - contained.height) // 2
    framed.paste(contained, (x, y))
    return framed


def render(manifest, output):
    panels = manifest["panels"]
    if not 1 <= len(panels) <= 6:
        raise ValueError("A storyboard page supports one to six panels; use numbered continuation pages without changing shot boundaries.")
    rows = 1 if len(panels) <= 3 else 2
    cols = len(panels) if rows == 1 else math.ceil(len(panels) / rows)
    page = Image.new("RGB", PAGE, "#f7f7f7")
    draw = ImageDraw.Draw(page)
    title = manifest.get("title", "Video-conditioning storyboard")
    duration = manifest.get("duration", "")
    draw.text((MARGIN, 18), f"{title}  |  {duration}", fill="#111111", font=font(42, bold=True))

    usable_w = PAGE[0] - 2 * MARGIN - (cols - 1) * GAP
    usable_h = PAGE[1] - TITLE_H - MARGIN - (rows - 1) * GAP
    panel_w = usable_w // cols
    panel_h = usable_h // rows
    header_h = 66 if rows == 1 else 52
    image_h = int(panel_h * (0.64 if rows == 1 else 0.52))
    body_size = 27 if rows == 1 else 20
    body_font = font(body_size)
    line_height = body_size + 7

    for index, panel in enumerate(panels):
        row, col = divmod(index, cols)
        x = MARGIN + col * (panel_w + GAP)
        y = TITLE_H + row * (panel_h + GAP)
        draw.rounded_rectangle((x, y, x + panel_w, y + panel_h), radius=8, fill="white", outline="#a7a7a7", width=2)
        draw.rectangle((x, y, x + panel_w, y + header_h), fill="#f0f2f4")
        draw.text((x + 16, y + 10), f"{panel['id']}  {panel['time']}", fill="#111111", font=font(31 if rows == 1 else 24, bold=True))

        image_xy = (x + 12, y + header_h + 12)
        image_size = (panel_w - 24, image_h)
        page.paste(open_panel_image(panel["image"], image_size), image_xy)
        meta_y = image_xy[1] + image_h + 14
        fields = [
            ("Shot Type", panel["shot_type"]),
            ("Camera", panel["camera"]),
            ("Action", panel["action"]),
            ("Emotion", panel["emotion"]),
            ("Dialogue / Subtitle", panel.get("dialogue", "None")),
            ("Video Control", panel["video_control"]),
            ("Transition to Next", panel.get("transition_to_next", panel.get("transition", "Natural ending"))),
        ]
        for label, value in fields:
            meta_y = add_field(draw, x + 16, meta_y, label, value, panel_w - 32, body_font, line_height)
        if meta_y > y + panel_h - 10:
            raise ValueError(f"Metadata for {panel['id']} exceeds its panel; shorten wording or place fewer beats on this continuation page.")

    page.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, help="JSON file containing title, duration, and one to six dynamically segmented panels")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    render(manifest, args.out)


if __name__ == "__main__":
    main()
