from qgen.allocator import allocate_questions_across_segments
from qgen.models import Segment


def _segment(i: int, text: str) -> Segment:
    return Segment(
        source_pdf="sample.pdf",
        segment_index=i,
        page_start=i * 10 + 1,
        page_end=(i + 1) * 10,
        text=text,
    )


def test_allocate_evenly_with_remainder():
    segments = [_segment(0, "a"), _segment(1, "b"), _segment(2, "c")]
    allocated = allocate_questions_across_segments(segments, 10)
    assert allocated == {0: 4, 1: 3, 2: 3}
    assert sum(allocated.values()) == 10


def test_allocate_skips_empty_segments():
    segments = [_segment(0, "a"), _segment(1, ""), _segment(2, "c")]
    allocated = allocate_questions_across_segments(segments, 5)
    assert allocated == {0: 3, 2: 2}

