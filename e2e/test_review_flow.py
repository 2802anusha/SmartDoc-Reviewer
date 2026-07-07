from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.agent.tools.github_tool.fetch_pr_files")
@patch("app.agent.tools.hf_tool.analyze")
def test_complete_review(mock_llm, mock_github):

    mock_github.return_value = [
        {
            "filename": "main.py",
            "patch": "print('hello')"
        }
    ]

    mock_llm.return_value = "[]"

    response = client.post(
        "/review",
        json={
            "pr_url": "https://github.com/demo/repo/pull/1"
        }
    )

    assert response.status_code == 200