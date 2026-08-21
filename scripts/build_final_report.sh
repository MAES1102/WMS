#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output="$root/output/pdf/event-driven-workflow-management-system.pdf"
html=$(mktemp /tmp/se-m-report.XXXXXX.html)
trap 'rm -f "$html"' EXIT
mkdir -p "$root/output/pdf"
pandoc "$root/docs/FINAL_REPORT.md" --standalone --embed-resources --resource-path="$root/docs:$root" --metadata pagetitle="Event-Driven Workflow Management System" --output "$html"
/opt/homebrew/bin/weasyprint "$html" "$output"
printf '%s\n' "$output"
