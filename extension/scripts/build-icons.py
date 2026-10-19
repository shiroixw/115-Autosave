#!/usr/bin/env python3
"""从 design/icon.svg 生成扩展所需的全部 PNG 图标。

Chrome Web Store 对 128×128 图标的规定（见 extension/store-assets/README.md）：
  · 实际图标 96×96，四周各留 16px 透明内边距，总尺寸 128×128；
  · 必须是 PNG；
  · 需在浅色、深色背景下均正常显示。

因此 128 尺寸不是简单缩放，而是「96×96 图形 + 16px 透明画布」合成。
其余尺寸（16/32/48）是工具栏图标，按原尺寸满版渲染，不补内边距。
若同级存在 website/public，则一并生成该站点的 favicon（32/128，满版）。

用法：
    python scripts/build-icons.py              # 生成并覆盖仓库中的 PNG
    python scripts/build-icons.py --browser /path/to/chrome

依赖：本机 Chrome/Edge（无头模式栅格化 SVG，自带抗锯齿与透明通道）+ Pillow。
不引入任何前端依赖。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "design" / "icon.svg"
SOURCE_PNG = ROOT / "design" / "icon-source-1024.png"
ICON_DIR = ROOT / "public" / "icon"
WEBSITE_PUBLIC = ROOT.parent / "website" / "public"

# Chrome Web Store 规范：128 画布内实际图标 96×96，四周各 16px 透明
STORE_CANVAS = 128
STORE_ART = 96
STORE_PADDING = (STORE_CANVAS - STORE_ART) // 2
SOURCE_SCALE = 8  # design/icon-source-1024.png = 128 规范的 8 倍图

CHROME_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
)


@dataclass(frozen=True)
class Target:
    """一个渲染目标：画布尺寸 + 图形在画布中的位置与边长。"""

    name: str
    canvas: int
    art: int
    offset: int
    out: Path


def find_browser() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("找不到 Chrome/Edge，无法栅格化 SVG。可用 --browser 指定路径。")


def render(browser: str, target: Target, workdir: Path) -> Image.Image:
    """用无头浏览器按目标尺寸渲染，保留透明通道。"""
    page = workdir / f"{target.name}.html"
    shot = workdir / f"{target.name}.png"
    page.write_text(
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        "html,body{margin:0;padding:0;background:transparent;overflow:hidden}"
        "img{position:absolute;display:block;"
        f"left:{target.offset}px;top:{target.offset}px;"
        f"width:{target.art}px;height:{target.art}px}}"
        f'</style></head><body><img src="{SVG.as_uri()}" alt=""></body></html>',
        encoding="utf-8",
    )

    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--default-background-color=00000000",
            f"--window-size={target.canvas},{target.canvas}",
            f"--screenshot={shot}",
            page.as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=120,
    )

    if not shot.exists():
        sys.exit(f"无头浏览器未产出 {target.name} 截图。")

    with Image.open(shot) as raw:
        return raw.convert("RGBA")


def targets() -> list[Target]:
    items = [
        Target(f"icon-{size}", size, size, 0, ICON_DIR / f"{size}.png") for size in (16, 32, 48)
    ] + [
        Target("store-128", STORE_CANVAS, STORE_ART, STORE_PADDING, ICON_DIR / "128.png"),
        Target(
            "source-1024",
            STORE_CANVAS * SOURCE_SCALE,
            STORE_ART * SOURCE_SCALE,
            STORE_PADDING * SOURCE_SCALE,
            SOURCE_PNG,
        ),
    ]

    # 官网 favicon / og:image 用满版图（不补内边距），与扩展图标同源，
    # 避免两处各存一份手绘素材而逐渐走样。
    if WEBSITE_PUBLIC.is_dir():
        items += [
            Target(f"website-{size}", size, size, 0, WEBSITE_PUBLIC / f"icon-{size}.png")
            for size in (32, 128)
        ]

    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="生成扩展图标 PNG")
    parser.add_argument("--browser", help="Chrome/Edge 可执行文件路径")
    args = parser.parse_args()

    if not SVG.exists():
        sys.exit(f"缺少矢量源：{SVG}")

    browser = args.browser or find_browser()

    with tempfile.TemporaryDirectory() as tmp:
        for target in targets():
            image = render(browser, target, Path(tmp))

            if image.size != (target.canvas, target.canvas):
                sys.exit(f"{target.name} 尺寸异常：{image.size}，应为 {target.canvas}²")
            alpha_min, alpha_max = image.getchannel("A").getextrema()
            # 带内边距的目标（128 / 1024）必须存在完全透明的留白，证明合规；
            # 小尺寸工具栏图标只要求角落有透明像素（圆角），不强制 alpha=0。
            needs_transparent_gutter = target.canvas > target.art
            if alpha_max != 255 or (needs_transparent_gutter and alpha_min != 0) or alpha_min == 255:
                sys.exit(f"{target.name} alpha 异常（{alpha_min}~{alpha_max}），检查 SVG 是否满版铺色")
            if needs_transparent_gutter:
                edge = target.offset
                expected = (edge, edge, target.canvas - edge, target.canvas - edge)
                if image.getbbox() != expected:
                    sys.exit(
                        f"{target.name} 实际图形边界 {image.getbbox()}，"
                        f"应为 {expected}（{target.art}×{target.art} 图形 + {edge}px 内边距）"
                    )

            target.out.parent.mkdir(parents=True, exist_ok=True)
            image.save(target.out, "PNG", optimize=True)
            rel = str(target.out.relative_to(ROOT.parent))
            print(f"写入 {rel:<40} {target.canvas}×{target.canvas}")


if __name__ == "__main__":
    main()
