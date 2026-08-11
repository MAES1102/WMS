#!/usr/bin/env python3
"""
WMS Report PDF Builder
======================
1. Renders every PlantUML block  → docs/figures/fig_NN.png   (java plantuml.jar)
2. Renders every Mermaid block   → docs/figures/fig_NN.png   (mmdc / Chrome)
3. Generates pyreverse diagrams  → docs/figures/pyreverse_*.png
4. Writes docs/REPORT_RENDER.md  (diagram fences replaced by image refs)
5. Runs pandoc + weasyprint      → REPORT_FINAL_UPDATED.pdf

CSS: docs/report-style.css  (IEEE/ACM academic style, A4, page numbers)
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE          = Path(__file__).parent.resolve()          # project root
REPORT_MD     = BASE / "docs" / "REPORT.md"
FIGURES_DIR   = BASE / "docs" / "figures"
RENDER_MD     = BASE / "docs" / "REPORT_RENDER.md"
CSS_FILE      = BASE / "docs" / "report-style.css"
FINAL_PDF     = BASE / "REPORT_FINAL_SUBMISSION.pdf"
PLANTUML_JAR  = BASE / "plantuml.jar"
MMDC_BIN      = BASE / "node_modules" / ".bin" / "mmdc"
VENV_BIN      = BASE / "venv" / "bin"
WEASYPRINT    = VENV_BIN / "weasyprint"
PYREVERSE     = VENV_BIN / "pyreverse"
PANDOC        = shutil.which("pandoc")
PUPPETEER_CFG = BASE / "puppeteer-config.json"
CHROME_PATH   = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ── Tool checks ───────────────────────────────────────────────────────────────
def check_tools():
    ok = True
    checks = [
        ("java",        ["java", "-version"]),
        ("plantuml.jar", None),
        ("mmdc",        [str(MMDC_BIN), "--version"]),
        ("pandoc",      [PANDOC or "pandoc", "--version"]),
        ("weasyprint",  [str(WEASYPRINT), "--version"]),
        ("pyreverse",   [str(PYREVERSE), "--version"]),
        ("dot",         ["dot", "-V"]),
    ]
    for name, cmd in checks:
        if name == "plantuml.jar":
            exists = PLANTUML_JAR.exists()
            print(f"  {'✓' if exists else '✗'} {name}: {PLANTUML_JAR}")
            if not exists:
                ok = False
        else:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                ver = (r.stdout + r.stderr).splitlines()[0][:60]
                print(f"  ✓ {name}: {ver}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                ok = False
    return ok


# ── PlantUML renderer ─────────────────────────────────────────────────────────
def render_plantuml(source: str, name: str) -> Path:
    puml_file = FIGURES_DIR / f"{name}.puml"
    png_file  = FIGURES_DIR / f"{name}.png"
    puml_file.write_text(source, encoding="utf-8")
    r = subprocess.run(
        ["java", "-jar", str(PLANTUML_JAR), "-tpng", "-o", str(FIGURES_DIR), str(puml_file)],
        capture_output=True, text=True
    )
    if r.returncode != 0 or not png_file.exists():
        if png_file.exists():
            print(f"    ~ {png_file.name}  (render failed, using cached PNG)")
        else:
            print(f"    ✗ PlantUML failed for {name}: {r.stderr[:200]}")
    else:
        print(f"    ✓ {png_file.name}  ({png_file.stat().st_size:,} bytes)")
    return png_file


# ── Mermaid renderer ──────────────────────────────────────────────────────────
def render_mermaid(source: str, name: str) -> Path:
    mmd_file = FIGURES_DIR / f"{name}.mmd"
    png_file = FIGURES_DIR / f"{name}.png"
    mmd_file.write_text(source, encoding="utf-8")
    cmd = [
        str(MMDC_BIN),
        "-i", str(mmd_file),
        "-o", str(png_file),
        "-b", "white",
        "-w", "1200",
        "--puppeteerConfigFile", str(PUPPETEER_CFG),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE), timeout=60)
    if r.returncode != 0 or not png_file.exists():
        if png_file.exists():
            print(f"    ~ {png_file.name}  (render failed, using cached PNG)")
        else:
            print(f"    ✗ Mermaid failed for {name}: {r.stderr[:200]}")
    else:
        print(f"    ✓ {png_file.name}  ({png_file.stat().st_size:,} bytes)")
    return png_file


# ── Figure-number extractor ───────────────────────────────────────────────────
def extract_fig_number(preceding: str):
    # Match caption-style bold references (e.g. **Figure 9 —) using the LAST
    # match so the figure's own caption wins over cross-references inside
    # diagram content that appears earlier in the look-back window.
    matches = list(re.finditer(r'\*\*Figure\s+(\d+)', preceding))
    if matches:
        return int(matches[-1].group(1))
    # Fallback: plain "Figure N —" with em/en-dash (also caption format)
    matches = list(re.finditer(r'Figure\s+(\d+)\s*[—–]', preceding))
    if matches:
        return int(matches[-1].group(1))
    return None


# ── Main processing loop ──────────────────────────────────────────────────────
def process_report():
    text = REPORT_MD.read_text(encoding="utf-8")
    pattern = re.compile(r'```(plantuml|mermaid)\n(.*?)```', re.DOTALL)

    auto_idx = 0
    rendered = []

    def replacer(m: re.Match) -> str:
        nonlocal auto_idx
        lang   = m.group(1)
        source = m.group(2)
        start  = m.start()

        # 1200-char window to capture long caption lines (some exceed 500 chars)
        preceding = text[max(0, start - 1200): start]
        fig_n = extract_fig_number(preceding)

        if fig_n is not None:
            name = f"fig_{fig_n:02d}"
        else:
            auto_idx += 1
            name = f"fig_auto_{auto_idx:02d}"

        print(f"  [{lang.upper():8s}] {name}")

        if lang == "plantuml":
            out = render_plantuml(source, name)
        else:
            out = render_mermaid(source, name)

        rendered.append(out)

        # Image path relative to docs/ (where REPORT_RENDER.md sits)
        rel = out.relative_to(FIGURES_DIR.parent)
        caption = f"Figure {fig_n}" if fig_n else name
        return f"\n![{caption}]({rel}){{width=100%}}\n"

    new_text = pattern.sub(replacer, text)
    return new_text, rendered


# ── Pyreverse (source-code UML) ───────────────────────────────────────────────
def run_pyreverse():
    print("\n── Pyreverse diagrams ──────────────────────────────────────────────")
    r = subprocess.run(
        [str(PYREVERSE), "-o", "png", "-p", "WMS", str(BASE / "app")],
        capture_output=True, text=True, cwd=str(FIGURES_DIR)
    )
    for png in ["classes_WMS.png", "packages_WMS.png"]:
        p = FIGURES_DIR / png
        if p.exists():
            print(f"  ✓ {png}  ({p.stat().st_size:,} bytes)")
        else:
            print(f"  ✗ {png} not generated: {r.stderr[:200]}")


# ── PDF generation ────────────────────────────────────────────────────────────
def generate_pdf(render_md: Path):
    print("\n── PDF generation ──────────────────────────────────────────────────")
    if not PANDOC:
        print("  ✗ pandoc not found"); return False

    if not CSS_FILE.exists():
        print(f"  ✗ CSS not found: {CSS_FILE}"); return False

    html_file = BASE / "docs" / "REPORT_RENDER.html"

    # pandoc: markdown+raw_html passes the cover-page <div> block through intact
    pandoc_cmd = [
        PANDOC, str(render_md),
        "--standalone",
        "--embed-resources",
        "--from", "markdown+raw_html",
        "--to", "html5",
        "--highlight-style", "kate",
        "--resource-path", str(FIGURES_DIR.parent),
        "--css", str(CSS_FILE),
        "--metadata", "pagetitle=WMS Final Report — Yermek Aubayev",
        "--metadata", "lang=en",
        "-o", str(html_file),
    ]
    r1 = subprocess.run(pandoc_cmd, capture_output=True, text=True, cwd=str(BASE / "docs"))
    if r1.returncode != 0:
        print(f"  ✗ pandoc html: {r1.stderr[:500]}"); return False
    print(f"  ✓ HTML: {html_file}  ({html_file.stat().st_size:,} bytes)")

    r2 = subprocess.run(
        [str(WEASYPRINT), str(html_file), str(FINAL_PDF)],
        capture_output=True, text=True
    )
    if r2.returncode != 0 or not FINAL_PDF.exists():
        print(f"  ✗ weasyprint: {r2.stderr[:500]}"); return False

    size_mb = FINAL_PDF.stat().st_size / 1_048_576
    print(f"  ✓ PDF: {FINAL_PDF}  ({size_mb:.1f} MB)")
    return True


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    print("═" * 67)
    print("  WMS Report PDF Builder  →  REPORT_FINAL_SUBMISSION.pdf")
    print("═" * 67)

    print("\n── Tool verification ───────────────────────────────────────────────")
    check_tools()   # informational only — build continues regardless

    # Write puppeteer config
    PUPPETEER_CFG.write_text(
        json.dumps({"executablePath": CHROME_PATH}, indent=2)
    )

    print("\n── Diagram rendering ───────────────────────────────────────────────")
    new_text, rendered = process_report()

    RENDER_MD.write_text(new_text, encoding="utf-8")
    print(f"\n  ✓ Rendered markdown → {RENDER_MD}")
    print(f"  ✓ Total diagrams processed: {len(rendered)}")

    run_pyreverse()

    ok = generate_pdf(RENDER_MD)

    print("\n" + "═" * 67)
    print("  SUMMARY")
    print("─" * 67)
    print(f"  CSS       : {CSS_FILE}")
    print(f"  Figures   : {FIGURES_DIR}")
    print(f"  Final PDF : {FINAL_PDF}")
    all_ok = True
    for p in sorted(FIGURES_DIR.glob("fig_*.png")):
        ok_flag = p.stat().st_size > 500
        all_ok = all_ok and ok_flag
        print(f"    {'✓' if ok_flag else '✗'} {p.name}  ({p.stat().st_size:,} b)")
    print("═" * 67)
    sys.exit(0 if (ok and all_ok) else 1)


if __name__ == "__main__":
    main()
