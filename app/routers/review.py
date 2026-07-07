import threading
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    ReviewJob,
    ReviewReport,
    ReviewRequest,
    ReviewJobResponse
)
from app.agent.orchestrator import run_review

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def run_agent_in_background(job_id: str, pr_url: str):
    """
    Run the agent in a background thread so the API
    responds immediately without blocking.
    """
    from app.database import engine
    from sqlmodel import Session
    with Session(engine) as session:
        run_review(job_id, pr_url, session)


# ── API Endpoints ──────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    session: Session = Depends(get_session)
):
    statement = select(ReviewJob).order_by(ReviewJob.created_at.desc())
    jobs = session.exec(statement).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs
        }
    )


@router.post("/review", response_model=ReviewJobResponse)
def create_review(
    body: ReviewRequest,
    session: Session = Depends(get_session)
):
    """
    Accept a PR URL, create a job, start the agent in background.
    Returns the job ID immediately.
    """
    # Validate URL contains github.com/*/pull/*
    if "github.com" not in body.pr_url or "/pull/" not in body.pr_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub PR URL. Format: https://github.com/owner/repo/pull/123"
        )

    # Create job in database
    job = ReviewJob(pr_url=body.pr_url)
    session.add(job)
    session.commit()
    session.refresh(job)

    # Start agent in background thread
    thread = threading.Thread(
        target=run_agent_in_background,
        args=(job.id, body.pr_url),
        daemon=True
    )
    thread.start()

    return ReviewJobResponse(
        id=job.id,
        pr_url=job.pr_url,
        status=job.status,
        created_at=job.created_at
    )


@router.get("/review/{job_id}/status")
def get_job_status(
    job_id: str,
    session: Session = Depends(get_session)
):
    """
    Poll this endpoint to get current job status.
    Frontend polls every 3 seconds.
    """
    job = session.get(ReviewJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "status": job.status,
        "error_message": job.error_message
    }


@router.get("/review/{job_id}", response_class=HTMLResponse)
def get_review_page(
    job_id: str,
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Serve the review result page for a specific job.
    """
    job = session.get(ReviewJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get report if complete
    report = None
    if job.status == "complete":
        statement = select(ReviewReport).where(ReviewReport.job_id == job_id)
        report = session.exec(statement).first()

    return templates.TemplateResponse(
        "review.html",
        {
            "request": request,
            "job": job,
            "report": report
        }
    )


@router.get("/reviews", response_class=HTMLResponse)
def list_reviews(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    List all past review jobs.
    """
    statement = select(ReviewJob).order_by(ReviewJob.created_at.desc())
    jobs = session.exec(statement).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs
        }
    )


@router.get("/health")
def health_check():
    """Health check endpoint for Docker and CI."""
    return {"status": "ok", "service": "smartdoc-reviewer"}