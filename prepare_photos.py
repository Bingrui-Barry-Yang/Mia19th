#!/usr/bin/env python3
"""Convert Photos source images into ordered, web-friendly WebP files."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "Photos"
OUTPUT_DIR = SOURCE_DIR / "web"
SUPPORTED = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp"}


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("找不到 ffmpeg，无法转换照片。")

    sources = sorted(
        (
            path
            for path in SOURCE_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED
        ),
        key=lambda path: path.name.casefold(),
    )
    if not sources:
        raise SystemExit("Photos/ 中没有可转换的照片。")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in OUTPUT_DIR.glob("*.webp"):
        old_file.unlink()

    with tempfile.TemporaryDirectory(prefix="mia-photos-") as temp_name:
        temp_dir = Path(temp_name)
        heic_sources = [
            path for path in sources if path.suffix.lower() in {".heic", ".heif"}
        ]
        if heic_sources:
            if shutil.which("qlmanage") is None:
                raise SystemExit("找不到 macOS Quick Look，无法读取 HEIC。")
            run(
                ["qlmanage", "-t", "-s", "2400", "-o", str(temp_dir)]
                + [str(path) for path in heic_sources]
            )

        for index, source in enumerate(sources, start=1):
            if source.suffix.lower() in {".heic", ".heif"}:
                converted_source = temp_dir / f"{source.name}.png"
                if not converted_source.exists():
                    raise SystemExit(f"HEIC 转换失败：{source.name}")
            else:
                converted_source = source

            output = OUTPUT_DIR / f"{index:03d}.webp"
            run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(converted_source),
                    "-vf",
                    "scale='min(1800,iw)':-2",
                    "-c:v",
                    "libwebp",
                    "-quality",
                    "84",
                    "-compression_level",
                    "6",
                    "-y",
                    str(output),
                ]
            )
            print(f"[{index:03d}/{len(sources):03d}] {source.name} -> {output.name}")

    print(f"已生成 {len(sources)} 张网页照片：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
