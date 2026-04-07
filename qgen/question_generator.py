from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from qgen.config import AppConfig
from qgen.models import QARecord, Segment


def _openai_rejects_temperature_param(exc: BaseException) -> bool:
    """True when the API indicates `temperature` is not valid for this model."""
    status = getattr(exc, "status_code", None)
    if status != 400:
        return False
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error") or {}
        if err.get("param") == "temperature":
            return True
        msg = str(err.get("message", "")).lower()
        if "temperature" in msg and (
            "unsupported" in msg or "not supported" in msg
        ):
            return True
    text = str(exc).lower()
    return "temperature" in text and (
        "unsupported" in text or "not supported" in text
    )


def _build_prompt(
    segment: Segment,
    question_count: int,
    question_instructions: str,
    difficulty: str,
) -> str:
    return f"""
You are generating study questions and expected correct answers from a PDF segment.

Rules:
1) Keep the output language the same as the source text language.
2) Generate exactly {question_count} question-answer pairs.
3) Follow these user instructions: {question_instructions}
4) Difficulty level: {difficulty}
5) Ensure answers are concise but complete and factually grounded in the provided text.
6) Output ONLY valid JSON (no markdown), as an array of objects with exactly:
   - question
   - expectedResponse

Source metadata:
- PDF: {segment.source_pdf}
- Segment index: {segment.segment_index}
- Page range: {segment.page_start}-{segment.page_end}

Source text:
\"\"\"
{segment.text}
\"\"\"
""".strip()


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    candidates = [stripped]

    fence_match = re.search(r"```(?:json)?\s*(\[.*\])\s*```", stripped, re.DOTALL)
    if fence_match:
        candidates.insert(0, fence_match.group(1))

    array_match = re.search(r"(\[.*\])", stripped, re.DOTALL)
    if array_match:
        candidates.append(array_match.group(1))

    parse_error: Exception | None = None
    for candidate in candidates:
        repaired = re.sub(r",\s*([\]}])", r"\1", candidate)
        try:
            payload = json.loads(repaired)
            if isinstance(payload, list):
                normalized: list[dict[str, Any]] = []
                for item in payload:
                    if isinstance(item, dict):
                        normalized.append(item)
                return normalized
        except Exception as exc:  # noqa: BLE001
            parse_error = exc
    raise ValueError(f"Could not parse JSON array from model output: {parse_error}")


class CompletionClient(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        pass


class _OpenAIBackend(CompletionClient):
    def __init__(self, client: OpenAI, config: AppConfig) -> None:
        self._client = client
        self._config = config
        self._omit_temperature: bool = False

    def _responses_create(self, prompt: str, *, include_temperature: bool) -> Any:
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "input": prompt,
            "max_output_tokens": self._config.max_output_tokens,
        }
        if include_temperature:
            kwargs["temperature"] = self._config.temperature
        return self._client.responses.create(**kwargs)

    def complete(self, prompt: str) -> str:
        include_temp = not self._omit_temperature
        try:
            response = self._responses_create(prompt, include_temperature=include_temp)
            return (response.output_text or "").strip()
        except Exception as exc:
            if include_temp and _openai_rejects_temperature_param(exc):
                self._omit_temperature = True
                response = self._responses_create(
                    prompt, include_temperature=False
                )
                return (response.output_text or "").strip()
            raise


class _GoogleBackend(CompletionClient):
    def __init__(self, client: Any, config: AppConfig) -> None:
        self._client = client
        self._config = config

    def complete(self, prompt: str) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self._config.google_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self._config.temperature,
                max_output_tokens=self._config.max_output_tokens,
            ),
        )
        text = getattr(response, "text", None)
        if text:
            return str(text).strip()
        return ""


def build_llm_client(config: AppConfig) -> CompletionClient:
    openai_key = config.get_openai_key()
    if openai_key:
        return _OpenAIBackend(OpenAI(api_key=openai_key), config)

    google_key = config.get_google_key()
    if google_key:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Google provider selected but google-genai is not installed. "
                "Run: pip install google-genai"
            ) from exc
        return _GoogleBackend(genai.Client(api_key=google_key), config)

    raise ValueError(
        f"No API key found. Set {config.openai_api_key_env} for OpenAI, or set "
        f"{config.google_api_key_env} for Google Gemini when OpenAI is not used. "
        "You can define these in a .env file in the project root."
    )


def build_openai_client(config: AppConfig) -> OpenAI:
    """Build an OpenAI client (unchanged contract: requires OpenAI key in env)."""
    return OpenAI(api_key=config.get_api_key())


def generate_qa_for_segment(
    client: CompletionClient,
    config: AppConfig,
    segment: Segment,
    question_count: int,
) -> list[QARecord]:
    if question_count <= 0:
        return []
    if not segment.text.strip():
        return []

    prompt = _build_prompt(
        segment=segment,
        question_count=question_count,
        question_instructions=config.question_instructions,
        difficulty=config.difficulty,
    )

    last_error: Exception | None = None
    for attempt in range(1, config.retry_attempts + 1):
        try:
            text = client.complete(prompt)
            rows = _extract_json_array(text)
            records: list[QARecord] = []
            for row in rows[:question_count]:
                question = str(row.get("question", "")).strip()
                expected = str(row.get("expectedResponse", "")).strip()
                if question and expected:
                    records.append(
                        QARecord(
                            question=question,
                            expectedResponse=expected,
                            sourcePdf=segment.source_pdf,
                            segmentIndex=segment.segment_index,
                            pageStart=segment.page_start,
                            pageEnd=segment.page_end,
                        )
                    )
            return records
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < config.retry_attempts:
                time.sleep(config.retry_backoff_seconds * attempt)
    raise RuntimeError(
        f"Failed to generate Q&A for {segment.source_pdf} segment "
        f"{segment.segment_index} after retries: {last_error}"
    )
