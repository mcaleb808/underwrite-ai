"""Markdown-aware chunker that splits guidelines by H2 headings."""

import re


def chunk_markdown(text: str) -> list[dict[str, str]]:
    """Split a markdown document into chunks at H2 (##) boundaries.

    Each chunk includes the rule_id (e.g. UW-030), section title, and full text.
    The document header (before the first H2) is discarded.
    """
    # split on H2 lines, keeping the heading
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section.startswith("## "):
            continue

        # extract heading line
        heading = section.split("\n", 1)[0].lstrip("# ").strip()

        # extract rule_id (e.g. "UW-001") from heading
        rule_match = re.match(r"(UW-\d+)", heading)
        if not rule_match:
            continue

        rule_id = rule_match.group(1)
        # section title is everything after the rule_id
        section_title = re.sub(r"^UW-\d+\s*[-\u2013\u2014]*\s*", "", heading).strip()
        if not section_title:
            section_title = heading

        chunks.append(
            {
                "rule_id": rule_id,
                "section_title": section_title,
                "text": section,
            }
        )

    return chunks
