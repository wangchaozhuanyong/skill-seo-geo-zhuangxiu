#!/usr/bin/env python3
"""Generate local SVG design concept assets from the media asset plan."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


CONCEPT_MANIFEST_NAME = "concept-asset-manifest.json"


@dataclass
class ConceptAssetsResult:
    status: str
    generated_count: int
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def media_assets_from_plan(plan: dict[str, object]) -> list[dict[str, object]]:
    assets: list[dict[str, object]] = []
    for raw in safe_list(plan.get("media_assets")):
        if isinstance(raw, dict) and raw.get("filename"):
            assets.append(raw)
    return assets


def generated_svg_filename(filename: str) -> str:
    path = Path(filename)
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", path.stem).strip("-") or "concept-asset"
    return f"{stem}.svg"


def wrap_text(text: str, width: int = 44) -> list[str]:
    words = re.split(r"\s+", text.strip())
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:4]


def palette_for_usage(usage_type: str) -> tuple[str, str, str, str]:
    usage = usage_type.lower()
    if usage == "hero":
        return "#2f3b2f", "#d8b36a", "#f3efe2", "#8a5f36"
    if usage == "material":
        return "#35404a", "#b98f5a", "#f0e8d8", "#6f7f75"
    return "#263742", "#c99c5d", "#f5efe3", "#637c88"


def render_svg(item: dict[str, object], generated_name: str) -> str:
    usage_type = str(item.get("usage_type", "general"))
    alt_en = str(item.get("alt_en", "")) or generated_name
    alt_zh = str(item.get("alt_zh", ""))
    concept_label = str(item.get("concept_label", "design concept / rendering concept"))
    prompt = str(item.get("prompt", "Renovation design concept visual."))
    primary, accent, paper, muted = palette_for_usage(usage_type)
    title_lines = wrap_text(alt_en, width=38)
    prompt_lines = wrap_text(prompt, width=70)
    title_tspans = "\n".join(
        f'<tspan x="96" dy="{0 if index == 0 else 34}">{html.escape(line)}</tspan>' for index, line in enumerate(title_lines)
    )
    prompt_tspans = "\n".join(
        f'<tspan x="96" dy="{0 if index == 0 else 24}">{html.escape(line)}</tspan>' for index, line in enumerate(prompt_lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="960" viewBox="0 0 1600 960" role="img" aria-labelledby="title desc">
  <title id="title">{html.escape(alt_en)}</title>
  <desc id="desc">{html.escape(alt_zh or alt_en)}. Generated design concept only; not a real completed project photo.</desc>
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{primary}"/>
      <stop offset="58%" stop-color="{muted}"/>
      <stop offset="100%" stop-color="{paper}"/>
    </linearGradient>
    <linearGradient id="glow" x1="0" x2="1">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="{paper}" stop-opacity="0.2"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="22" stdDeviation="22" flood-color="#111111" flood-opacity="0.24"/>
    </filter>
  </defs>
  <rect width="1600" height="960" fill="url(#bg)"/>
  <path d="M120 820 L760 520 L1480 730 L1480 890 L120 890 Z" fill="#1d2729" opacity="0.38"/>
  <path d="M250 720 L820 420 L1330 620 L760 880 Z" fill="{paper}" opacity="0.86" filter="url(#softShadow)"/>
  <path d="M820 420 L1330 620 L1330 320 L820 150 Z" fill="#ffffff" opacity="0.42"/>
  <path d="M250 720 L820 420 L820 150 L250 360 Z" fill="#f7f0df" opacity="0.48"/>
  <rect x="915" y="388" width="235" height="132" rx="8" fill="{accent}" opacity="0.62"/>
  <rect x="510" y="548" width="350" height="92" rx="10" fill="#ffffff" opacity="0.75"/>
  <rect x="560" y="500" width="205" height="42" rx="8" fill="{primary}" opacity="0.72"/>
  <circle cx="1180" cy="240" r="126" fill="url(#glow)" opacity="0.55"/>
  <path d="M1010 690 C1120 640 1235 650 1360 710" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round" opacity="0.86"/>
  <rect x="72" y="64" width="640" height="300" rx="28" fill="#111111" opacity="0.34"/>
  <text x="96" y="124" fill="{paper}" font-family="Georgia, 'Times New Roman', serif" font-size="44" font-weight="700">
    {title_tspans}
  </text>
  <text x="96" y="278" fill="{accent}" font-family="Arial, sans-serif" font-size="24" font-weight="700" letter-spacing="2">
    {html.escape(concept_label.upper())}
  </text>
  <text x="96" y="758" fill="#172023" font-family="Arial, sans-serif" font-size="25" font-weight="700">PLANNING / RENDERING CONCEPT</text>
  <text x="96" y="806" fill="#172023" font-family="Arial, sans-serif" font-size="21">
    {prompt_tspans}
  </text>
  <rect x="96" y="858" width="760" height="42" rx="21" fill="#111111" opacity="0.68"/>
  <text x="126" y="886" fill="{paper}" font-family="Arial, sans-serif" font-size="18">
    Generated visual for design planning only. Not a real project photo, review, price proof, or before/after evidence.
  </text>
</svg>
"""


