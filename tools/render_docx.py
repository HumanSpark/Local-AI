# File: tools/render_docx.py
# Purpose: Render the documents a model produced via tool use into Word-styled PNG screenshots (visual proof).
# Project: sparkbench | Date: 2026-07-14
#
# Overview: Reads a tooluse_harness results JSON, and for each create_word_document tool call builds a
# Word-like A4 HTML page (title + body paragraphs, 1-inch margins, office font) and screenshots it with
# Playwright (system python has playwright + Pillow; the chromium browser is already cached). The rendered
# content is exactly what _exec_tool wrote into the .docx, so the PNG faithfully shows the saved document.
# Output PNGs are kept well under the 2000px limit (A4 at 96dpi = 794x1123).

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PNG_DIR = ROOT / "results/tool-use/png"

PAGE_CSS = """
<style>
  html,body{margin:0;background:#525659}
  .page{width:794px;min-height:1123px;margin:0 auto;background:#fff;
        padding:96px 96px 96px 96px;box-sizing:border-box;
        font-family:'Calibri','Carlito','DejaVu Sans',sans-serif;color:#1a1a1a;
        font-size:15px;line-height:1.5}
  h1{font-size:20px;font-weight:700;margin:0 0 18px;color:#1f3864}
  p{margin:0 0 11px;white-space:pre-wrap}
  .tag{position:absolute;top:8px;left:50%;transform:translateX(-50%);
       color:#cfd3d6;font:600 12px sans-serif}
</style>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def doc_html(title: str, paras: list[str], tag: str) -> str:
    body = "".join(f"<p>{esc(str(p))}</p>" for p in paras)
    head = f"<h1>{esc(title)}</h1>" if title else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'>{PAGE_CSS}</head>"
            f"<body><div class='tag'>{esc(tag)}</div><div class='page'>{head}{body}</div></body></html>")


def main() -> None:
    ap = argparse.ArgumentParser(description="Render tool-use documents to Word-styled PNG screenshots.")
    ap.add_argument("--results", required=True, help="path to a results-<label>.json from tooluse_harness")
    ap.add_argument("--only", nargs="*", help="optional task ids to render (default: all with a docx call)")
    args = ap.parse_args()

    data = json.loads(Path(args.results).read_text())
    label = data["label"]
    out_dir = PNG_DIR / label
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, str, list[str]]] = []
    for r in data["results"]:
        if args.only and r["id"] not in args.only:
            continue
        for c in r.get("called", []):
            if c["name"] == "create_word_document" and c.get("json_ok") and c.get("args"):
                a = c["args"]
                paras = a.get("body_paragraphs") or []
                if isinstance(paras, str):
                    paras = [paras]
                jobs.append((r["id"], str(a.get("title") or ""), [str(p) for p in paras]))
                break

    if not jobs:
        print(f"  no renderable create_word_document calls in {args.results}")
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
        for task_id, title, paras in jobs:
            page.set_content(doc_html(title, paras, f"{label}  ·  {task_id}"))
            png = out_dir / f"{task_id}.png"
            page.screenshot(path=str(png), full_page=True)
            print(f"  rendered {png.relative_to(ROOT)}")
        browser.close()


if __name__ == "__main__":
    main()
