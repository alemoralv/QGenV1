from qgen.question_generator import _extract_json_array


def test_extract_json_array_plain():
    payload = '[{"question":"q1","expectedResponse":"a1"}]'
    rows = _extract_json_array(payload)
    assert rows[0]["question"] == "q1"
    assert rows[0]["expectedResponse"] == "a1"


def test_extract_json_array_from_code_fence_and_trailing_comma():
    payload = """```json
[
  {"question":"q1","expectedResponse":"a1",},
]
```"""
    rows = _extract_json_array(payload)
    assert len(rows) == 1
    assert rows[0]["question"] == "q1"

