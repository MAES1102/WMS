#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
pdf_path="$repo_root/output/pdf/invoice-approval-final-report.pdf"

mkdir -p "$repo_root/output/pdf"

TEXINPUTS="$repo_root/docs:" pandoc "$repo_root/docs/FINAL_REPORT.md" \
  --from markdown+raw_tex \
  --toc \
  --resource-path="$repo_root/docs:$repo_root" \
  --pdf-engine=xelatex \
  --top-level-division=chapter \
  --variable documentclass=report \
  --variable papersize=a4 \
  --variable geometry:margin=18mm \
  --variable mainfont="DejaVu Sans" \
  --variable monofont="DejaVu Sans Mono" \
  --variable colorlinks=true \
  --variable linkcolor=ForestGreen \
  --output "$pdf_path"

printf '%s\n' "$pdf_path"
