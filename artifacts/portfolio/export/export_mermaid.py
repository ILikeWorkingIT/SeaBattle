"""Extract Mermaid fences from portfolio diagrams and render SVG/PNG via Kroki."""

from __future__ import annotations

import base64
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPORT = Path(__file__).resolve().parent
MMD_DIR = EXPORT / "mmd"

SOURCES: tuple[tuple[str, str], ...] = (
    ("diagrams/diagram-c4-001.md", "c4"),
    ("diagrams/diagram-seq-001.md", "seq-shot"),
    ("diagrams/diagram-seq-002.md", "seq-reconnect"),
    ("diagrams/diagram-state-001.md", "state-session"),
    ("diagrams/diagram-ai-overview.md", "ai-overview"),
    ("diagrams/diagram-class-session-overview.md", "class-session"),
    ("diagrams/diagram-dfd-overview.md", "dfd-overview"),
    ("diagrams/diagram-redis-keys.md", "redis-keys"),
)

FENCE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def extract() -> list[Path]:
    MMD_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rel, stem in SOURCES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        blocks = FENCE.findall(text)
        if not blocks:
            raise SystemExit(f"no mermaid in {rel}")
        for i, body in enumerate(blocks, start=1):
            name = stem if len(blocks) == 1 else f"{stem}-{i}"
            path = MMD_DIR / f"{name}.mmd"
            path.write_text(body.strip() + "\n", encoding="utf-8")
            written.append(path)
    return written


def _ink(src: Path, dest: Path, fmt: str) -> None:
    diagram = src.read_text(encoding="utf-8")
    token = base64.urlsafe_b64encode(diagram.encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/{fmt}/{token}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SeaBattlePortfolioExport/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            dest.write_bytes(resp.read())
        print(f"mermaid.ink {fmt} {dest.name}")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"mermaid.ink failed for {src.name} {fmt}: {exc}")


def render(paths: list[Path]) -> None:
    print("render via mermaid.ink")
    for src in paths:
        _ink(src, EXPORT / f"{src.stem}.svg", "svg")
        _ink(src, EXPORT / f"{src.stem}.png", "img")


def write_preview(paths: list[Path]) -> None:
    parts = [
        "<!DOCTYPE html>",
        '<html lang="ru"><head><meta charset="utf-8" />',
        "<title>Sea Battle diagrams</title>",
        '<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"; mermaid.initialize({ startOnLoad: true, theme: "neutral" });</script>',
        "<style>body{font-family:Segoe UI,sans-serif;margin:24px;background:#f6f6f6} h2{margin-top:2rem} pre.mermaid{background:#fff;padding:16px}</style>",
        "</head><body>",
        "<p>Локальный просмотр (Chrome). Для слайдов удобнее готовые SVG/PNG рядом с этим файлом.</p>",
    ]
    for src in paths:
        body = src.read_text(encoding="utf-8")
        parts.append(f"<h2>{src.stem}</h2>")
        parts.append('<div class="mermaid">')
        parts.append(body)
        parts.append("</div>")
    parts.append("</body></html>")
    (EXPORT / "preview.html").write_text("\n".join(parts), encoding="utf-8")
    print("wrote preview.html")


def main() -> None:
    paths = extract()
    print(f"wrote {len(paths)} mmd files under {MMD_DIR}")
    render(paths)
    write_preview(paths)


if __name__ == "__main__":
    main()
