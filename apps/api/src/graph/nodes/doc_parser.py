"""Extract structured clinical data from medical PDFs via LLM."""

from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.graph.state import UnderwritingState
from src.schemas.medical import ParsedMedicalRecord
from src.services.log import bind, get_logger, llm_observability
from src.tools.pdf_extract import extract_text

log = get_logger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

SYSTEM = (
    "You extract structured clinical facts from medical PDFs into JSON matching the"
    " ParsedMedicalRecord schema. Copy values verbatim where possible. If a field is"
    " absent in the document, leave it empty — do not invent values. Lab `flag` must"
    " be one of high|low|normal. Diagnosis `status` must be one of"
    " active|controlled|resolved when stated, otherwise null."
)


def _resolve(p: str) -> Path:
    path = Path(p)
    if path.is_absolute() and path.exists():
        return path
    return DATA_DIR / p


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.FAST_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=0,
        callbacks=[llm_observability],
    )


def _parse_one(pdf_path: Path) -> ParsedMedicalRecord:
    text = extract_text(pdf_path)
    if not text:
        return ParsedMedicalRecord(source_path=str(pdf_path))

    structured = _llm().with_structured_output(ParsedMedicalRecord)
    result = structured.invoke(
        [
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Source: {pdf_path.name}\n\n---\n{text}"),
        ]
    )
    # with_structured_output returns the model with source_path possibly missing;
    # ensure it is set deterministically.
    if isinstance(result, ParsedMedicalRecord):
        result.source_path = str(pdf_path)
        return result
    return ParsedMedicalRecord(source_path=str(pdf_path), **dict(result))


def run(state: UnderwritingState) -> dict[str, Any]:
    bind(node="doc_parser", task_id=state.get("task_id"))
    paths = state.get("medical_doc_paths") or []
    if not paths and "applicant" in state:
        paths = list(state["applicant"].medical_docs)

    log.info("node_start", doc_count=len(paths))

    parsed: list[ParsedMedicalRecord] = []
    errors: list[str] = []
    for raw in paths:
        resolved = _resolve(raw)
        try:
            parsed.append(_parse_one(resolved))
        except Exception as exc:
            errors.append(f"doc_parser failed for {raw}: {exc!r}")
            log.warning("doc_parse_failed", path=raw, error=repr(exc))

    log.info("node_end", parsed=len(parsed), errors=len(errors))

    update: dict[str, Any] = {
        "parsed_medical": parsed,
        "events": [
            {
                "node": "doc_parser",
                "type": "parsed",
                "doc_count": len(parsed),
                "error_count": len(errors),
            }
        ],
    }
    if errors:
        update["errors"] = errors
    return update
