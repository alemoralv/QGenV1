import pytest

from qgen.config import AppConfig
from qgen.question_generator import build_llm_client


def test_build_llm_client_errors_when_no_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    cfg = AppConfig.from_dict({})
    with pytest.raises(ValueError, match="No API key"):
        build_llm_client(cfg)
