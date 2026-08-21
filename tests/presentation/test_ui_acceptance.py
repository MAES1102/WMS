from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


UI_FILE = Path(__file__).parents[2] / "app" / "static" / "invoices.html"
VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.label_targets: list[str] = []
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.main_count = 0
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            self.ids.append(element_id)
        if tag == "label" and (target := attributes.get("for")):
            self.label_targets.append(target)
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1
        if tag == "form" and "form" in self.stack:
            self.errors.append("nested form")
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or tag not in self.stack:
            self.errors.append(f"unexpected closing tag: {tag}")
            return
        index = len(self.stack) - 1 - self.stack[::-1].index(tag)
        if index != len(self.stack) - 1:
            self.errors.append(
                f"misnested closing tag: {tag} after {self.stack[index + 1:]}"
            )
        self.stack = self.stack[:index]


def parsed_ui() -> tuple[str, StructureParser]:
    source = UI_FILE.read_text(encoding="utf-8")
    parser = StructureParser()
    parser.feed(source)
    parser.close()
    return source, parser


def test_ui_has_one_well_formed_primary_document_structure() -> None:
    _source, parser = parsed_ui()
    duplicate_ids = sorted(
        element_id
        for element_id, count in Counter(parser.ids).items()
        if count > 1
    )

    assert parser.main_count == 1
    assert parser.h1_count == 1
    assert duplicate_ids == []
    assert parser.errors == []
    assert parser.stack == []
    assert set(parser.label_targets) <= set(parser.ids)


def test_primary_status_exposes_user_outcome_before_technical_trace() -> None:
    source, _parser = parsed_ui()

    required_status_fields = (
        'id="invoice-title"',
        'id="status-supplier"',
        'id="status-state"',
        'id="status-next-action"',
        'id="status-final-result"',
        'id="status-mode"',
        'id="status-scenario"',
    )
    assert all(field in source for field in required_status_fields)
    assert source.index('id="business-result"') < source.index(
        "Technical audit trace"
    )
    assert '<details>\n          <summary>Technical audit trace</summary>' in source
    assert '<details class="constructor-details">' in source
    assert '<details class="constructor-details" open>' not in source
    assert "Workflow constructor (advanced)" in source
    assert 'id="scenario" name="scenario"' in source
    assert "Archive fails once, then succeeds" in source
    assert "Archive remains unavailable" in source
    assert "run.invoice_number" in source
    assert "run.supplier_name" in source


def test_ui_has_keyboard_and_live_feedback_hooks() -> None:
    source, _parser = parsed_ui()

    assert 'class="skip-link" href="#main-content"' in source
    assert 'id="run-view" class="process hidden" aria-live="polite"' in source
    assert source.count('role="alert"') == 3
    assert '<caption class="sr-only">' in source
    assert "button:focus-visible" in source
