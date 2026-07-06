import httpx
import re
from app.config import settings


class GitHubTool:
    """Fetches PR diff data from GitHub API."""

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token}"

    def parse_pr_url(self, pr_url: str) -> tuple[str, str, int]:
        """
        Parse GitHub PR URL into owner, repo, pr_number.
        Example: https://github.com/owner/repo/pull/42
        Returns: ("owner", "repo", 42)
        """
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
        owner = match.group(1)
        repo = match.group(2)
        pr_number = int(match.group(3))
        return owner, repo, pr_number

    def fetch_pr_files(self, pr_url: str) -> list[dict]:
        """
        Fetch all changed files and their diffs from a GitHub PR.
        Returns list of dicts with filename, status, patch.
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"

        with httpx.Client(headers=self.headers, timeout=30.0) as client:
            response = client.get(url)

        if response.status_code == 404:
            raise ValueError(f"PR not found: {pr_url}")
        if response.status_code == 403:
            raise ValueError("GitHub API rate limit hit. Add GITHUB_TOKEN to .env")
        if response.status_code != 200:
            raise ValueError(f"GitHub API error: {response.status_code}")

        files = response.json()

        result = []
        for f in files:
            result.append({
                "filename": f.get("filename", ""),
                "status": f.get("status", ""),
                "additions": f.get("additions", 0),
                "deletions": f.get("deletions", 0),
                "patch": f.get("patch", "")
            })

        return result

    def format_diff_for_review(self, files: list[dict]) -> str:
        """
        Format the list of file diffs into a clean string
        for the LLM to analyze.
        """
        if not files:
            return "No files changed in this PR."

        output = []
        for f in files:
            output.append(f"### File: {f['filename']} ({f['status']})")
            output.append(f"Additions: {f['additions']} | Deletions: {f['deletions']}")
            if f["patch"]:
                output.append("```diff")
                output.append(f["patch"][:3000])
                output.append("```")
            else:
                output.append("(binary file or no patch available)")
            output.append("")

        return "\n".join(output)


class HuggingFaceTool:
    """Calls HuggingFace Inference API for LLM analysis."""

    def __init__(self):
        from huggingface_hub import InferenceClient
        self.client = InferenceClient(
            model=settings.model_id,
            token=settings.hf_token
        )

    def analyze(self, system_prompt: str, user_content: str) -> str:
        """
        Send a prompt to the LLM and return the response text.
        """
        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"HuggingFace API error: {e}")
            return "[]"


# Single instances used across the app
github_tool = GitHubTool()
hf_tool = HuggingFaceTool()