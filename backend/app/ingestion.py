import re
from pathlib import Path
from typing import Any
EVENT_RULES = {
    "lost_circulation": ("lost circulation", "loss of returns", "mud loss"),
    "kick": ("kick", "influx"),
    "stuck_pipe": ("stuck pipe", "pipe stuck"),
    "torque_drag": ("torque drag", "high torque", "drag"),
    "pressure_anomaly": ("pressure anomaly", "abnormal pressure", "pressure spike"),
    "cementing_issue": ("cementing issue", "cement failure", "poor cement"),
    "fishing": ("fishing", "fish in hole"),
    "npt": ("npt", "non-productive time", "non productive time"),
}
SEVERITIES = ("critical", "high", "medium", "low")
def extract_pages(filename: str, content: bytes) -> list[str]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return [content.decode("utf-8", errors="replace")]
    if suffix == ".pdf":
        try:
            import fitz
            document = fitz.open(stream=content, filetype="pdf")
            pages = [page.get_text() for page in document]
            if any(page.strip() for page in pages):
                return pages
        except Exception as fitz_error:
            pages = None
        try:
            import pdfplumber
            with pdfplumber.open(stream=content) as fallback:
                return [(page.extract_text() or "") for page in fallback.pages]
        except ImportError:
            if pages is not None:
                return pages
            raise ValueError("PDF extraction failed and optional pdfplumber is not installed") from fitz_error
        except Exception as fallback_error:
            raise ValueError(f"PDF extraction failed: {fallback_error}") from fallback_error
    raise ValueError("Only PDF and TXT reports are supported")
def extract_text(filename: str, content: bytes) -> str:
    return "\n".join(extract_pages(filename, content))
def extract_candidates(text: str) -> list[dict]:
    candidates = []
    for index, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        event_type = next((name for name, keywords in EVENT_RULES.items() if any(keyword in lowered for keyword in keywords)), None)
        depth_match = re.search(r"(?P<top>\d+(?:\.\d+)?)\s*(?:-|to)\s*(?P<bottom>\d+(?:\.\d+)?)\s*m", line, re.I)
        severity = next((value for value in SEVERITIES if value in lowered), None)
        formation = re.search(r"formation\s*[:=-]?\s*([A-Za-z][A-Za-z ]+)", line, re.I)
        mitigation = re.search(r"(?:mitigation|action|response)\s*[:=-]\s*(.+)$", line, re.I)
        if event_type or depth_match:
            candidates.append({"line": line.strip(), "page_or_line": index, "event_type": event_type, "top_depth_m": float(depth_match.group("top")) if depth_match else None, "bottom_depth_m": float(depth_match.group("bottom")) if depth_match else None, "formation": formation.group(1).strip() if formation else None, "severity": severity, "mitigation": mitigation.group(1).strip() if mitigation else None, "confidence": round((0.35 if event_type else 0) + (0.3 if depth_match else 0) + (0.2 if formation else 0) + (0.15 if severity else 0), 2), "review_status": "needs_review"})
    return candidates
def extract_document_pages(pages: list[str]) -> list[dict[str, Any]]:
    candidates = []
    for page_number, page in enumerate(pages, start=1):
        for candidate in extract_candidates(page):
            candidate["page_or_line"] = page_number
            candidates.append(candidate)
    return candidates
