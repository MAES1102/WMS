# PBI-E26 — Final Report and Defense Reconciliation

| Field | Value |
|---|---|
| Status | `ACCEPTED — project-level final artifact reconciliation` |
| Date | `2026-08-13` |
| Entry evidence | PBI-E24 and PBI-E25 accepted; EV-045 and EV-046 |
| Instructor approval | `NOT CLAIMED` |

## 1. Report correction

The preserved 41-page prototype report described optional Kafka, random task outcomes, cyclic retry, a primarily abstract workflow demonstration, and historical Scrum measurements that no longer match the accepted invoice product or current evidence policy. E26 does not overwrite that historical record. It creates a separate final report for the invoice-approval reference application.

The new report leads with the practical invoice problem, user-visible states/actions/results, and the five business scenarios. It then explains requirements, process evidence, architecture, shared custom logic, both execution modes, implementation, verification, deployment, reuse, and limitations. The final claim ledger distinguishes verified results from unexecuted container/browser/production/release work.

## 2. UML correction

Eight PlantUML v3 sources were rendered locally to vector SVG and PDF without an external rendering service. Every SVG was scanned for PlantUML/Graphviz error pages. A contact sheet and the final report pages were visually inspected. Sequence views use dedicated landscape pages; other views are full vector figures. Captions, clipping, orientation, and duplicate numbering were corrected before the final build.

## 3. Reuse and defense material

`docs/REUSE_DISCLOSURE.md` separates general-purpose open-source dependencies, temporary verification tooling, behavioral product references, and independently implemented workflow policy. It states that Camunda, n8n, and Temporal are references only and that no external engine/source/definition/diagram/UI is included.

`docs/DEFENSE_SCRIPT.md` provides a product-first five-minute demonstration, likely questions, evidence statements, and explicit limitations. It prevents the defense from leading with task lights, raw trace, or the advanced constructor.

## 4. Generated output and checks

`scripts/build_final_report.sh` builds `output/pdf/invoice-approval-final-report.pdf` through Pandoc/XeLaTeX. The recorded build is 39 pages, A4 with two correctly rotated landscape sequence pages, approximately 629 KiB, and contains no extracted PlantUML/Graphviz error text. The report and all 39 rendered pages were inspected as a contact sheet; key business, UML, sequence, and activity pages were inspected at full size.

Final repository checks re-run the full suite (`220 passed in 10.83s`), Python compilation, JavaScript syntax, UML-source balance/error scans, PDF metadata/text checks, and `git diff --check`. Git durability, commit, push, release, external deployment, and instructor approval remain separate decisions and are not claimed by this record.
