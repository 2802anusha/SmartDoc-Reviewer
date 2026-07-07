import json

from app.agent.orchestrator import (
    calculate_score,
    parse_json_response
)


def test_parse_valid_json():

    text = '[{"severity":"High"}]'

    result = parse_json_response(text)

    assert len(result) == 1
    assert result[0]["severity"] == "High"


def test_parse_invalid_json():

    result = parse_json_response("hello world")

    assert result == []


def test_calculate_score():

    security = [{"severity": "Critical"}]
    style = [{"severity": "Medium"}]
    logic = [{"severity": "Low"}]

    score = calculate_score(
        security,
        style,
        logic
    )

    assert score == 73