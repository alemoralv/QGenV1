from __future__ import annotations

from qgen.models import Segment


def allocate_questions_across_segments(
    segments: list[Segment], total_questions: int
) -> dict[int, int]:
    if total_questions <= 0:
        raise ValueError("total_questions must be > 0")

    active_indices = [i for i, s in enumerate(segments) if s.text.strip()]
    if not active_indices:
        return {}

    base = total_questions // len(active_indices)
    remainder = total_questions % len(active_indices)

    allocated = {idx: base for idx in active_indices}
    for idx in active_indices[:remainder]:
        allocated[idx] += 1
    return allocated

