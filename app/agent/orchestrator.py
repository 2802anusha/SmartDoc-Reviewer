import json
import re
from datetime import datetime
from sqlmodel import Session
from app.models import ReviewJob, ReviewReport
from app.agent.tools import github_tool, hf_tool
from app.agent.prompts import (
    SECURITY_PROMPT,
    STYLE_PROMPT,
    LOGIC_PROMPT,
    SYNTHESIS_PROMPT
)


def parse_json_response(response: str) -> list:
    """
    Safely parse LLM JSON response into a list.
    Handles cases where LLM adds extra text around the JSON.
    """
    try:
        # Direct parse first
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    try:
        # Try to extract JSON array from response
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    # Return empty list if nothing works
    print(f"Could not parse JSON from response: {response[:200]}")
    return []


def calculate_score(
    security: list,
    style: list,
    logic: list
) -> int:
    """
    Calculate overall PR score out of 100.
    Deduct points based on severity of findings.
    """
    score = 100
    deductions = {
        "Critical": 20,
        "High": 10,
        "Medium": 5,
        "Low": 2
    }

    all_findings = security + style + logic
    for finding in all_findings:
        severity = finding.get("severity", "Low")
        score -= deductions.get(severity, 2)

    return max(0, score)  # never go below 0


def update_job_status(session: Session, job: ReviewJob, status: str):
    """Update job status in the database."""
    job.status = status
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)


def run_review(job_id: str, pr_url: str, session: Session):
    """
    Main agent orchestrator — runs the full 4-step review loop.

    Step 1: Fetch PR diff from GitHub
    Step 2: Analyze for security issues
    Step 3: Analyze for style issues
    Step 4: Analyze for logic issues
    Step 5: Synthesize final summary
    """

    # Get job from database
    job = session.get(ReviewJob, job_id)
    if not job:
        print(f"Job {job_id} not found")
        return

    try:
        # ── Step 1: Fetch PR diff ──────────────────────────────
        print(f"[Agent] Step 1: Fetching PR diff for {pr_url}")
        update_job_status(session, job, "fetching")

        files = github_tool.fetch_pr_files(pr_url)
        diff_text = github_tool.format_diff_for_review(files)

        if not files:
            update_job_status(session, job, "failed")
            job.error_message = "No files found in this PR"
            session.add(job)
            session.commit()
            return

        print(f"[Agent] Fetched {len(files)} files successfully")

        # ── Step 2: Security analysis ──────────────────────────
        print("[Agent] Step 2: Analyzing security issues...")
        update_job_status(session, job, "analyzing_security")

        security_response = hf_tool.analyze(
            system_prompt=SECURITY_PROMPT,
            user_content=f"Review this code diff for security issues:\n\n{diff_text}"
        )
        security_findings = parse_json_response(security_response)
        print(f"[Agent] Found {len(security_findings)} security issues")

        # ── Step 3: Style analysis ─────────────────────────────
        print("[Agent] Step 3: Analyzing style issues...")
        update_job_status(session, job, "analyzing_style")

        style_response = hf_tool.analyze(
            system_prompt=STYLE_PROMPT,
            user_content=f"Review this code diff for style issues:\n\n{diff_text}"
        )
        style_findings = parse_json_response(style_response)
        print(f"[Agent] Found {len(style_findings)} style issues")

        # ── Step 4: Logic analysis ─────────────────────────────
        print("[Agent] Step 4: Analyzing logic issues...")
        update_job_status(session, job, "analyzing_logic")

        logic_response = hf_tool.analyze(
            system_prompt=LOGIC_PROMPT,
            user_content=f"Review this code diff for logic issues:\n\n{diff_text}"
        )
        logic_findings = parse_json_response(logic_response)
        print(f"[Agent] Found {len(logic_findings)} logic issues")

        # ── Step 5: Synthesize final summary ───────────────────
        print("[Agent] Step 5: Synthesizing final summary...")
        update_job_status(session, job, "synthesizing")

        synthesis_input = f"""
Security findings: {json.dumps(security_findings)}
Style findings: {json.dumps(style_findings)}
Logic findings: {json.dumps(logic_findings)}
"""
        summary = hf_tool.analyze(
            system_prompt=SYNTHESIS_PROMPT,
            user_content=synthesis_input
        )

        # ── Calculate score ────────────────────────────────────
        overall_score = calculate_score(
            security_findings,
            style_findings,
            logic_findings
        )

        # ── Save report to database ────────────────────────────
        report = ReviewReport(
            job_id=job_id,
            pr_url=pr_url,
            security_findings=json.dumps(security_findings),
            style_findings=json.dumps(style_findings),
            logic_findings=json.dumps(logic_findings),
            summary=summary,
            overall_score=overall_score
        )
        session.add(report)

        # Mark job as complete
        update_job_status(session, job, "complete")
        session.commit()

        print(f"[Agent] Review complete. Score: {overall_score}/100")

    except Exception as e:
        print(f"[Agent] Error: {e}")
        job.error_message = str(e)
        update_job_status(session, job, "failed")
        session.commit()