from unittest.mock import patch

from app.agent.tools import hf_tool


@patch.object(hf_tool, "analyze")
def test_llm(mock_llm):

    mock_llm.return_value = '[{"severity":"Low"}]'

    result = hf_tool.analyze(
        "prompt",
        "code"
    )

    assert "severity" in result