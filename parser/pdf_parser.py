"""
Parse USDA-style inspection PDFs with pdfplumber + regex heuristics.

Layouts vary; tune PATTERNS_* if your PDFs differ.
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)
import re
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw_pdfs"

DATE_PATTERNS = [
    re.compile(
        r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b"
    ),
    re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+(?:19|20)\d{2}",
        re.I,
    ),
    # APHIS PST: 23-JAN-2026
    re.compile(r"\b\d{1,2}-(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)-\d{4}\b", re.I),
]

# APHIS Public Search Tool inspection report header
APHIS_PST_FACILITY = re.compile(
    r"(?is)Inspection Report\s*\r?\n\s*(.+?)\s+Customer ID\s*:",
)
APHIS_PST_LOCATION = re.compile(
    r"(?m)^(\d[\dA-Za-z\s,.#-]+?)\s+Certificate\s*:\s*[^\n]+\r?\n\s*([^\n]+)$",
)
APHIS_PST_INSPECTION_DATE = re.compile(
    r"(?im)^\s*Date:\s*(\d{1,2}-[A-Z]{3}-\d{4})\s*$",
)

FACILITY_LINE = re.compile(
    r"(?im)^\s*(?:facility|establishment|name|business)\s*[:#]?\s*(.+)$"
)
COMPANY_LINE = re.compile(r"(?im)^\s*company\s*[:#]?\s*(.+)$")
LOCATION_LINE = re.compile(
    r"(?im)^\s*(?:address|location|city\s*,?\s*state)\s*[:#]?\s*(.+)$"
)

SEVERITY_CRITICAL = re.compile(
    r"(?im)\b(critical|direct\s+noncompliance|repeat\s+noncompliance)\b"
)
SEVERITY_NON = re.compile(r"(?im)\b(non[- ]?critical|noncritical|minor)\b")

SPECIES_HINT = re.compile(
    r"(?i)\b(cattle|swine|poultry|chicken|turkey|sheep|goat|bison|equine|horse|deer|elk)\b"
)

def _extract_dates(text: str) -> list[str]:
    found: list[str] = []
    for pat in DATE_PATTERNS:
        found.extend(m.group(0).strip() for m in pat.finditer(text))
    return found


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def _guess_species(text: str) -> str | None:
    m = SPECIES_HINT.search(text)
    return m.group(1).title() if m else None


def _line_starts_non_critical(line: str) -> bool:
    s = line.strip().lower()
    return s.startswith("non-critical") or s.startswith("noncritical")


def _line_starts_critical(line: str) -> bool:
    s = line.strip().lower()
    if _line_starts_non_critical(line):
        return False
    return bool(re.match(r"^critical\b", s))


def _split_violation_entries(text: str) -> list[tuple[str, str]]:
    """Return list of (severity_label, body) from raw text."""
    # APHIS PST: e.g. "2.126(b) Critical Repeat" then narrative until "End Section"
    m_aphis = re.search(
        r"(?s)(\d+\.\d+\([^)]+\)\s*Critical[^\n]*)\r?\n(.*?)(?=End\s+Section)",
        text,
    )
    if m_aphis:
        body = (m_aphis.group(1) + "\n" + m_aphis.group(2)).strip()
        return [("Critical", body)]

    lines = text.splitlines()
    entries: list[tuple[str, str]] = []
    current_sev = "Unknown"
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        body = "\n".join(buf).strip()
        if body:
            entries.append((current_sev, body))
        buf = []

    for line in lines:
        # e.g. "2.126(b) Critical Repeat" (APHIS regulation line)
        if re.search(r"(?i)\d+\.\d+\([^)]+\)\s*Critical\b", line) and not re.search(
            r"(?i)non[-\s]?critical", line
        ):
            flush()
            current_sev = "Critical"
            buf.append(line.strip())
        elif _line_starts_critical(line):
            flush()
            current_sev = "Critical"
            rest = re.sub(r"(?i)^critical\s*[:|\-]?\s*", "", line.strip())
            if rest:
                buf.append(rest)
        elif _line_starts_non_critical(line) or re.match(
            r"(?i)^non[-\s]?critical\b", line.strip()
        ):
            flush()
            current_sev = "Non-Critical"
            rest = re.sub(r"(?i)^non[-\s]?critical\s*[:|\-]?\s*", "", line.strip())
            if rest:
                buf.append(rest)
        elif len(line.strip()) > 2:
            buf.append(line.rstrip())

    flush()

    if not entries:
        chunk_severity = "Unknown"
        for line in lines:
            if SEVERITY_CRITICAL.search(line) and not SEVERITY_NON.search(line):
                chunk_severity = "Critical"
            elif SEVERITY_NON.search(line):
                chunk_severity = "Non-Critical"
            elif len(line.strip()) > 40:
                entries.append((chunk_severity, line.strip()))

    return entries if entries else [("Unknown", text[:2000])]


def _facility_meta(text: str) -> dict[str, str | None]:
    name = None
    m = APHIS_PST_FACILITY.search(text)
    if m:
        name = re.sub(r"\s+", " ", m.group(1).strip())
    if not name:
        name = _first_match(FACILITY_LINE, text)
    if not name:
        for line in text.splitlines()[:15]:
            s = line.strip()
            if len(s) > 5 and not s.lower().startswith("page"):
                name = s
                break

    loc = _first_match(LOCATION_LINE, text)
    if not loc:
        ml = APHIS_PST_LOCATION.search(text)
        if ml:
            loc = f"{ml.group(1).strip()}, {ml.group(2).strip()}"

    return {
        "facility_name": name,
        "company": _first_match(COMPANY_LINE, text),
        "location": loc,
    }


def parse_pdf(path: Path) -> list[dict[str, Any]]:
    """Parse one PDF; return one dict per violation row."""
    path = Path(path)
    rows: list[dict[str, Any]] = []
    try:
        with pdfplumber.open(path) as pdf:
            text = "\n".join(
                (page.extract_text() or "") for page in pdf.pages
            )
    except Exception as e:
        logger.error("Failed to read %s: %s", path.name, e)
        return rows

    text = text or ""
    meta = _facility_meta(text)
    dates = _extract_dates(text)
    m_ins = APHIS_PST_INSPECTION_DATE.search(text)
    if m_ins:
        inspection_date = m_ins.group(1)
    elif dates:
        inspection_date = dates[0]
    else:
        inspection_date = "Unknown"
    species = _guess_species(text)

    entries = _split_violation_entries(text)
    if not entries:
        entries = [("Unknown", text[:2000])]

    for severity, notes in entries:

        if severity == "Unknown":
            if re.search(r"critical|direct\s+noncompliance|repeat\s+noncompliance", notes, re.I):
                severity = "Critical"
        elif re.search(r"non[- ]?critical|minor", notes, re.I):
            severity = "Non-Critical"

        row = {
        "facility_name": meta.get("facility_name") or "Unknown",
        "company": meta.get("company") or "",
        "location": meta.get("location") or "",
        "inspection_date": inspection_date,
        "severity": severity,
        "species": species,
        "inspector_notes": notes[:8000],
        "source_pdf": path.name,
        }
        rows.append(row)

    return rows


def parse_all_pdfs(
    raw_dir: Path | None = None,
    glob: str = "*.pdf",
) -> list[dict[str, Any]]:
    """Load every PDF under raw_dir and flatten to structured rows."""
    raw = Path(raw_dir) if raw_dir else RAW_DIR
    if not raw.is_dir():
        logger.warning("Directory missing: %s", raw)
        return []
    out: list[dict[str, Any]] = []
    for pdf_path in sorted(raw.glob(glob)):
        if pdf_path.is_file():
            out.extend(parse_pdf(pdf_path))
    return out
