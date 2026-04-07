from pathlib import Path

import pandas as pd

from qgen.exporter import write_outputs_for_pdf
from qgen.models import QARecord


def test_write_outputs_with_required_columns(tmp_path: Path):
    records = [
        QARecord(
            question="Q1",
            expectedResponse="A1",
            sourcePdf="x.pdf",
            segmentIndex=0,
            pageStart=1,
            pageEnd=10,
        )
    ]
    csv_path, xlsx_path = write_outputs_for_pdf(tmp_path, "LSAR", records, False)
    assert csv_path.name == "LSAR_qgen.csv"
    assert xlsx_path.name == "LSAR_qgen.xlsx"

    df = pd.read_csv(csv_path)
    assert list(df.columns) == ["question", "expectedResponse"]
    assert df.iloc[0]["question"] == "Q1"
    assert df.iloc[0]["expectedResponse"] == "A1"

