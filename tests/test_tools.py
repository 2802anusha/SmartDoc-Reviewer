from unittest.mock import patch

from app.agent.tools import github_tool


@patch.object(github_tool, "fetch_pr_files")
def test_fetch_pr(mock_fetch):

    mock_fetch.return_value = [
        {
            "filename": "main.py",
            "patch": "print('hello')"
        }
    ]

    files = github_tool.fetch_pr_files(
        "dummy"
    )

    assert len(files) == 1