def render_report(result: ConceptAssetsResult, rows: list[dict[str, str]], asset_dir: Path) -> str:
    lines = [
        "# Concept Asset Generation Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: {result.status}",
        f"- Generated assets: {result.generated_count}",
        f"- Asset dir: `{asset_dir}`",
        "- 执行状态: draft-only；只生成本地概念 SVG，不上传媒体、不写 CMS、不发布",
        "",
        "## 今日决策",
        "",
        "今天补齐媒体链路中的本地概念效果图文件步骤：从 media asset plan 生成可审核的设计/效果图 SVG 文件，供后续 media-url-map 映射为公开 URL。",
        "",
        "## Assets",
        "",
    ]
    if rows:
        for row in rows:
            lines.append(f"- `{row['placeholder_filename']}` -> `{row['generated_filename']}` | usage: `{row['usage_type']}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
            "## Safety Notes",
            "",
            "- 这些 SVG 是设计概念/效果图方案，不是真实客户照片或完工证明。",
            "- 后续如果需要真实照片，必须由业主提供并确认可公开使用。",
            "- 上传或发布仍需要 owner approval、explicit execution、QA、backup、changelog 和 rollback plan。",
            "",
        ]
    )
    return "\n".join(lines)


def run_concept_assets(
    root: Path,
    *,
    media_plan_path: str = "",
    asset_dir: str = "",
) -> tuple[ConceptAssetsResult, tuple[Path, Path]]:
    root = root.resolve()
    plan_file = Path(media_plan_path) if media_plan_path else root / "seo-workspace" / "data" / "media-asset-plan.json"
    if not plan_file.is_absolute():
        plan_file = root / plan_file
    output_dir = Path(asset_dir) if asset_dir else root / "seo-workspace" / "media" / "generated"
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    manifest_path = data_dir / CONCEPT_MANIFEST_NAME
    report_path = reports_dir / f"{today}-concept-assets-report.md"

    media_assets = media_assets_from_plan(read_json(plan_file))
    blockers: list[str] = []
    warnings: list[str] = []
    if not media_assets:
        blockers.append("No media assets found. Run media-assets first.")

    rows: list[dict[str, str]] = []
    if not blockers:
        output_dir.mkdir(parents=True, exist_ok=True)
        for item in media_assets:
            placeholder = str(item.get("filename", ""))
            generated_name = generated_svg_filename(placeholder)
            local_path = output_dir / generated_name
            write_text(local_path, render_svg(item, generated_name))
            rows.append(
                {
                    "placeholder_filename": placeholder,
                    "generated_filename": generated_name,
                    "local_path": str(local_path),
                    "usage_type": str(item.get("usage_type", "")),
                    "mime_type": "image/svg+xml",
                    "concept_label": str(item.get("concept_label", "")),
                    "claim_boundary": "Generated SVG design/rendering concept only; not a real project photo or customer case proof.",
                }
            )
    else:
        warnings.append("Concept assets were not generated because the media plan is empty or missing.")

    status = "concept_assets_generated" if rows and not blockers else "blocked_missing_media_plan"
    result = ConceptAssetsResult(status=status, generated_count=len(rows), blockers=blockers, warnings=warnings)
    result.artifacts.update({"manifest": str(manifest_path), "report": str(report_path), "asset_dir": str(output_dir)})
    write_text(
        manifest_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "no_media_upload_executed": True,
                "assets": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result, rows, output_dir))
    return result, (manifest_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local SVG design concept assets from media-asset-plan.json.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--media-plan-path", default="")
    parser.add_argument("--asset-dir", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, _ = run_concept_assets(Path(args.root), media_plan_path=args.media_plan_path, asset_dir=args.asset_dir)
    for artifact in result.artifacts.values():
        print(artifact)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
