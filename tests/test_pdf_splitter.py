from qgen.pdf_splitter import build_segments_from_page_texts


def test_build_segments_10_page_boundaries():
    pages = [f"page {i}" for i in range(1, 26)]
    segments = build_segments_from_page_texts("a.pdf", pages, pages_per_segment=10)

    assert len(segments) == 3
    assert (segments[0].page_start, segments[0].page_end) == (1, 10)
    assert (segments[1].page_start, segments[1].page_end) == (11, 20)
    assert (segments[2].page_start, segments[2].page_end) == (21, 25)
    assert segments[0].segment_index == 0
    assert segments[2].segment_index == 2


def test_build_segments_omits_blank_page_text_from_join():
    pages = ["hello", "", "world"]
    segments = build_segments_from_page_texts("a.pdf", pages, pages_per_segment=10)
    assert len(segments) == 1
    assert segments[0].text == "hello\n\nworld"

