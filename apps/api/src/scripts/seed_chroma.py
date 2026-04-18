"""Seed the Chroma vector store with underwriting guidelines."""

from pathlib import Path

from src.config import settings
from src.rag.ingest import ingest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    md_path = DATA_DIR / "guidelines.md"
    count = ingest(md_path, settings.CHROMA_DIR)
    print(f"ingested {count} guideline chunks into {settings.CHROMA_DIR}")


if __name__ == "__main__":
    main()
