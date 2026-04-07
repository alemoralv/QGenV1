from dataclasses import dataclass


@dataclass(slots=True)
class Segment:
    source_pdf: str
    segment_index: int
    page_start: int
    page_end: int
    text: str


@dataclass(slots=True)
class QARecord:
    question: str
    expectedResponse: str
    sourcePdf: str
    segmentIndex: int
    pageStart: int
    pageEnd: int

