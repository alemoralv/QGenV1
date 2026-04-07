from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from qgen.models import Segment


def extract_page_texts(pdf_path: str | Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    texts: list[str] = []
    for page in reader.pages:
        texts.append((page.extract_text() or "").strip())
    return texts


def build_segments_from_page_texts(
    source_pdf: str,
    page_texts: list[str],
    pages_per_segment: int,
) -> list[Segment]:
    segments: list[Segment] = []
    if pages_per_segment <= 0:
        raise ValueError("pages_per_segment must be > 0")

    for start in range(0, len(page_texts), pages_per_segment):
        end = min(start + pages_per_segment, len(page_texts))
        chunk_pages = page_texts[start:end]
        merged_text = "\n\n".join([t for t in chunk_pages if t.strip()]).strip()
        segments.append(
            Segment(
                source_pdf=source_pdf,
                segment_index=len(segments),
                page_start=start + 1,
                page_end=end,
                text=merged_text,
            )
        )
    return segments


def split_pdf_into_segments(
    pdf_path: str | Path,
    pages_per_segment: int,
) -> list[Segment]:
    path = Path(pdf_path)
    page_texts = extract_page_texts(path)
    return build_segments_from_page_texts(
        source_pdf=path.name,
        page_texts=page_texts,
        pages_per_segment=pages_per_segment,
    )

