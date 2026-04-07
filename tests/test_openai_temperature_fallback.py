from qgen.question_generator import _openai_rejects_temperature_param


class _Fake400Temperature:
    status_code = 400
    body = {
        "error": {
            "message": "Unsupported parameter: 'temperature' is not supported with this model.",
            "param": "temperature",
            "type": "invalid_request_error",
        }
    }


class _Fake400Other:
    status_code = 400
    body = {"error": {"message": "Something else", "param": "model"}}


def test_openai_rejects_temperature_param_detects_known_error() -> None:
    assert _openai_rejects_temperature_param(_Fake400Temperature())


def test_openai_rejects_temperature_param_false_for_other_400() -> None:
    assert not _openai_rejects_temperature_param(_Fake400Other())
