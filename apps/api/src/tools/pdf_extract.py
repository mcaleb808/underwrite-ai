"""PDF text extraction helper used by doc_parser."""

from pathlib import Path

from pypdf import PdfReader


def extract_text(pdf_path: str | Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(parts).strip()
