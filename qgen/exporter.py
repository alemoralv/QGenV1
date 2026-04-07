from __future__ import annotations

from pathlib import Path

import pandas as pd

from qgen.models import QARecord


def write_outputs_for_pdf(
    output_dir: str | Path,
    pdf_stem: str,
    records: list[QARecord],
    include_metadata_columns: bool,
) -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for record in records:
        row: dict[str, object] = {
            "question": record.question,
            "expectedResponse": record.expectedResponse,
        }
        if include_metadata_columns:
            row.update(
                {
                    "sourcePdf": record.sourcePdf,
                    "segmentIndex": record.segmentIndex,
                    "pageStart": record.pageStart,
                    "pageEnd": record.pageEnd,
                }
            )
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        base_cols = ["question", "expectedResponse"]
        if include_metadata_columns:
            base_cols += ["sourcePdf", "segmentIndex", "pageStart", "pageEnd"]
        df = pd.DataFrame(columns=base_cols)

    csv_path = output_path / f"{pdf_stem}_qgen.csv"
    xlsx_path = output_path / f"{pdf_stem}_qgen.xlsx"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_excel(xlsx_path, index=False)
    return csv_path, xlsx_path

